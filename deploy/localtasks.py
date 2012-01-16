import sys, os, stat
from tasklib import env

def post_deploy(environment=None):
    sys.path.append(env['django_dir'])
    sys.path.append(os.path.join(env['ve_dir'], 'lib', 'python2.6', 'site-packages'))

    import settings as django_settings
    
    try:
        from settings import MEDIA_ROOT
        if MEDIA_ROOT is not None and MEDIA_ROOT != '':
            os.mkdir(MEDIA_ROOT)
            os.chmod(MEDIA_ROOT, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except ImportError, e:
        # no MEDIA_ROOT? not a fatal error
        print "No MEDIA_ROOT found: %s" % e
