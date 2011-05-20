#!/usr/bin/python
import os
top = os.environ.get('SRCDIR', '.')
out = os.environ.get('BUILDDIR', '.build')
os.environ['PREFIX'] = os.environ.get('DISTDIR', '.dist')
distdir = 'dist'
APPNAME='net-sandbox'

with open('VERSION', 'r') as VERSION_FILE:
	VERSION = VERSION_FILE.read().strip()

def configure(conf):
	conf.check_tool('gcc')

def clobber(ctx):
	ctx.exec_command(['rm','-rf', '.dist'])
def all(ctx):
	ctx.exec_command('waf configure build install')

def build(bld):
	bld.install_files('${PREFIX}/lib/python', ['net_sandbox.py'])
	bld.program(
			source = 'unshare-pid.c',
			target = 'unshare-pid',
			features = 'c cprogram',
			install_path='${PREFIX}/bin',
			chmod = 0755)
