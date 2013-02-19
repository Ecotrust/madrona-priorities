SECRET_KEY = 'secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'priorities',
        'USER': 'vagrant',
    }
}

# This should be a local folder created for use with the install_media command 
MEDIA_ROOT = '/usr/local/apps/madrona-priorities/mediaroot/'
MEDIA_URL = 'http://localhost:8000/media/'
STATIC_URL = 'http://localhost:8000/media/'

POSTGIS_TEMPLATE='template1'
DEBUG = True
TEMPLATE_DEBUG = DEBUG 

ADMINS = (
        ('Madrona', 'madrona@ecotrust.org')
        ) 

import logging
logging.getLogger('django.db.backends').setLevel(logging.ERROR)
import os
LOG_FILE = os.path.join(os.path.dirname(__file__),'..','seak.log')

MARXAN_BIN =  os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'marxan_bin', 'MarOpt_v243_Linux32')) # or 64 bit?
MARXAN_OUTDIR =  '/home/vagrant/marxan_output'  # for vagrant boxes, put this outside the shared dir so we can symlink
MARXAN_TEMPLATEDIR = os.path.join(MARXAN_OUTDIR, 'template')
