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
	p.add_option('-u', '--user', help='user to run script as (default: guessed from $SUDO_USER)', default=None)
	p.add_option('-s', '--shadow', action='append', default=[], dest='shadow_dirs', help='directories to shadow (can be specified multiple times)')
	unshare_flag_names = filter(lambda c: c.startswith("CLONE_"), dir(unshare))
	unshare_flag_desc = "(any of: %s)" % (", ".join(unshare_flag_names),)
	p.add_option('-n', '--unshare', action='append', default=[], dest='unshare_flags', help='flags to unshare (may be specified multiple times) ' + unshare_flag_desc)

	opts, args = p.parse_args()
	if not os.geteuid() == 0:
		raise Usage("must be root!")
	user = opts.user or os.environ['SUDO_USER']
	base = opts.base
	shadow_dirs = opts.shadow_dirs or ['/tmp', '/var']
	unshare_flags = 0
	for flag_name in opts.unshare_flags or ['CLONE_NEWNS', 'CLONE_NEWNET', 'CLONE_NEWPID']:
		unshare_flags |= getattr(unshare, flag_name)

	def namespaced_action():
		unshare.unshare(unshare.CLONE_NEWNS | unshare.CLONE_NEWNET)

		def chroot_action():
			for d in shadow_dirs:
				subprocess.check_call(['chown', user, d])
			subprocess.check_call(['ifconfig', 'lo', 'up'])
			if opts.init:
				subprocess.check_call([opts.init])
			def user_action():
				subprocess.check_call(args or ['bash', '-i'])
			selective_chroot.execute_as_user(user_action, user=user)
		ret, MOUNT_DIRS = selective_chroot.chroot(base=base, shadow_dirs=shadow_dirs, action=chroot_action)
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
		ret = 1
	except KeyboardInterrupt:
		ret = 1
	sys.exit(ret)
