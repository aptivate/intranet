import os, stat, project_settings

def post_deploy(environment=None):
    sys.path.append(project_settings.django_dir)
    import settings as django_settings
    if 'MEDIA_ROOT' in django_settings:
        if django_settings.MEDIA_ROOT is not None and \
            django_settings.MEDIA_ROOT != '':
            mkdir(django_settings.MEDIA_ROOT)
            os.chmod(django_settings.MEDIA_ROOT, stat.S_IRWXU |
                stat.S_IRWXG | stat.S_IRWXO)
