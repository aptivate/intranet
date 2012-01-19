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
        from settings import HAYSTACK_WHOOSH_PATH
        if HAYSTACK_WHOOSH_PATH is not None and HAYSTACK_WHOOSH_PATH != '':
            if not os.path.exists(HAYSTACK_WHOOSH_PATH):
                os.mkdir(HAYSTACK_WHOOSH_PATH)
            os.chmod(HAYSTACK_WHOOSH_PATH, stat.S_IRWXU | stat.S_IRWXG | 
                stat.S_IRWXO)
    except ImportError, e:
        # no HAYSTACK_WHOOSH_PATH? not a fatal error
        print "No HAYSTACK_WHOOSH_PATH found: %s" % e
