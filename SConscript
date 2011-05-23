#!/usr/bin/env python
import os

Import('env')

def dist(filename=''):
	return os.path.join(os.environ.get('DISTDIR', 'dist'), filename)

unshare = env.Program(source=['unshare-pid.c'])

env.Install(dist('lib/python'), Glob('*.py'))
env.Install(dist('bin'), [unshare])
