import sys, os, stat
from tasklib import env

def post_deploy(environment=None):
    sys.path.append(env['django_dir'])
    sys.path.append(os.path.join(env['ve_dir'], 'lib', 'python2.6', 'site-packages'))

    import settings as django_settings
    
    try:
        from settings import MEDIA_ROOT
        if MEDIA_ROOT is not None and MEDIA_ROOT != '':
            if not os.path.exists(MEDIA_ROOT):
                os.mkdir(MEDIA_ROOT)
            os.chmod(MEDIA_ROOT, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except ImportError, e:
        # no MEDIA_ROOT? not a fatal error
        print "No MEDIA_ROOT found: %s" % e

    try:
        from settings import HAYSTACK_CONNECTIONS
        whoosh_path = HAYSTACK_CONNECTIONS['default']['PATH']
        if not os.path.exists(whoosh_path):
            os.mkdir(whoosh_path)
        os.chmod(whoosh_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except ImportError, e:
        # no HAYSTACK_CONNECTIONS? not a fatal error
        print "No HAYSTACK_CONNECTIONS found: %s" % e
