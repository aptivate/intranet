import sys

from jcc import cpp

options = {
    'include': ('org.eclipse.osgi.jar', 'tika-app-1.0.jar',),
    'jar': ('tika-parsers-1.0.jar', 'tika-core-1.0.jar',),
    'package': ('org.xml.sax',),
    'python': 'tika',
    'version': '1.0',
    'reserved': ('asm',),
    'classes': ('java.io.File', 'java.io.FileInputStream',
        'java.io.StringBufferInputStream',),
}

import sys
import os.path

args = []

for dir in sys.path:
    probe_dir = os.path.join(dir, 'jcc')
    if os.path.exists(probe_dir):
        print "Found jcc library at: %s" % probe_dir
        args = [os.path.join(probe_dir, 'nonexistent-argv-0')]
        break

if not args:
    raise Exception("tika library not found in sys.path: %s" % sys.path)

for k, v in options.iteritems():
    if k == 'classes':
        args.extend(v)
    elif hasattr(v, '__iter__'):
        for value in v:
            args.append('--%s' % k)
            args.append(value)
    else:
        args.append('--%s' % k)
        args.append(v)

forwarded_args = []

skip_next_arg = False
forward_next_arg = False
egg_info_mode = False

for arg in sys.argv[1:]:
    if skip_next_arg:
        skip_next_arg = False
    elif forward_next_arg:
        forward_next_arg = False
        forwarded_args.append(arg)
    elif arg == 'install':
        args.append('--install')
    elif arg == 'build':
        args.append('--build')
    elif arg == '-c':
        # forwarded_args.append(arg)
        pass
    elif arg == 'egg_info':
        args.append('--egg-info')
    else:
        forwarded_args.append(arg)
    """
    elif arg == '--single-version-externally-managed':
        forwarded_args.append(arg)
    elif arg == '--egg-base' or arg == '--record':
        forwarded_args.append(arg)
        forward_next_arg = True
    else:
        raise NotImplementedError("Unknown argument: %s" % arg)
    """
    
for extra_arg in forwarded_args:
    args.append('--extra-setup-arg')
    args.append(extra_arg)

# monkey patch to send extra args to distutils
# import setuptools
# old_setup = setuptools.setup
"""
from distutils.core import setup as old_setup
def new_setup(**attrs):
	attrs['script_args'].extend(forwarded_args)
	print "running setup %s" % attrs['script_args']
	old_setup(**attrs)

def new_compile(**kwargs):
    print "changing jccPath from %s to %s" % (kwargs['jccPath'],
        jcc.__path__)
    kwargs['jccPath'] = jcc.__path__
    kwargs['setup_func'] = new_setup
    from jcc.python import compile
    compile(**kwargs, new_setup)
"""

print "args = %s" % args

cpp.jcc(args)
