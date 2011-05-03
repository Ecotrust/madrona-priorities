from celery.decorators import task

@task
def marxan_start(m):
    print "Setting up dirs"
    m.setup()
    print "writing .dat files"
    m.write_pu()
    m.write_puvcf()
    m.write_spec()
    m.write_input()
    print "running Marxan with ..."
    for s in m.species:
        print "  ", s 
    m.run()
    print 
    print "COMPLETE"
    return m.best

@task()
def add(x,y):
    return x + y


