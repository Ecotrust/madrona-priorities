import os
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.contrib.auth.models import User
from seak.models import ConservationFeature, PlanningUnit, Cost, PuVsCf, PuVsCost
from django.contrib.gis.utils import LayerMapping
from shapely.geometry import Point
from shapely import wkt, wkb
from shapely.ops import cascaded_union
from django.contrib.gis.gdal import DataSource

class Command(BaseCommand):
    help = 'Imports shapefile with conservationfeatures/costs and xls metadata to planning units'
    args = '<shp_path xls_path>'

    def handle(self, *args, **options):
        from django.core.management.base import CommandError
        from django.conf import settings
        try: 
            shp = args[0]
            xls = args[1]
            assert os.path.exists(shp)
            assert os.path.exists(xls)
        except:
            raise CommandError("Specify shp and xls file\n python manage.py import_planning_units test.shp test.xls")


        backup = False
        import_shp = True
        app = 'seak'

        modls = ['ConservationFeature',  'Cost', 'PuVsCf', 'PuVsCost']
        if import_shp:
            modls.append('PlanningUnit')

        # backup old tables
        if backup:
            print "backing up old tables to /tmp/"
            from django.core.management.commands.dumpdata import Command as Dumper
            from django.core.management.base import CommandError
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
        ms = [ConservationFeature, Cost, PuVsCf, PuVsCost]
        if import_shp:
            ms.append(PlanningUnit)
        for m in ms: 
            objs = m.objects.all().delete()
            assert len(m.objects.all()) == 0

        # Load ConservationFeatures from xls
        print
        print "Loading ConservationFeatures"
        import xlrd
        book = xlrd.open_workbook(xls)
        sheet = book.sheet_by_name("ConservationFeatures")
        headers = [str(x).strip() for x in sheet.row_values(0)] #returns all the CELLS of row 0,

        fieldnames = ['name', 'uid', 'level1','level2','level3','level4', 'level5', 'dbf_fieldname', 'units']

        assert len(headers) == len(fieldnames)
        for h in range(len(headers)): 
            if headers[h] != fieldnames[h]:
                print "WARNING: field %s is '%s' in the xls file but model is expecting '%s' ... OK?" % (h, headers[h], fieldnames[h])

        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
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
        headers = [str(x).strip() for x in sheet.row_values(0)] #returns all the CELLS of row 0,

        fieldnames = ['name', 'uid', 'dbf_fieldname', 'units', 'desc']

        assert len(headers) == len(fieldnames)
        for h in range(len(headers)): 
            if headers[h] != fieldnames[h]:
                print "WARNING: field %s is '%s' in the xls file but model is expecting '%s' ... OK?" % (h, headers[h], fieldnames[h])

        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
            params = dict(zip(fieldnames, vals))
            c = Cost(**params)
            c.save()

        cs = Cost.objects.all()
        assert len(cs) == sheet.nrows - 1

        # Load PU from shpfile
        print
        print "Loading planning units from Shapefile"
        ds = DataSource(shp)
        layer = ds[0]
        print "WARNING It is your responsibility to make sure the shapefile projection below matches srid %s" % settings.GEOMETRY_DB_SRID
        print layer.srs

        sheet = book.sheet_by_name("PlanningUnits")
        headers = [str(x.strip()) for x in sheet.row_values(0)] #returns all the CELLS of row 0,
        fieldnames = ['name_field', 'fid_field']
        assert len(headers) == len(fieldnames)
        for h in range(len(headers)): 
            if headers[h] != fieldnames[h]:
                print "WARNING: field %s is '%s' in the xls file but model is expecting '%s' ... OK?" % (h, headers[h], fieldnames[h])
        for i in xrange(1, sheet.nrows):
            vals = [str(x.strip()) for x in sheet.row_values(i)]
            params = dict(zip(fieldnames, vals))
 
        mapping = {
            'name' : params['name_field'],
            'fid' : params['fid_field'], 
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
                amt = feature.get(cf.dbf_fieldname)
                # TODO allow negative or null values
                """
                if amt is None or amt < 0:
                    amt = 0
                """
                obj = PuVsCf(pu=pu, cf=cf, amount=amt)
                obj.save()

            for c in cs: 
                amt = feature.get(c.dbf_fieldname)
                if amt is None or amt < 0:
                    # DONT allow negative or null values
                    amt = 0
                obj = PuVsCost(pu=pu, cost=c, amount=amt)
                obj.save()

        assert len(PuVsCf.objects.all()) == len(pus) * len(cfs_with_fields)
        assert len(PuVsCost.objects.all()) == len(pus) * len(cs)

        # Export the puvscf table to csv directly 
        from django.conf import settings
        out = os.path.realpath(os.path.join(settings.MARXAN_TEMPLATEDIR, 'puvcf.dat'))
        print "Exporting the table to %s" % out
        query = """
            COPY (SELECT cf_id as species, pu_id as pu, amount 
                FROM %s_puvscf
                ORDER BY pu)
            TO '%s'
            WITH DELIMITER ','
            CSV HEADER
        """ % (app, out)
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(query)
