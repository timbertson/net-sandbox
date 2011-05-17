#!/usr/bin/env python
import os
import sys
import subprocess
import unshare
import selective_chroot

class Usage(RuntimeError):
	pass

MOUNT_DIRS = []

def main():
	global MOUNT_DIRS
	from optparse import OptionParser
	p = OptionParser()
	p.add_option('-b', '--base', default='/tmp/chroot.rootfs')
	p.add_option('--init', help='init script', default=None)
	p.add_option('-u', '--user', help='user to run script as (guessed from $SUDO_USER)', default=None)
	p.add_option('-s', '--shadow', action='append', default=[], dest='shadow_dirs', help='directories to shadow')
	opts, args = p.parse_args()
	if not os.geteuid() == 0:
		raise Usage("must be root!")
	user = opts.user or os.environ['SUDO_USER']
	base = opts.base
	shadow_dirs = opts.shadow_dirs or ['/tmp', '/var']

	def namespaced_action():
		unshare.unshare(unshare.CLONE_NEWNS | unshare.CLONE_NEWNET)

		def chroot_action():
			for dir in shadow_dirs:
				subprocess.check_call(['chown', user, dir])
			subprocess.check_call(['ifconfig', 'lo', 'up'])
			if opts.init:
				subprocess.check_call([opts.init])
			def user_action():
				subprocess.check_call(args or ['bash', '-i'])
			selective_chroot.execute_as_user(user_action, user=user)
		ret, MOUNT_DIRS = selective_chroot.chroot(base=base, shadow_dirs=shadow_dirs, action=chroot_action)
		return ret
	
	ret = selective_chroot.in_subprocess(namespaced_action)
	for dir in MOUNT_DIRS:
		os.removedirs(dir)
	#TODO? shutil.rmtree(base)
	return ret

if __name__ == '__main__':
	try:
		ret = main()
	except Usage, e:
		print >> sys.stderr, e
		ret = 1
	except KeyboardInterrupt:
		ret = 1
	sys.exit(ret)
