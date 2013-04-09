import os
from django.core.management.base import BaseCommand, CommandError
from seak.models import ConservationFeature, PlanningUnit, Cost, Aux, PuVsCf, PuVsCost, PuVsAux, DefinedGeography
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.template.defaultfilters import slugify
from django.core.management import call_command
from seak.jenks import get_jenks_breaks
from madrona.layer_manager.models import Layer, Theme 
import json

def find_possible(key, possible):
    """
    Given a key and a list, find possible matches 
    Right now it just checks for case
    """
    if key in possible:
        return key
    possible = [x for x in possible if x.lower() == key]
    if possible == []:
        return None
    return possible[0]

class Command(BaseCommand):
    help = 'Imports shapefile with conservationfeatures/costs and xls metadata to planning units'
    args = '<shp_path> <xls_path> <optional: full resolution shp_path>'

    def handle(self, *args, **options):
        from django.conf import settings

        try: 
            shp = args[0]
            xls = args[1]
            assert os.path.exists(shp)
            assert os.path.exists(xls)
            print "Using %s as the data layer" % shp
            print "Using %s as the xls metadata" % xls
        except (AssertionError, IndexError):
            raise CommandError("Specify shp and xls file\n \
                    python manage.py import_planning_units test.shp test.xls <optional: full res shp>")

        try:
            fullres_shp = args[2]
            assert os.path.exists(fullres_shp)
            print "Using %s as the full-res display layer" % fullres_shp
        except (AssertionError, IndexError):
            print "Using %s as the full-res display layer" % shp
            fullres_shp = shp

        backup = False
        import_shp = True
        app = 'seak'

        modls = ['ConservationFeature',  'Cost', 'Aux', 'PuVsCf', 'PuVsCost', 'PuVsAux']
        if import_shp:
            modls.append('PlanningUnit')

        # backup old tables
        if backup:
            print "backing up old tables to /tmp/"
            from django.core.management.commands.dumpdata import Command as Dumper
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
        ms = [ConservationFeature, Cost, Aux, PuVsCf, PuVsCost, PuVsAux,DefinedGeography]
        if import_shp:
            ms.append(PlanningUnit)
        for m in ms: 
            m.objects.all().delete()
            assert len(m.objects.all()) == 0

        # Loading planning units from Shapefile
        print "Loading planning units from Shapefile"
        ds = DataSource(shp)
        layer = ds[0]

        # Load ConservationFeatures from xls
        print
        print "Loading ConservationFeatures"
        import xlrd
        book = xlrd.open_workbook(xls)
        sheet = book.sheet_by_name("ConservationFeatures")
        headers = [str(x).strip() for x in sheet.row_values(0)] #returns all the CELLS of row 0,

        fieldnames = ['name', 'uid', 'level1', 'level2', 'dbf_fieldname', 'units','desc']

        if len(headers) < len(fieldnames):
            raise Exception("The ConservationFeatures sheet has errors: expecting these headers\n  %s\nBut found\n  %s" % (fieldnames, headers))

        for h in range(len(fieldnames)): 
            if headers[h].lower() != fieldnames[h].lower():
                raise Exception("field %s is '%s' in the xls file but model is expecting '%s'." % (h, headers[h], fieldnames[h]))

        extra_fields = headers[len(fieldnames):] 
        if len(extra_fields) > 0:
            print "WARNING: extra fields in ConservationFeatures sheet not being used\n    ", extra_fields

        uids = []
        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
            params = dict(zip(fieldnames, vals))
            if params['uid'] in uids:
                raise Exception("Already used UID %s" % params['uid'])
            else:
                uids.append(params['uid'])
            cf = ConservationFeature(**params)
            cf.save()

        cfs = ConservationFeature.objects.all()
        # ensure uniqueness
        level_strings = []
        names = []
        for cf in cfs:
            if cf.level_string in level_strings:
                raise Exception("Levels are not unique: " + cf.level_string)
            if slugify(cf.name) in names:
                raise Exception("Name is not unique: " + cf.name)
            level_strings.append(cf.level_string)
            names.append(slugify(cf.name))
        assert len(cfs) == sheet.nrows - 1

        for cf in cfs:
            fname = cf.dbf_fieldname
            if fname not in layer.fields:
                if find_possible(fname, layer.fields):
                    raise Exception("DBF has no field named `%s`.\n Did you mean `%s`" % (fname, 
                        find_possible(fname, layer.fields)))
                raise Exception("DBF has no field named %s (it IS case sensitive).\n\n %s" % (fname, 
                    layer.fields))
            if fname is None or fname == '':
                print "WARNING: No dbf_fieldname specified for %s" % cf.name
                print "   no info can be extracted from shapefile for this conservation feature"
                continue

        # Load Costs from xls
        print
        print "Loading Costs"
        sheet = book.sheet_by_name("Costs")
        headers = [str(x).strip() for x in sheet.row_values(0)] #returns all the CELLS of row 0,

        fieldnames = ['name', 'uid', 'dbf_fieldname', 'units', 'desc']

        if len(headers) < len(fieldnames):
            raise Exception("The Costs sheet has errors: expecting these headers\n  %s\nBut found\n  %s" % (fieldnames, headers))

        for h in range(len(fieldnames)): 
            if headers[h].lower() != fieldnames[h].lower():
                raise Exception("field %s is '%s' in the xls file but model is expecting '%s'." % (h, headers[h], fieldnames[h]))

        extra_fields = headers[len(fieldnames):] 
        if len(extra_fields) > 0:
            print "WARNING: extra fields in Cost sheet not being used\n    ", extra_fields

        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
            params = dict(zip(fieldnames, vals))
            c = Cost(**params)
            c.save()

        cs = Cost.objects.all()
        assert len(cs) == sheet.nrows - 1

        for c in cs:
            fname = c.dbf_fieldname
            if fname not in layer.fields:
                if find_possible(fname, layer.fields):
                    raise Exception("DBF has no field named `%s`.\n Did you mean `%s`" % (fname,
                        find_possible(fname, layer.fields)))
                raise Exception("DBF has no field named %s (it IS case sensitive).\n\n %s" % (fname, 
                    layer.fields))

        # Load Aux from xls
        print
        print "Loading Auxillary Data fields"
        sheet = book.sheet_by_name("Other Fields")
        headers = [str(x).strip() for x in sheet.row_values(0)] #returns all the CELLS of row 0,

        fieldnames = ['name', 'uid', 'dbf_fieldname', 'units', 'desc']

        if len(headers) < len(fieldnames):
            raise Exception("The Other Fields sheet has errors: expecting these headers\n  %s\nBut found\n  %s" % (fieldnames, headers))

        for h in range(len(fieldnames)): 
            if headers[h].lower() != fieldnames[h].lower():
                raise Exception("field %s is '%s' in the xls file but model is expecting '%s'." % (h, headers[h], fieldnames[h]))

        extra_fields = headers[len(fieldnames):] 
        if len(extra_fields) > 0:
            print "WARNING: extra fields in Other Fields sheet not being used\n    ", extra_fields

        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
            params = dict(zip(fieldnames, vals))
            aux = Aux(**params)
            aux.save()

        auxs = Aux.objects.all()
        assert len(auxs) == sheet.nrows - 1

        for aux in auxs:
            fname = aux.dbf_fieldname
            if fname not in layer.fields:
                if find_possible(fname, layer.fields):
                    raise Exception("DBF has no field named `%s`.\n Did you mean `%s`" % (fname,
                        find_possible(fname, layer.fields)))
                raise Exception("DBF has no field named %s (it IS case sensitive).\n\n %s" % (fname, 
                    layer.fields))

        # Load PU from shpfile
        print
        print "WARNING It is your responsibility to make sure the shapefile projection below matches srid %s" % settings.GEOMETRY_DB_SRID
        print layer.srs

        sheet = book.sheet_by_name("PlanningUnits")
        headers = [str(x.strip()) for x in sheet.row_values(0)] #returns all the CELLS of row 0,
        fieldnames = ['name_field', 'fid_field', 'null_value', 'area_field']
        if len(headers) != len(fieldnames):
            raise Exception("The PlanningUnits sheet has errors: expecting these headers\n  %s\nBut found\n  %s" % (fieldnames, headers))
        for h in range(len(headers)): 
            if headers[h] != fieldnames[h]:
                print "WARNING: field %s is '%s' in the xls file but model is expecting \
                       '%s' ... OK?" % (h, headers[h], fieldnames[h])
        for i in xrange(1, sheet.nrows):
            #vals = [str(x.strip()) for x in sheet.row_values(i)]
            vals = sheet.row_values(i)
            params = dict(zip(fieldnames, vals))
 
        mapping = {
            'name' : params['name_field'],
            'fid' : params['fid_field'], 
            'geometry' : 'MULTIPOLYGON',
        }

        if params['area_field']:
            mapping['calculated_area'] = params['area_field']

        NULL_VALUE = params['null_value']
        FID_FIELD = params['fid_field']

        if "PlanningUnit" in modls:
            lm = LayerMapping(PlanningUnit, shp, mapping, transform=False, encoding='iso-8859-1')
            lm.save(strict=True, verbose=False)
        else:
            print ".... not loading shp"

        pus = PlanningUnit.objects.all()
        if len(layer) != len(pus):
            raise Exception("Layer has %d features but %s planning units are loaded" % (len(layer),len(pus)))

        print
        print "Generating tile configuration files"
        cfs_with_fields = [x for x in cfs if x.dbf_fieldname is not None and x.dbf_fieldname != '' ]

        xml_template = """<?xml version="1.0"?>
<!DOCTYPE Map [
<!ENTITY google_mercator "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over">
]>
<Map srs="&google_mercator;">
    <Style name="pu" filter-mode="first">
        %(extra_rules)s
        <Rule>
            <PolygonSymbolizer fill="#ffffff" fill-opacity="0.0" />
        </Rule>
    </Style>
    <Style name="pu-outline" filter-mode="first">
        <Rule>
            <LineSymbolizer stroke="#222222" stroke-width="0.5" stroke-opacity="1" stroke-linejoin="round" />
        </Rule>
    </Style>
    <Layer name="layer" srs="&google_mercator;">
        <StyleName>pu-outline</StyleName>
        <StyleName>pu</StyleName>
        <Datasource>
            <Parameter name="type">shape</Parameter>
            <Parameter name="file">%(shppath)s</Parameter>
        </Datasource>
    </Layer>
</Map>""" 
        xml = xml_template % {'shppath': os.path.abspath(fullres_shp), 'extra_rules': ''}

        if not os.path.exists(settings.TILE_CONFIG_DIR):
            os.makedirs(settings.TILE_CONFIG_DIR)

        with open(os.path.join(settings.TILE_CONFIG_DIR, 'planning_units.xml'), 'w') as fh:
            print "  writing planning_units.xml"
            fh.write(xml)

        # Get all dbf fieldnames for the utfgrids
        all_dbf_fieldnames = [cf.dbf_fieldname for cf in cfs_with_fields]
        all_dbf_fieldnames.extend([c.dbf_fieldname for c in cs])
        all_dbf_fieldnames.append(params['name_field'])

        cfg = {
            "logging": "warning",
            "cache": {
                "name": "Multi",
                "tiers": [
                    #{ "name": "Memcache", "servers": ["127.0.0.1:11211"] },
                    { "name": "Disk", "path": "/tmp/%s-stache" % slugify(settings.APP_NAME) }
                ]
            },
            "layers": {
                "planning_units":
                {
                    "provider": 
                     { "name": "mapnik", "mapfile": "planning_units.xml" },
                    "metatile": 
                    { "rows": 4, "columns": 4, "buffer": 64 }
                },
                "utfgrid":
                {
                    "provider":
                    {
                        "class": "TileStache.Goodies.Providers.MapnikGrid:Provider",
                        "kwargs":
                        {
                            "mapfile": "planning_units.xml", 
                            "fields": all_dbf_fieldnames,
                            "layer_index": 0,
                            "scale": 4
                        }
                    }
                }
            }
        }


        print 
        print "create mapnik xml file symbolizing each conservation features and cost"
        numeric_dbf_fieldnames = all_dbf_fieldnames[:]
        numeric_dbf_fieldnames.remove(params['name_field'])
        for fieldname in numeric_dbf_fieldnames:
            vals = layer.get_fields(fieldname)
            vals = [x for x in vals if x >= 0 ]
            breaks = sorted(get_jenks_breaks(vals, 4))
            breaks = [0.000001 if x == 0.0 else x for x in breaks]

            colors = {
                'c1': '#CC4C02', # high 
                'c2': '#FE9929', 
                'c3': '#FED98E', 
                'c4': '#FFFFD4', # low
                'c5': '#FFFFFF', # zero
            }

            tdict = {"fieldname": fieldname, 'b1': breaks[1], 'b2': breaks[2], 'b3': breaks[3]}
            tdict.update(colors)
 
            extra_rules = """
                <Rule>
                    <Filter>([%(fieldname)s] &gt;= %(b3)f)</Filter>
                    <PolygonSymbolizer fill="%(c1)s" fill-opacity="1.0" />
                </Rule>
                <Rule>
                    <Filter>([%(fieldname)s] &gt;= %(b2)f)</Filter>
                    <PolygonSymbolizer fill="%(c2)s" fill-opacity="1.0" />
                </Rule>
                <Rule>
                    <Filter>([%(fieldname)s] &gt;= %(b1)f)</Filter>
                    <PolygonSymbolizer fill="%(c3)s" fill-opacity="1.0" />
                </Rule>
                <Rule>
                    <Filter>([%(fieldname)s] &gt; 0)</Filter>
                    <PolygonSymbolizer fill="%(c4)s" fill-opacity="1.0" />
                </Rule>
                <Rule>
                    <Filter>([%(fieldname)s] = 0)</Filter>
                    <PolygonSymbolizer fill="%(c5)s" fill-opacity="1.0" />
                </Rule>
            """ % tdict 

            xml = xml_template % {'shppath': os.path.abspath(fullres_shp), 'extra_rules': extra_rules} 
            with open(os.path.join(settings.TILE_CONFIG_DIR, fieldname + '.xml'), 'w') as fh:
                print "  writing %s.xml" % fieldname
                fh.write(xml)

                # add layers (provider = mapnik) for each of the above
                lyrcfg = {
                    "provider": { "name": "mapnik", "mapfile": fieldname + ".xml" },
                    "metatile": { "rows": 4, "columns": 4, "buffer": 64 }
                }
                cfg["layers"][fieldname] = lyrcfg

        with open(os.path.join(settings.TILE_CONFIG_DIR, 'tiles.cfg'), 'w') as fh:
            print "  writing tiles.cfg"
            fh.write(json.dumps(cfg))

        print 
        print "Populating theme and layers for the layer manager"
        Layer.objects.filter(url__startswith="/tiles/").delete()
        call_command('loaddata','project_base_layers')

        for cf in cfs_with_fields:
            url = "/tiles/%s/${z}/${x}/${y}.png" % cf.dbf_fieldname
            legend = "/media/legends/relative_value.png"
            print " ",url
            theme_name = cf.level1
            theme, created = Theme.objects.get_or_create(name="auto_%s" % theme_name, display_name=theme_name)
            desc = cf.desc
            lyr = Layer.objects.create(name=cf.name, layer_type="XYZ", url=url, 
                    opacity=1.0, description=desc, legend=legend, legend_title=cf.name)
            lyr.themes.add(theme)
            lyr.save()

        theme_name = "Costs"
        theme, created = Theme.objects.get_or_create(name="auto_%s" % theme_name, display_name=theme_name)
        for c in cs: 
            url = "/tiles/%s/${z}/${x}/${y}.png" % c.dbf_fieldname
            legend = "/media/legends/relative_value.png"
            print " ",url
            desc = c.desc
            lyr = Layer.objects.create(name=c.name, layer_type="XYZ", url=url, 
                    opacity=1.0, description=desc, legend=legend, legend_title=c.name)
            lyr.themes.add(theme)
            lyr.save()

        # planning unit boundaries
        url = "/tiles/planning_units/${z}/${x}/${y}.png"
        legend = "/media/legends/planning_units.png"
        name = "Planning Units"
        try:
            lyr = Layer.objects.get(name=name)
            lyr.delete()
        except Layer.DoesNotExist:
            pass
        print " ",url
        theme_name = "Base"
        try:
            theme = Theme.objects.get(display_name=theme_name)
        except Theme.DoesNotExist:
            theme = Theme.objects.create(name="auto_%s" % theme_name, display_name=theme_name)
        desc = "Planning unit boundaries"
        lyr = Layer.objects.create(name=name, layer_type="XYZ", url=url, default_on=True,
                opacity=1.0, description=desc, legend=legend, legend_title=name)
        lyr.themes.add(theme)
        lyr.save()

        print 
        print "Loading costs, conservation features and auxillary data associated with each planning unit"
        for feature in layer:
            pu = pus.get(fid=feature.get(mapping['fid']))

            for aux in auxs:
                amt = feature.get(aux.dbf_fieldname)
                if amt == NULL_VALUE:
                    amt = None
                obj = PuVsAux(pu=pu, aux=aux, value=amt)
                obj.save()

            for cf in cfs_with_fields:
                amt = feature.get(cf.dbf_fieldname)
                if amt == NULL_VALUE:
                    amt = None
                elif amt < 0:
                    print "WARNING:", cf.dbf_fieldname, "has negative values"
                    amt = 0  # no non-null negatives
                obj = PuVsCf(pu=pu, cf=cf, amount=amt)
                obj.save()

            for c in cs: 
                amt = feature.get(c.dbf_fieldname)
                if amt == NULL_VALUE:
                    amt = None
                elif amt < 0:
                    print "WARNING:", c.dbf_fieldname, "has negative values"
                    amt = 0  # no non-null negatives
                obj = PuVsCost(pu=pu, cost=c, amount=amt)
                obj.save()

        assert len(PuVsCf.objects.all()) == len(pus) * len(cfs_with_fields)
        assert len(PuVsCost.objects.all()) == len(pus) * len(cs)
        assert len(PuVsAux.objects.all()) == len(pus) * len(auxs)

        # Load Geographies from xls
        print
        print "Loading Defined Geographies"
        sheet = book.sheet_by_name("Geographies")
        headers = sheet.row_values(0) #returns all the CELLS of row 0,
        fieldnames = ['geography', 'dbf_fieldname']

        assert len(headers) == len(fieldnames)
        for h in range(len(headers)): 
            if headers[h] != fieldnames[h]:
                print "WARNING: field %s is '%s' in the xls file but model is expecting '%s' ... OK?" % (h,
                        headers[h], fieldnames[h])

        for i in xrange(1, sheet.nrows):
            vals = sheet.row_values(i)
            print vals
            params = dict(zip(fieldnames, vals))
            dg = DefinedGeography(name=params['geography'])
            dg.save()

            fids = []
            for feature in layer:
                if feature.get(params['dbf_fieldname']) != NULL_VALUE:
                    fids.append(feature.get(FID_FIELD))

            pus = PlanningUnit.objects.filter(fid__in=fids)

            """
            # old method, assumed geography field was either cost or consfeat
            pus = [x.pu for x in PuVsCf.objects.filter(amount__isnull=False, 
                    cf__dbf_fieldname=params['dbf_fieldname'])]
            if len(pus) == 0:
                pus = [x.pu for x in PuVsCost.objects.filter(amount__isnull=False, 
                        cost__dbf_fieldname=params['dbf_fieldname'])]
                if len(pus) == 0:
                    raise Exception(params['geography'] + " has no planning units; check field named " + params['dbf_fieldname'])
            """
            for pu in pus:
                dg.planning_units.add(pu)
            dg.save()

        dgs = DefinedGeography.objects.all()
        assert len(dgs) == sheet.nrows - 1

        # Export the puvscf table to csv directly 
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
        
   
