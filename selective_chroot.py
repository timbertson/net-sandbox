#!/usr/bin/env python

import os,sys
import subprocess
from optparse import OptionParser
SYSTEM_MOUNTPOINTS = set(['/proc', '/sys'])

def main():
	p = OptionParser(usage="%prog [OPTIONS] cmd")
	p.add_option('-b', '--base')
	p.add_option('-s', '--shadow', action='append', default=[], dest='shadow_dirs')
	p.add_option('-n', '--dry-run', action='store_true', help='print commands, but do nothing')
	opts,args = p.parse_args()
	assert opts.base, "Please provide a base directory"
	def action():
		if not opts.dry_run:
			execute_as_user(lambda: subprocess.check_call(args))
	chroot(base=opts.base, shadow_dirs = opts.shadow_dirs, dry_run=opts.dry_run, action=action)

def chroot(base, shadow_dirs, action, dry_run=False):
	mounted_dirs = create_fs_mirror(base, shadow_dirs, dry_run)
	def _action():
		os.chroot(base)
		for system_dir in SYSTEM_MOUNTPOINTS:
			_run_cmd(['mount', system_dir], dry_run=dry_run)
		return action()
	ret = in_subprocess(_action)
	return ret, mounted_dirs

def in_subprocess(func):
	"""a helper to run a function in a subprocess"""
	child_pid = os.fork()
	if child_pid == 0:
		func()
		os._exit(0)
	else:
		(pid, status) = os.waitpid(child_pid, 0)
		return status

def execute_as_user(func, user=None):
	def action():
		become_user(user)
		func()
	return in_subprocess(action)

import pwd
def become_user(name=None):
	if name is None:
		name = os.environ['SUDO_USER']
		assert name != 'root'

	# Get the uid/gid from the name
	running_uid = pwd.getpwnam(name).pw_uid
	running_gid = pwd.getpwnam(name).pw_gid

	# Remove group privileges
	os.setgroups([])

	# Try setting the new uid/gid
	os.setgid(running_gid)
	os.setuid(running_uid)

def _run_cmd(cmd, dry_run, silent=False):
	if dry_run:
		if not silent:
			print ' '.join(cmd)
	else:
		subprocess.check_call(cmd)

def create_fs_mirror(base, shadow_dirs, dry_run=False):
	sep = os.path.sep
	base = base.rstrip(sep)
	shadow_dirs = [dir.rstrip(sep) for dir in shadow_dirs]
	def add_slash(path): return path.rstrip('/') + '/'

	assert any([base.startswith(shadow + os.path.sep) for shadow in shadow_dirs])
	def is_shadowed(path):
		return path in shadow_dirs
	def shares_prefix_with_shadowed(path):
		return any(add_slash(shadow_dir).startswith(add_slash(path)) for shadow_dir in shadow_dirs)

	def run_cmd(cmd, silent=False):
		_run_cmd(cmd, dry_run=dry_run, silent=silent)

	def chroot_path(path):
		return os.path.join(base, path.lstrip('/'))

	mounted_dirs = []
	def bind_mount(path):
		run_cmd(['mkdir','-p', chroot_path(path)], silent=True)
		if path not in SYSTEM_MOUNTPOINTS:
			# procfs / sysfs will be auto mounted without arguments
			run_cmd(['mount', '--bind', path, chroot_path(path)])
		mounted_dirs.append(chroot_path(path))
	
	def mkdir_p(path):
		run_cmd(['mkdir', '-p', chroot_path(path)])

	for path, dirnames, filenames in os.walk('/', followlinks=True):
		fullpath = lambda x: os.path.join(path, x)
		for dirname in dirnames[:]:
			full = fullpath(dirname)
			keep = False
			if is_shadowed(full):
				mkdir_p(full)
			elif not shares_prefix_with_shadowed(full):
				bind_mount(full)
			else:
				# shares a prefix with a shadowed dir; we can't remove it yet...
				keep = True
			if not keep:
				dirnames.remove(dirname)
	
	return mounted_dirs


if __name__ == '__main__':
	main()



