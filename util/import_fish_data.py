from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','wp',__file__)))

import settings
setup_environ(settings)
#==================================#
from arp.models import ConservationFeature, PlanningUnit, Cost, PuVsCf, PuVsCost

#------------------------------------#
# Config
xls = "../data/PrioritySpeciesList_DRAFT_mp.xls" # NOT xlsx
shp = "../data/HUC8_FocalSpecies.shp"
backup = False
#------------------------------------#

modls = ['ConservationFeature',  'Cost', 'PuVsCf', 'PuVsCost',
        #'PlanningUnit'
        ]

# backup old tables
if backup:
    print "backing up old tables to /tmp/"
    from django.core.management.commands.dumpdata import Command as Dumper
    from django.core.management.base import CommandError
    app = 'arp'
    for modl in modls:
        try:
            fix = Dumper.handle(Dumper(), "%s.%s" % (app, modl.lower()), format='json', indent=4)
        except CommandError, message:
            print "# dumpdata raised a CommandError: %s" % message
        else:
            fixname = "/tmp/%s_%s.json" % (app, modl.lower())
            fh = open(os.path.join(fixname), "w+")
            fh.write(fix)
            fh.close()

# Clear them out
print
print "Cleaning out old tables"
for m in ConservationFeature, Cost, PuVsCf, PuVsCost: #PlanningUnit, 
    objs = m.objects.all()
    for obj in objs:
        obj.delete()
    assert len(m.objects.all()) == 0

# Load CF from xls
print
print "Loading ConservationFeatures"
import xlrd
book = xlrd.open_workbook(xls)
sheet = book.sheet_by_name("ConservationFeatures")
headers = [str(x.strip()) for x in sheet.row_values(0)] #returns all the CELLS of row 0,

fieldnames = ['sci_name', 'common_name', 'name', 'level1','level2','level3','level4', 'level5',
           'esu_dps', 'dbf_fieldname', 'units']

assert len(headers) == len(fieldnames)
for h in range(len(headers)): 
    if headers[h] != fieldnames[h]:
        print "WARNING: field %s is named '%s' in the xls file but the model is expecting '%s' ... OK?" % (h, headers[h], fieldnames[h])

for i in xrange(1, sheet.nrows):
    vals = [str(x.strip()) for x in sheet.row_values(i)]
    params = dict(zip(fieldnames, vals))
    cf = ConservationFeature(**params)
    cf.save()

cfs = ConservationFeature.objects.all()
assert len(cfs) == sheet.nrows - 1

for cf in cfs:
    fname = cf.dbf_fieldname
    if fname is None or fname == '':
        print "WARNING: No dbf_fieldname specified for %s, no info can be extracted from shapefile for this species" % cf.name
        continue

# Load Costs from xls
print
print "Loading Costs"
sheet = book.sheet_by_name("Costs")
headers = [str(x.strip()) for x in sheet.row_values(0)] #returns all the CELLS of row 0,

fieldnames = ['name', 'dbf_fieldname', 'units']

assert len(headers) == len(fieldnames)
for h in range(len(headers)): 
    if headers[h] != fieldnames[h]:
        print "WARNING: field %s is named '%s' in the xls file but the model is expecting '%s' ... OK?" % (h, headers[h], fieldnames[h])

for i in xrange(1, sheet.nrows):
    vals = [str(x.strip()) for x in sheet.row_values(i)]
    params = dict(zip(fieldnames, vals))
    c = Cost(**params)
    c.save()

cs = Cost.objects.all()
assert len(cs) == sheet.nrows - 1

# Load PU from shpfile
print
print "Loading planning units from Shapefile"
from django.contrib.gis.gdal import DataSource
ds = DataSource(shp)
layer = ds[0]
print "WARNING It is your responsibility to make sure the shapefile projection below matches srid %s" % settings.GEOMETRY_DB_SRID
print layer.srs

from django.contrib.gis.utils import LayerMapping
mapping = {
    'name' : 'SUBBASIN',
    'fid' : 'OBJECTID',
    'area' : 'SqMi_orig',
    'geometry' : 'MULTIPOLYGON',
}

if "PlanningUnit" in modls:
    lm = LayerMapping(PlanningUnit, shp, mapping, transform=False, encoding='iso-8859-1')
    lm.save(strict=True, verbose=False)
else:
    print ".... not loading shp"

pus = PlanningUnit.objects.all()
assert len(layer) == len(pus)

print 
print "Loading costs and habitat amounts associated with each planning unit"
cfs_with_fields = [x for x in cfs if x.dbf_fieldname is not None and x.dbf_fieldname != '' ]
for feature in layer:
    pu = pus.get(fid=feature.get(mapping['fid']))
    for cf in cfs_with_fields:
        obj = PuVsCf(pu=pu, cf=cf, amount=feature.get(cf.dbf_fieldname))
        obj.save()

    for c in cs: 
        obj = PuVsCost(pu=pu, cost=c, amount=feature.get(c.dbf_fieldname))
        obj.save()

assert len(PuVsCf.objects.all()) == len(pus) * len(cfs_with_fields)
assert len(PuVsCost.objects.all()) == len(pus) * len(cs)

