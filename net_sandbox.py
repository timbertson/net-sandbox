#!/usr/bin/env python
import os
import sys
import subprocess
import unshare
import selective_chroot

class Usage(RuntimeError):
	pass

MOUNT_DIRS = []
DEFAULT_SHADOW_DIRS = ['/tmp', '/var']
CLONE_NEWPID = 'CLONE_NEWPID'
DEFAULT_UNSHARE_FLAGS = ['CLONE_NEWNS', 'CLONE_NEWNET', CLONE_NEWPID]
DEFAULT_CMD = ['bash', '-i']

def main():
	from optparse import OptionParser
	p = OptionParser()
	p.add_option('-b', '--base', default='/tmp/chroot.rootfs')
	p.add_option('-u', '--user', help='user to run script as (default: guessed from $SUDO_USER)', default=None)
	p.add_option('-s', '--shadow', action='append', default=[], dest='shadow_dirs', help='directories to shadow (can be specified multiple times)')
	p.add_option('-i', '--init', default=None, help='init command (run as root)')
	unshare_flag_names = filter(lambda c: c.startswith("CLONE_"), dir(unshare))
	unshare_flag_desc = "(any of: %s)" % (", ".join(unshare_flag_names),)
	p.add_option('-n', '--unshare', action='append', default=[], dest='unshare_flags', help='flags to unshare (may be specified multiple times) ' + unshare_flag_desc)

	opts, args = p.parse_args()
	if not os.geteuid() == 0:
		raise Usage("you must be root!")
	return sandbox(unshare_flag_names = opts.unshare_flags or DEFAULT_UNSHARE_FLAGS,
			shadow_dirs = opts.shadow_dirs or DEFAULT_SHADOW_DIRS,
			chroot_base = opts.base,
			init_expr = opts.init,
			user = opts.user,
			cmd = args or DEFAULT_CMD)

def sandbox(unshare_flag_names = DEFAULT_UNSHARE_FLAGS,
	shadow_dirs = DEFAULT_SHADOW_DIRS,
	chroot_base='/tmp/chroot.rootfs',
	init_expr=None,
	user=None,
	cmd = DEFAULT_CMD):

	user = user or os.environ['SUDO_USER']

	unshare_flag_names = unshare_flag_names[:]
	unshare_flags = 0
	needs_pid_unshare = CLONE_NEWPID in unshare_flag_names
	if needs_pid_unshare:
		# this flag does not work with unshare, as it relies on a fork(). So just re-execute this
		# script with the same arguments after a call to the unshare-pid tool.
		unshare_flag_names.remove(CLONE_NEWPID)
		if CLONE_NEWPID not in os.environ:
			os.environ[CLONE_NEWPID] = 'true'
			os.execv('unshare-pid', [sys.argv[0]] + sys.argv)
		else:
			del os.environ[CLONE_NEWPID]

	for flag_name in unshare_flag_names:
		unshare_flags |= getattr(unshare, flag_name)

	def namespaced_action():
		global MOUNT_DIRS
		unshare.unshare(unshare_flags)
		os.environ['SANDBOX'] = 'true'

		def chroot_action():
			for d in shadow_dirs:
				subprocess.check_call(['chown', user, d])
			subprocess.check_call(['ifconfig', 'lo', 'up'])
			if init_expr:
				subprocess.check_call(['bash','-c', init_expr])
			def user_action():
				subprocess.check_call(cmd)
			selective_chroot.execute_as_user(user_action, user=user)
		ret, MOUNT_DIRS = selective_chroot.chroot(base=chroot_base, shadow_dirs=shadow_dirs, action=chroot_action)
		return ret
	
	ret = selective_chroot.in_subprocess(namespaced_action)
	for d in MOUNT_DIRS:
		os.removedirs(d)
	#TODO? shutil.rmtree(base)
	return ret

if __name__ == '__main__':
	try:
		ret = main()
	except Usage, e:
		print >> sys.stderr, e
		ret = 2
	except subprocess.CalledProcessError:
		ret = 1
	except KeyboardInterrupt:
		ret = 3
	sys.exit(ret)
