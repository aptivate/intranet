#!/usr/bin/python2.6
#
# This script is to set up various things for our projects. It can be used by:
#
# * developers - setting up their own environment
# * jenkins - setting up the environment and running tests
# * fabric - it will call a copy on the remote server when deploying
#
# The tasks it will do (eventually) include:
#
# * creating, updating and deleting the virtualenv
# * creating, updating and deleting the database (sqlite or mysql)
# * setting up the local_settings stuff
# * running tests
"""This script is to set up various things for our projects. It can be used by:

* developers - setting up their own environment
* jenkins - setting up the environment and running tests
* fabric - it will call a copy on the remote server when deploying

"""

import os, sys
import getpass
import random

try:
    # For testing replacement routines for older python compatibility
    # raise ImportError()
    import subprocess
    from subprocess import call as _call_command

    def _capture_command(argv):
        return subprocess.Popen(argv, stdout=subprocess.PIPE).communicate()[0]

except ImportError:
    def _capture_command(argv):
        command = ' '.join(argv)
        # print "(_capture_command) Executing: %s" % command
        fd = os.popen(command)
        output = fd.read()
        fd.close()
        return output
        
    # older python
    def _call_command(argv, stdin=None, stdout=None):
        argv = [i.replace('"', '\"') for i in argv]
        argv = ['"%s"' % i for i in argv]
        command = " ".join(argv)
        
        if stdin is not None:
            command += " < " + stdin.name
        
        if stdout is not None:
            command += " > " + stdout.name
        
        # sys.stderr.write("(_call_command) Executing: %s\n" % command)
        
        return os.system(command)

# import per-project settings
import project_settings

env = {}

def _setup_paths():
    """Set up the paths used by other tasks"""
    env['deploy_dir'] = os.path.dirname(__file__)
    # what is the root of the project - one up from this directory
    env['project_dir'] = os.path.abspath(os.path.join(env['deploy_dir'], '..'))
    env['django_dir']  = os.path.join(env['project_dir'], project_settings.django_dir)
    env['ve_dir']      = os.path.join(env['django_dir'], '.ve')
    env['python_bin']  = os.path.join(env['ve_dir'], 'bin', 'python2.6')
    env['manage_py']   = os.path.join(env['django_dir'], 'manage.py')
    env['project_name'] = project_settings.project_name
    env['project_type'] = project_settings.project_type


def _call_wrapper(argv, **kwargs):
    if env['verbose']:
        print "Executing command: %s" % ' '.join(argv)
    _call_command(argv, **kwargs)

def _manage_py(args, cwd=None, supress_output=False):
    # for manage.py, always use the system python 2.6
    # otherwise the update_ve will fail badly, as it deletes
    # the virtualenv part way through the process ...
    manage_cmd = ['/usr/bin/python2.6', env['manage_py']]
    if isinstance(args, str):
        manage_cmd.append(args)
    else:
        manage_cmd.extend(args)

    # Allow manual specification of settings file
    if env.has_key('manage_py_settings'):
        manage_cmd.append('--settings=%s' % env['manage_py_settings'])

    if cwd == None:
        cwd = env['django_dir']

    if env['verbose']:
        print 'Executing manage command: %s' % ' '.join(manage_cmd)
    output_lines = []
    
    try:
        popen = subprocess.Popen(manage_cmd, cwd=cwd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except OSError, e:
        print "Failed to execute command: %s: %s" % (manage_cmd, e)
        raise e
    
    for line in iter(popen.stdout.readline, ""):
        if env['verbose'] or not supress_output:
            print line,
        output_lines.append(line)
    returncode = popen.wait()
    if returncode != 0:
        sys.exit(popen.returncode)
    return output_lines


def _create_dir_if_not_exists(dir_path, world_writeable=False):
    if not os.path.exists(dir_path):
        _call_wrapper(['mkdir', '-p', dir_path])
    if world_writeable:
        _call_wrapper(['chmod', '-R', '777', dir_path])


def _get_django_db_settings():
    # import local_settings from the django dir. Here we are adding the django
    # project directory to the path. Note that env['django_dir'] may be more than
    # one directory (eg. 'django/project') which is why we use django_module
    sys.path.append(env['django_dir'])
    import local_settings

    db_user = 'nouser'
    db_pw   = 'nopass'
    db_host = '127.0.0.1'
    db_port = None
    # there are two ways of having the settings:
    # either as DATABASE_NAME = 'x', DATABASE_USER ...
    # or as DATABASES = { 'default': { 'NAME': 'xyz' ... } }
    try:
        db = local_settings.DATABASES['default']
        db_engine = db['ENGINE']
        db_name   = db['NAME']
        if db_engine.endswith('mysql'):
            db_user   = db['USER']
            db_pw     = db['PASSWORD']
            if db.has_key('PORT'):
                db_port = db['PORT']
            if db.has_key('HOST'):
                db_host = db['HOST']

    except (AttributeError, KeyError):
        try:
            db_engine = local_settings.DATABASE_ENGINE
            db_name   = local_settings.DATABASE_NAME
            if db_engine.endswith('mysql'):
                db_user   = local_settings.DATABASE_USER
                db_pw     = local_settings.DATABASE_PASSWORD
                if hasattr(local_settings, 'DATABASE_PORT'):
                    db_port = local_settings.DATABASE_PORT
                if hasattr(local_settings, 'DATABASE_HOST'):
                    db_host = local_settings.DATABASE_HOST
        except AttributeError:
            # we've failed to find the details we need - give up
            print("Failed to find database settings")
            sys.exit(1)
    env['db_port'] = db_port
    env['db_host'] = db_host
    return (db_engine, db_name, db_user, db_pw, db_port, db_host)


def _mysql_exec_as_root(mysql_cmd):
    """ execute a SQL statement using MySQL as the root MySQL user"""
    mysql_call = ['mysql', '-u', 'root', '-p'+_get_mysql_root_password()]
    mysql_call += ['--host=%s' % env['db_host']]
    
    if env['db_port'] != None:
        mysql_call += ['--port=%s' % env['db_port']]
    mysql_call += ['-e']
    if env['verbose']:
        print 'Executing MySQL command: %s' % ' '.join(mysql_call + [mysql_cmd])
    return _call_command(mysql_call + [mysql_cmd])


def _get_mysql_root_password():
    # first try to read the root password from a file
    # otherwise ask the user
    if not env.has_key('root_pw'):
        file_exists = _call_command(['sudo', 'test', '-f', '/root/mysql_root_password'])
        if file_exists == 0:
            # note this requires sudoers to work with this - jenkins particularly ...
            root_pw = _capture_command(["sudo", "cat", "/root/mysql_root_password"])
            env['root_pw'] = root_pw.rstrip()
        else:
            env['root_pw'] = getpass.getpass('Enter MySQL root password:')
    return env['root_pw']


def clean_ve():
    """Delete the virtualenv so we can start again"""
    _call_wrapper(['rm', '-rf', env['ve_dir']])


def clean_db():
    """Delete the database for a clean start"""
    # first work out the database username and password
    db_engine, db_name, db_user, db_pw, db_port, db_host = _get_django_db_settings()
    # then see if the database exists
    if db_engine.endswith('sqlite'):
        # delete sqlite file
        if os.path.isabs(db_name):
            db_path = db_name
        else:
            db_path = os.path.abspath(os.path.join(env['django_dir'], db_name))
        os.remove(db_path)
    elif db_engine.endswith('mysql'):
        # DROP DATABASE
        _mysql_exec_as_root('DROP DATABASE IF EXISTS %s' % db_name)

        test_db_name = 'test_' + db_name
        _mysql_exec_as_root('DROP DATABASE IF EXISTS %s' % test_db_name)


def create_ve():
    """Create the virtualenv"""
    _manage_py("update_ve")


def update_ve():
    """ Update the virtualenv """
    create_ve()

def create_private_settings():

    private_settings_file = os.path.join(env['django_dir'],
                                    'private_settings.py')
    if not os.path.exists(private_settings_file):
        # don't use "with" for compatibility with python 2.3 on whov2hinari
        f = open(private_settings_file, 'w')
        try:
            secret_key = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])
            db_password = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for i in range(12)])
            
            f.write("SECRET_KEY = '%s'\n" % secret_key)
            f.write("DB_PASSWORD = '%s'\n" % db_password)
        finally:
            f.close()
    
def link_local_settings(environment):
    """ link local_settings.py.environment as local_settings.py """
    # die if the correct local settings does not exist
    local_settings_env_path = os.path.join(env['django_dir'],
                                    'local_settings.py.'+environment)
    if not os.path.exists(local_settings_env_path):
        print "Could not find file to link to: %s" % local_settings_env_path
        sys.exit(1)

    files_to_remove = ('local_settings.py', 'local_settings.pyc')
    for file in files_to_remove:
        full_path = os.path.join(env['django_dir'], file)
        if os.path.exists(full_path):
            os.remove(full_path)

    os.symlink('local_settings.py.'+environment, 
        os.path.join(env['django_dir'],'local_settings.py'))


def update_db(syncdb=True, drop_test_db=True):
    """ create the database, and do syncdb and migrations (if syncdb==True)"""
    # first work out the database username and password
    db_engine, db_name, db_user, db_pw, db_port, db_host = _get_django_db_settings()
    # then see if the database exists
    if db_engine.endswith('mysql'):
        if not db_exists(db_user, db_pw, db_name, db_port, db_host):
            _mysql_exec_as_root('CREATE DATABASE %s CHARACTER SET utf8' % db_name)
            _mysql_exec_as_root(('GRANT ALL PRIVILEGES ON %s.* TO \'%s\'@\'localhost\' IDENTIFIED BY \'%s\'' % 
                (db_name, db_user, db_pw)))

        if not db_exists(db_user, db_pw, 'test_'+db_name, db_port, db_host):
            create_test_db(drop_after_create=drop_test_db)

    print 'syncdb: %s' % type(syncdb)
    if env['project_type'] == "django" and syncdb:
        # if we are using South we need to do the migrations aswell
        use_migrations = False
        for app in project_settings.django_apps:
            if os.path.exists(os.path.join(env['django_dir'], app, 'migrations')):
                use_migrations = True
        _manage_py(['syncdb', '--noinput'])
        if use_migrations:
            _manage_py(['migrate', '--noinput'])

def db_exists(db_user, db_pw, db_name, db_port, db_host):
    db_exist_call = ['mysql', '-u', db_user, '-p'+db_pw]
    db_exist_call += ['--host=%s' % db_host]
                      
    if db_port != None:
        db_exist_call += ['--port=%s' % db_port]
        
    db_exist_call += [db_name, '-e', 'quit']
    
    return _call_command(db_exist_call) == 0
    

def create_test_db(drop_after_create=True):
    db_engine, db_name, db_user, db_pw, db_port, db_host = _get_django_db_settings()
    
    test_db_name = 'test_' + db_name
    ret = _mysql_exec_as_root('CREATE DATABASE %s CHARACTER SET utf8' % test_db_name)
    ret = _mysql_exec_as_root(('GRANT ALL PRIVILEGES ON %s.* TO \'%s\'@\'localhost\' IDENTIFIED BY \'%s\'' % 
        (test_db_name, db_user, db_pw)))
    if drop_after_create:
        ret = _mysql_exec_as_root(('DROP DATABASE %s' % test_db_name))

def dump_db(dump_filename='db_dump.sql'):
    """Dump the database in the current working directory"""
    project_name = project_settings.django_dir.split('/')[-1]
    db_engine, db_name, db_user, db_pw, db_port, db_host = _get_django_db_settings()
    if not db_engine.endswith('mysql'):
        print 'dump_db only knows how to dump mysql so far'
        sys.exit(1)
    dump_cmd = ['/usr/bin/mysqldump', '--user='+db_user, '--password='+db_pw,
                '--host='+db_host]
    if db_port != None:
        dump_cmd.append('--port='+db_port)
    dump_cmd.append(db_name)
    
    dump_file = open(dump_filename, 'w')
    if env['verbose']:
        print 'Executing dump command: %s\nSending stdout to %s' % (' '.join(dump_cmd), dump_filename)
    _call_command(dump_cmd, stdout=dump_file)
    dump_file.close()

def update_git_submodules():
    """If this is a git project then check for submodules and update"""
    git_modules_file = os.path.join(env['project_dir'], '.gitmodules')
    if os.path.exists(git_modules_file):
        git_submodule_cmd =['git', 'submodule', 'update', '--init']
        _call_wrapper(git_submodule_cmd, cwd=env['project_dir'])

def setup_db_dumps(dump_dir):
    """ set up mysql database dumps in root crontab """
    if not os.path.isabs(dump_dir):
        print 'dump_dir must be an absolute path, you gave %s' % dump_dir
        sys.exit(1)
    project_name = project_settings.django_dir.split('/')[-1]
    cron_file = os.path.join('/etc', 'cron.daily', 'dump_'+project_name)

    db_engine, db_name, db_user, db_pw, db_port, db_host = _get_django_db_settings()
    if db_engine.endswith('mysql'):
        _create_dir_if_not_exists(dump_dir)
        dump_file_stub = os.path.join(dump_dir, 'daily-dump-')

        # has it been set up already
        cron_grep = _call_wrapper('sudo crontab -l | grep mysqldump', shell=True)
        if cron_grep == 0:
            return
        if os.path.exists(cron_file):
            return

        # write something like:
        # 30 1 * * * mysqldump --user=osiaccounting --password=aptivate --host=127.0.0.1 osiaccounting >  /var/osiaccounting/dumps/daily-dump-`/bin/date +\%d`.sql

        # don't use "with" for compatibility with python 2.3 on whov2hinari
        f = open(cron_file, 'w')
        try:
            f.write('#!/bin/sh\n')
            f.write('/usr/bin/mysqldump --user=%s --password=%s --host=%s --port=%s ' %
                    (db_user, db_pw, db_host, db_port))
            f.write('%s > %s' % (db_name, dump_file_stub))
            f.write(r'`/bin/date +\%d`.sql')
            f.write('\n')
        finally:
            f.close()
        
        os.chmod(cron_file, 0755)


def run_tests(*extra_args):
    """Run the django tests.

    With no arguments it will run all the tests for you apps (as listed in
    project_settings.py), but you can also pass in multiple arguments to run
    the tests for just one app, or just a subset of tests. Examples include:

    ./tasks.py run_tests:myapp
    ./tasks.py run_tests:myapp.ModelTests,myapp.ViewTests.my_view_test
    """
    args = ['test', '-v0']

    if extra_args:
        args += extra_args
    else:
        # default to running all tests
        args += project_settings.django_apps

    _manage_py(args)


def quick_test(*extra_args):
    """Run the django tests with local_settings.py.dev_fasttests

    local_settings.py.dev_fasttests (should) use port 3307 so it will work
    with a mysqld running with a ramdisk, which should be a lot faster. The
    original environment will be reset afterwards.

    With no arguments it will run all the tests for you apps (as listed in
    project_settings.py), but you can also pass in multiple arguments to run
    the tests for just one app, or just a subset of tests. Examples include:

    ./tasks.py quick_test:myapp
    ./tasks.py quick_test:myapp.ModelTests,myapp.ViewTests.my_view_test
    """
    original_environment = _infer_environment()

    link_local_settings('dev_fasttests')
    create_ve()
    update_db()
    run_tests(*extra_args)
    link_local_settings(original_environment)


def _install_django_jenkins():
    """ ensure that pip has installed the django-jenkins thing """
    pip_bin = os.path.join(env['ve_dir'], 'bin', 'pip')
    cmd = [pip_bin, 'install', '-E', env['ve_dir'], 'django-jenkins']
    _call_wrapper(cmd)

def _manage_py_jenkins():
    """ run the jenkins command """
    args = ['jenkins', ]
    args += ['--pylint-rcfile', os.path.join(env['project_dir'], 'jenkins', 'pylint.rc')]
    coveragerc_filepath = os.path.join(env['project_dir'], 'jenkins', 'coverage.rc')
    if os.path.exists(coveragerc_filepath):
        args += ['--coverage-rcfile', coveragerc_filepath]
    args += project_settings.django_apps
    _manage_py(args, cwd=env['project_dir'])

def run_jenkins():
    """ make sure the local settings is correct and the database exists """
    update_ve()
    _install_django_jenkins()
    create_private_settings()
    link_local_settings('jenkins')
    clean_db()
    update_db()
    _manage_py_jenkins()


def _infer_environment():
    local_settings = os.path.join(env['django_dir'], 'local_settings.py')
    if os.path.exists(local_settings):
        return os.readlink(local_settings).split('.')[-1]
    else:
        print 'no environment set, or pre-existing'
        sys.exit(2)


def deploy(environment=None):
    """Do all the required steps in order"""
    if environment == None:
        environment = _infer_environment()

    create_private_settings()
    link_local_settings(environment)
    update_git_submodules()
    create_ve()
    update_db()

def patch_south():
    """ patch south to fix pydev errors """
    south_db_init = os.path.join(env['ve_dir'],
                'lib/python2.6/site-packages/south/db/__init__.py')
    patch_file = os.path.join(env['deploy_dir'], 'south.patch')
    cmd = ['patch', '-N', '-p0', south_db_init, patch_file]
    _call_wrapper(cmd)
