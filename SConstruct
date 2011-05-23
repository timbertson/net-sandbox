#!/usr/bin/env python
from SCons import SConsign
import os

env = Environment(ENV = os.environ)
Export('env')

builddir = os.environ.get('BUILDDIR', '.build')
print "Bulding in", builddir

# Store signature information in build directory
SConsign.File(builddir + os.sep)

SConscript('src/sconscript',
	variant_dir = builddir)

