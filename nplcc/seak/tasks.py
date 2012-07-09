from celery.task import task

@task()
def marxan_start(m):
    print "Setting up dirs"
    m.setup()
    print "writing .dat files"
    m.write_pu()
    m.write_puvcf()
    m.write_spec()
    m.write_input()
    print "running Marxan..."
    m.run()
    print 
    print "COMPLETE"
    return m.best

@task()
def add(x,y):
    return x + y


