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


def test():
    with cd(LOCAL_DATA_DIR):
        run('ls -alt')

def virtualenv(command, user=None):
    with cd(env.directory):
        if not user:
            run(env.activate + '&&' + command)
        else:
            sudo(env.activate + '&&' + command, user=user)

def maintenance_on():
    with cd(env.directory):
        run('touch MAINTENANCE_MODE')

def maintenance_off():
    with cd(env.directory):
        run('rm MAINTENANCE_MODE')

def deploy():
    """
    Update to new revision
    """
    maintenance_on()
    with cd(env.directory):
        run("git checkout %s" % BRANCH)
        run("git pull")
        virtualenv("python priorities/manage.py install_media")
        virtualenv("python priorities/manage.py syncdb")
        virtualenv("python priorities/manage.py migrate")
        run("touch deploy/wsgi.py")
    maintenance_off()

def import_dataset():
    """
    upload a new dataset
    """
    pass

    with cd(env.directory):
        maintenance_on()

        # upload data if not there already
        with settings(warn_only=True):
            if run("test -d priorities/data/%s" % dirname).failed:
                put(local_data_dir, 'priorities/data/')  

        # Clear server cache
        virtualenv("python priorities/manage.py clear_cache")

        # clear tilestache cache
        sudo("rm -rf %s" % STACHE_DIR)

        # make sure postgres user can write out
        sudo("chmod 777 marxan_output/template") # TODO probably a better way to handle this

        # Load data
        virtualenv("python priorities/manage.py import_planning_units \
                %(data)s/%(pu_simple)s \
                %(data)s/%(xls)s \
                %(data)s/%(pu)s" % {'data': 'priorities/data/' + dirname, 'pu_simple': pu_simple, 'xls': xls, 'pu': pu })

        # precache
        virtualenv("python priorities/manage.py precache")

        # perms for tilestache dir
        run("sudo chown www-data -R %s" % STACHE_DIR)
        run("sudo chmod 777 -R %s" % STACHE_DIR)

        # Restart the application server and the celeryd process
        run("touch deploy/wsgi.py")
        run("touch deploy/tilestache_wsgi.py")

        # restart celeryd TODO 
        print
        print "##### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        print " TODO: you need to restart `celeryd` on the server manually!"
        print "##### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        print 

    print "###########################################################"
    print "Test and run `fab maintenance_off` when ready"
    print "###########################################################"

