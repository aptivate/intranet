import sys, os, stat
from tasklib import env

def post_deploy(environment=None):
    sys.path.append(env['django_dir'])
    sys.path.append(os.path.join(env['ve_dir'], 'lib', 'python2.6', 'site-packages'))
    import settings as django_settings
    
    if 'MEDIA_ROOT' in django_settings:
        if django_settings.MEDIA_ROOT is not None and \
            django_settings.MEDIA_ROOT != '':
            mkdir(django_settings.MEDIA_ROOT)
            os.chmod(django_settings.MEDIA_ROOT, stat.S_IRWXU |
                stat.S_IRWXG | stat.S_IRWXO)
