from django.conf import settings
from django.contrib.gis.db import models
from lingcod.features.models import PointFeature, LineFeature, PolygonFeature, FeatureCollection
from lingcod.features import register, alternate
from lingcod.layers.models import PrivateLayerList
from lingcod.unit_converter.models import area_in_display_units
from lingcod.analysistools.models import Analysis
from lingcod.analysistools.widgets import SliderWidget
from lingcod.common.utils import get_class
from lingcod.features import register
from django.contrib.gis.geos import GEOSGeometry 
from lingcod.common.utils import asKml
from django import forms
from arp.tasks import marxan_start
from lingcod.async.ProcessHandler import *
import os
import glob

@register
class AOI(PolygonFeature):
    description = models.TextField(default="", null=True, blank=True)

    class Options:
        manipulators = []
        verbose_name = 'Area of Interest'
        show_template = 'foi/show.html'
        form = 'arp.forms.AOIForm'
        icon_url = 'common/images/aoi.png'

@register
class LOI(LineFeature):
    description = models.TextField(default="", null=True, blank=True)

    class Options:
        manipulators = []
        verbose_name = 'Linear Feature'
        show_template = 'foi/show.html'
        form = 'arp.forms.LOIForm'
        icon_url = 'common/images/loi.png'

@register
class POI(PointFeature):
    description = models.TextField(default="", null=True, blank=True)

    class Options:
        manipulators = []
        verbose_name = 'Point of Interest'
        show_template = 'foi/show.html'
        form = 'arp.forms.POIForm'
        icon_url = 'common/images/poi.png'

@register
class Folder(FeatureCollection):
    description = models.TextField(default="", null=True, blank=True)
        
    class Options:
        verbose_name = 'Folder'
        valid_children = ( 
                'arp.models.AOI', 
                'arp.models.LOI', 
                'arp.models.POI', 
                'arp.models.Folder',
                'arp.models.UserKml',
                'arp.models.BufferPoint',
                'arp.models.WatershedPrioritization',
                )
        form = 'arp.forms.FolderForm'
        show_template = 'array/show.html'

    @classmethod
    def css(klass):
        return """ li.KmlDocument > .icon { 
        background: url('%(media)skmltree/dist/images/sprites/kml.png?1302821411') no-repeat -566px 0px ! important;
        }
        li.%(uid)s > .icon { 
        background: url('%(media)skmltree/dist/images/sprites/kml.png?1302821411') no-repeat -231px 0px ! important;
        } """ % { 'uid': klass.model_uid(), 'media': settings.MEDIA_URL }
    
@register
class UserKml(PrivateLayerList):
    class Options:
        verbose_name = "Uploaded KML"
        form = 'arp.forms.UserKmlForm'
        export_png = False
        show_template = 'layers/privatekml_show.html'

class Watershed(models.Model):
    fid = models.IntegerField()
    huc12 = models.BigIntegerField()
    coho = models.FloatField()
    chinook = models.FloatField()
    steelhead = models.FloatField()
    climate_cost = models.FloatField()
    area = models.FloatField()
    name = models.CharField(max_length=99)
    geometry = models.PolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
            null=True, blank=True, verbose_name="Watersheds")
    objects = models.GeoManager()

    def __unicode__(self):
        return u'%s' % self.name

    @property
    def kml(self):
        return """
        <Placemark id="huc_%s">
            <visibility>1</visibility>
            <name>%s</name>
            <styleUrl>#selected-watersheds</styleUrl>
            %s
        </Placemark>
        """ % (self.huc12, self.name, asKml(self.geometry))

@register
class WatershedPrioritization(Analysis):
    input_target_coho = models.FloatField(verbose_name='Target Percentage of Coho Habitat')
    input_target_chinook = models.FloatField(verbose_name='Target Percentage of Chinook Habitat') 
    input_target_steelhead = models.FloatField(verbose_name='Target Percentage of Steelhead Habitat')
    input_penalty_coho = models.FloatField(verbose_name='Penalty for missing Coho target', default=0.5)
    input_penalty_chinook = models.FloatField(verbose_name='Penalty for missing Chinook target') 
    input_penalty_steelhead = models.FloatField(verbose_name='Penalty for missing Steelhead target')
    input_cost_climate = models.FloatField(verbose_name='Relative cost of Climate Change')

    # All output fields should be allowed to be Null/Blank
    output_units = models.TextField(null=True, blank=True,
            verbose_name="Watersheds in Optimal Reserve")
    output_geometry = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
            null=True, blank=True, verbose_name="Watersheds")

    @property
    def species(self):
        from arp.marxan import ConservationFeature 
        species = []
        ws = Watershed.objects.all()
        for s in ['coho','chinook','steelhead']:
            from django.db.models import Sum
            agg = ws.aggregate(Sum(s))
            total = agg[s + "__sum"]
            pct = self.__dict__['input_target_' + s]
            target = total * pct
            penalty = self.__dict__['input_penalty_' + s] * 100

            species.append( 
                ConservationFeature(len(species)+1,s, penalty, target, pct, total) 
            )

        return species

    @property
    def outdir(self):
        return os.path.realpath("/tmp/test/%s" % self.uid)

    
    def run(self):
        from arp.marxan import MarxanAnalysis

        units = Watershed.objects.all()
        m = MarxanAnalysis(self, units, self.outdir)

        check_status_or_begin(marxan_start, task_args=(m,), polling_url=self.get_absolute_url())
        self.process_results()
        return True

    @property
    def progress(self):
        path = os.path.join(self.outdir,"output","test_r*.dat")
        outputs = glob.glob(path)
        if len(outputs) == settings.MARXAN_NUMREPS:
            if not self.done:
                return (0,settings.MARXAN_NUMREPS)
        return (len(outputs), settings.MARXAN_NUMREPS)

    @property
    def marxan(self):
        """
        TODO Fix this crap ... it works as proof-of-concept but it's horribly sloppy
        Whoever wrote this should be punished and likely will be 
        if they try to maintain or debug this property

        Ideally this should all be handled in process_results(?)
        """
        from django.core.cache import cache
        use_cache = False
        key = "wp_marxan_%s_%s" % (self.pk, self.date_modified)
        try:
            cached_result = cache.get(key)
            if use_cache and cached_result: 
                return cached_result
        except:
            pass

        log = open(os.path.join(self.outdir,"output","test_log.dat"),'r').read()

        wids = [int(x.strip()) for x  in self.output_units.split(',')]
        wshds = Watershed.objects.filter(huc12__in=wids)
        num_units = len(wshds)
        sum_area = 0
        for w in wshds:
            sum_area += w.area

        species = self.species
        time = open(os.path.join(self.outdir,"output","test_log.dat"),'r').readlines()[-3]
        time = time.replace("Time passed so far is ","")
        best = [x.split('\t') for x in open(os.path.join(self.outdir,"output","test_mvbest.dat"),'r').readlines()][1:]
        out_species = []
        gchart_seqs = []
        gchart_labels = []

        max_habitat = 0
        for s in species:
            if s.total > max_habitat:
                max_habitat = s.total

        hit = 0
        miss = 0
        for b in best:
            cf = [s for s in species if s.name == b[1]][0] 
            cf.amount = float(b[3])
            cf.occurences = int(b[5])
            cf.miss = False
            if b[8].strip().lower() != 'yes':
                cf.miss = True
                miss += 1
            else:
                hit += 1
            out_species.append(cf)

            minpixel = int(max_habitat / 350.)*2

            if cf.miss:
                gchart_seqs.append((int(cf.amount), int(cf.target - cf.amount), minpixel, 0, int(cf.total - cf.target)) )
            else:
                gchart_seqs.append((int(cf.target), 0, minpixel, int(cf.amount - cf.target), int(cf.total - cf.amount)) )
            gchart_labels.append(cf.name)

        cs = []
        for c in zip(*gchart_seqs):
            cs.append(','.join([str(x) for x in c]))
        chd = '|'.join(cs)

        gchart_url = "https://chart.googleapis.com/chart?cht=bhs&chs=350x125&chd=t:%(chd)s&chco=2d69ff,dd6a6a,111111,4f89f9,c6d9fd&chbh=20&chds=0,%(max_habitat)s&chxt=x,y&chxl=1:|Coho|Chinook|Steelhead|0:|0|%(max_habitat)s" % {'chd': chd, 'max_habitat': int(max_habitat)}

        r = {'log': log,
            'watersheds': wshds,
            'num_units': num_units,
            'area': sum_area,
            'species': out_species, 
            'chart_url': gchart_url,
            'hit': hit,
            'num_species': hit+miss,
            'time': time,
            'runs': settings.MARXAN_NUMREPS
        }
        cache.set(key, r)
        return r

    @property
    def status_html(self):
        url = self.get_absolute_url()
        if process_is_running(url):
            status = """Analysis for <em>%s</em> is currently running.</p>
            <p>%s of %s model runs completed.""" % (self.name,
                     self.progress[0], self.progress[1])
        elif process_is_complete(url):
            status = "%s processing is done. Close this panel and hit 'Refresh' to see the results." % self.name
        elif process_is_pending(url):
            status = "%s is in the queue but not yet running" % self.name
        else:
            status = "something isn't right here..."

        return "<p>%s</p>" % status

    def process_results(self):
        if process_is_complete(self.get_absolute_url()):
            chosen = get_process_result(self.get_absolute_url())
            units = Watershed.objects.all()
            wshds = units.filter(pk__in=chosen)
            self.output_units = ','.join([str(x.huc12) for x in wshds])
            self.output_geometry = wshds.collect()
            super(Analysis, self).save() # save without calling save()

    @property
    def done(self):
        """ Boolean; is process complete? """
        done = True
        for of in self.outputs.keys():
            if not self.outputs[of]:
                done = False
        if not done:
            done = True
            # only process async results if output fields are blank
            # this means we have to recheck after running
            self.process_results()
            for of in self.outputs.keys():
                if not self.outputs[of]:
                    done = False
        return done

    @classmethod
    def mapnik_geomfield(self):
        return "output_geometry"

    @property 
    def kml_done(self):
        wids = [int(x.strip()) for x  in self.output_units.split(',')]
        wshds = Watershed.objects.filter(huc12__in=wids)
        return "%s\n\n<Folder id=\"%s\"><name>%s</name>%s</Folder>" % (self.kml_style, 
                self.uid, self.name, '\n'.join([x.kml for x in wshds]))

    @property 
    def kml_working(self):
        return """
        <Placemark id="%s">
            <visibility>0</visibility>
            <name>%s (WORKING)</name>
        </Placemark>
        """ % (self.uid, self.name)

    @property
    def kml_style(self):
        return """
        <Style id="selected-watersheds">
            <IconStyle>
                <color>ffffffff</color>
                <colorMode>normal</colorMode>
                <scale>0.9</scale> 
                <Icon> <href>http://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href> </Icon>
            </IconStyle>
            <LabelStyle>
                <color>ffffffff</color>
                <scale>0.8</scale>
            </LabelStyle>
            <PolyStyle>
                <color>7766ffff</color>
            </PolyStyle>
        </Style>
        """

    class Options:
        form = 'arp.forms.WatershedPrioritizationForm'
        verbose_name = 'Watershed Prioritization Analysis'
        show_template = 'wp/show.html'
        form_template = 'wp/form.html'
        icon_url = 'common/images/watershed.png'


@register
class BufferPoint(Analysis):
    input_lat = models.FloatField(verbose_name='Latitude')
    input_lon = models.FloatField(verbose_name='Longitude') 
    input_buffer_distance = models.FloatField(verbose_name="Buffer Distance (m)")

    # All output fields should be allowed to be Null/Blank
    output_area= models.FloatField(null=True,blank=True, 
            verbose_name="Buffer Area (meters)")
    output_point_geom = models.PointField(srid=settings.GEOMETRY_DB_SRID,
            null=True, blank=True, verbose_name="Point Geometry")
    output_poly_geom = models.PolygonField(srid=settings.GEOMETRY_DB_SRID,
            null=True, blank=True, verbose_name="Buffered Point Geometry")

    @classmethod
    def mapnik_geomfield(self):
        return "output_poly_geom"

    def run(self):
        try:
            g = GEOSGeometry('SRID=4326;POINT(%s %s)' % (self.input_lon, self.input_lat))
            g.transform(settings.GEOMETRY_DB_SRID)
            self.output_point_geom = g
            self.output_poly_geom = g.buffer(self.input_buffer_distance)
            self.output_area = self.output_poly_geom.area
        except:
            return False
        return True

    @property 
    def kml_done(self):
        return """
        %s

        <Placemark id="%s">
            <visibility>1</visibility>
            <name>%s</name>
            <styleUrl>#%s-default</styleUrl>
            <MultiGeometry>
            %s
            %s
            </MultiGeometry>
        </Placemark>
        """ % (self.kml_style, self.uid, self.name, self.model_uid(),
            asKml(self.output_point_geom.transform(
                    settings.GEOMETRY_CLIENT_SRID, clone=True)),
            asKml(self.output_poly_geom.transform(
                    settings.GEOMETRY_CLIENT_SRID, clone=True)))

    @property 
    def kml_working(self):
        return """
        <Placemark id="%s">
            <visibility>0</visibility>
            <name>%s (WORKING)</name>
            <styleUrl>#%s-default</styleUrl>
            <Point>
              <coordinates>%s,%s</coordinates>
            </Point>
        </Placemark>
        """ % (self.uid, self.name, self.model_uid(), 
                self.input_lon, self.input_lat)

    @property
    def kml_style(self):
        return """
        <Style id="%s-default">
            <IconStyle>
                <color>ffffffff</color>
                <colorMode>normal</colorMode>
                <scale>0.9</scale> 
                <Icon> <href>http://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href> </Icon>
            </IconStyle>
            <LabelStyle>
                <color>ffffffff</color>
                <scale>0.8</scale>
            </LabelStyle>
            <PolyStyle>
                <color>778B1A55</color>
            </PolyStyle>
        </Style>
        """ % (self.model_uid(),)

    class Options:
        verbose_name = "Buffer Point"
        form = 'arp.forms.BufferPointsForm'
        show_template = 'analysis/show.html'
        icon_url = 'analysistools/img/buffer-16x16.png'
