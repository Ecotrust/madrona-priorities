from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from local_data import *
import os

APP = 'nplcc'
BRANCH = APP
STACHE_DIR = "/tmp/nplcc-stache" 
env.directory = '/usr/local/apps/%s' % APP
env.hosts = ['ninkasi.ecotrust.org']
env.activate = 'source %s' % os.path.join(env.directory, 'env-%s' % APP,'bin','activate')
env.deploy_user = 'www-data'


def virtualenv(command, user=None):
    with cd(env.directory):
        if not user:
            run(env.activate + '&&' + command)
        else:
            sudo(env.activate + '&&' + command, user=user)

def maintenance_on():
    """
    Maintenance mode ON (i.e. Site goes down for maintenance )
    """
    with cd(env.directory):
        run('touch MAINTENANCE_MODE')

def maintenance_off():
    """
    Maintenance mode OFF (i.e. Site is back online )
    """
    with cd(env.directory):
        run('rm MAINTENANCE_MODE')

def fix_permissions():
    """
    Make sure all directories have appropriate permissions
    """
    with cd(env.directory):
        sudo("chgrp www-data -R marxan_output")
        sudo("chmod 775 -R marxan_output")
        sudo("chmod 777 marxan_output/template") # TODO probably a better way to handle this
        run("sudo chown www-data -R %s" % STACHE_DIR)
        run("sudo chmod 755 -R %s" % STACHE_DIR)
        run("sudo chown www-data -R mediaroot")

def deploy():
    """
    Update remote server to new code revision.
    """
    maintenance_on()
    with cd(env.directory):
        run("git checkout %s" % BRANCH)
        run("git pull")
        virtualenv("python priorities/manage.py install_media")
        virtualenv("python priorities/manage.py syncdb")
        virtualenv("python priorities/manage.py migrate")
        run("touch deploy/wsgi.py")
        restart_celery()

    print "###########################################################"
    print "Test and run `fab maintenance_off` when ready"
    print "###########################################################"

def restart_celery():
    sudo("/etc/init.d/celeryd_%s restart" % APP)
    sudo("/etc/init.d/celeryd_%s status" % APP)

def import_dataset():
    """
    Upload a new dataset. Edit local_data.py first!
    """
    pass

    with cd(env.directory):
        maintenance_on()

        # upload data if not there already
        #with settings(warn_only=True):
        #    if run("test -d priorities/data/%s" % dirname).failed:
        put(local_data_dir, 'priorities/data/')  

        # Clear server cache
        virtualenv("python priorities/manage.py clear_cache")

        # clear tilestache cache
        sudo("rm -rf %s" % STACHE_DIR)

        # make sure postgres user can write out
        sudo("chmod 777 marxan_output/template") # TODO probably a better way to handle this
        sudo("chgrp www-data marxan_output")
        sudo("chmod 775 marxan_output")

        # Load data
        virtualenv("python priorities/manage.py import_planning_units \
                %(data)s/%(pu_simple)s \
                %(data)s/%(xls)s \
                %(data)s/%(pu)s" % {'data': 'priorities/data/' + dirname, 'pu_simple': pu_simple, 'xls': xls, 'pu': pu })

        # precache
        sudo("chmod 777 -R %s" % STACHE_DIR)
        virtualenv("python priorities/manage.py precache")

        # perms for tilestache dir
        sudo("chown www-data -R %s" % STACHE_DIR)
        sudo("chmod 755 -R %s" % STACHE_DIR)

        # Restart the application server and the celeryd process
        run("touch deploy/wsgi.py")
        run("touch deploy/tilestache_wsgi.py")
        restart_celery()

    print "###########################################################"
    print "Test and run `fab maintenance_off` when ready"
    print "###########################################################"

def local_import():
        actv = '. /usr/local/src/madrona-priorities/env-priorities/bin/activate'
        command = "python manage.py import_planning_units \
                %(data)s/%(pu_simple)s \
                %(data)s/%(xls)s \
                %(data)s/%(pu)s" % {'data': local_data_dir, 'pu_simple': pu_simple, 'xls': xls, 'pu': pu }
        local(actv + ' && ' + command)

