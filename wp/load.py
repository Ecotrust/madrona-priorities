from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(__file__))

import settings
setup_environ(settings)

#===================================#
from django.contrib.gis.utils import LayerMapping
from arp.models import Watershed

a = Watershed.objects.all()
for i in a:
    i.delete()

mapping = {
    'fid': "OBJECTID", 
    'coho': 'Coho_m', 
    'chinook': 'Chnk_m', 
    'steelhead': 'StlHd_m', 
    'climate_cost': 'pcp80bdfmm', 
    'area': 'area_km2',
    'name': 'HU_12_NAME',
    'huc12': 'HUC_12',
    'geometry': 'POLYGON'
}

lm = LayerMapping(Watershed,'../media/staticmap/data/huc6_4326.shp',mapping)
lm.save(verbose=True)
