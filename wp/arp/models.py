import os
import glob
from django import forms
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry 
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.utils.html import escape
from lingcod.features.models import PointFeature, LineFeature, PolygonFeature, FeatureCollection
from lingcod.features import register, alternate
from lingcod.layers.models import PrivateLayerList
from lingcod.unit_converter.models import area_in_display_units
from lingcod.analysistools.models import Analysis
from lingcod.analysistools.widgets import SliderWidget
from lingcod.common.utils import get_class
from lingcod.features import register
from lingcod.common.utils import asKml
from lingcod.async.ProcessHandler import *
from lingcod.common.utils import get_logger
from arp.tasks import marxan_start
from arp.marxan import MarxanError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json

logger = get_logger()


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""
    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value == "":
            return None
        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value, *args, **kwargs):
        """Convert our JSON object to a string before we save"""
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        return super(JSONField, self).get_db_prep_save(value, *args, **kwargs)

class ConservationFeature(models.Model):
    sci_name = models.CharField(max_length=99)
    common_name = models.CharField(max_length=99)
    name = models.CharField(max_length=99)
    level1 = models.CharField(max_length=99)
    level2 = models.CharField(max_length=99,null=True,blank=True)
    level3 = models.CharField(max_length=99,null=True,blank=True)
    level4 = models.CharField(max_length=99,null=True,blank=True)
    level5 = models.CharField(max_length=99,null=True,blank=True)
    esu_dps = models.CharField(max_length=99, null=True, blank=True)
    dbf_fieldname = models.CharField(max_length=15,null=True,blank=True)
    units = models.CharField(max_length=16, null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

class Cost(models.Model):
    name = models.CharField(max_length=99)
    dbf_fieldname = models.CharField(max_length=15,null=True,blank=True)
    units = models.CharField(max_length=16, null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

class PlanningUnit(models.Model):
    fid = models.IntegerField()
    area = models.FloatField()
    name = models.CharField(max_length=99)
    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
            null=True, blank=True, verbose_name="Planning Unit Geometry")
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

class PuVsCf(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    cf = models.ForeignKey(ConservationFeature)
    amount = models.FloatField()
    class Meta:
        unique_together = ("pu", "cf")

class PuVsCost(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    cost = models.ForeignKey(Cost)
    amount = models.FloatField()
    class Meta:
        unique_together = ("pu", "cost")

@register
class WatershedPrioritization(Analysis):
    input_target = JSONField(verbose_name='Target Percentage of Habitat')
    input_penalty = JSONField(verbose_name='Penalties for Missing Targets') 
    input_relativecost = JSONField(verbose_name='Relative Costs')

    # All output fields should be allowed to be Null/Blank
    output_calculated_target = JSONField(null=True, blank=True)
    output_best = JSONField(null=True, blank=True, verbose_name="Watersheds in Optimal Reserve")
    output_unit_counts = JSONField(null=True, blank=True)
    output_geometry = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
            null=True, blank=True, verbose_name="Watersheds")

    @property
    def outdir(self):
        return os.path.realpath(os.path.join(settings.MARXAN_OUTDIR, "%s_" % (self.uid,) ))
        # slugify(self.date_modified))
        # TODO this is not asycn-safe!!!

    def run(self):
        from arp.marxan import MarxanAnalysis
        from django.db.models import Sum
         
        # create the target and penalties
        print "Create targets and penalties"
        cfs = []
        for cf in ConservationFeature.objects.annotate(Sum('puvscf__amount')):
            try:
                total = float(cf.puvscf__amount__sum)
            except TypeError: 
                total = 0.0
            target = total * 0.5 # TODO get actual target pcts!!!
            penalty = 50.0 # TODO get actual penalties!!!
            if target > 0:
                cfs.append((cf.pk, target, penalty, cf.name))

        # Calc costs for each planning unit
        # TODO incorporate weightings instead of just a sum
        print "Calculate costs for each planning unit"
        pucosts = [(pu.pk, pu.puvscost__amount__sum) for pu in PlanningUnit.objects.annotate(Sum('puvscost__amount'))]

        # Pull the puvscf table
        #print "Pull data from the puvscf table"
        # This takes and insanely long time and is not stable
        # resort to a horrible hack of exporting the data directly to csv via SQL query
        #puvscf = [(r.cf.pk, r.pu.pk, r.amount) for r in PuVsCf.objects.all().order_by('pu__pk')]

        print "Creating the MarxanAnalysis object"
        m = MarxanAnalysis(pucosts, cfs, self.outdir)

        print "Firing off the asycn process"
        check_status_or_begin(marxan_start, task_args=(m,), polling_url=self.get_absolute_url())
        self.process_results()
        return True

    @property
    def progress(self):
        path = os.path.join(self.outdir,"output","wp_r*.csv")
        outputs = glob.glob(path)
        if len(outputs) == settings.MARXAN_NUMREPS:
            if not self.done:
                return (0,settings.MARXAN_NUMREPS)
        return (len(outputs), settings.MARXAN_NUMREPS)

    @property
    def marxan(self):
        """
        Called by process_results which will cache the dict
        May want to "cache" them by saving them to output_ fields of the feature instead?
        """
        use_cache = settings.USE_CACHE
        key = "wp_marxan_%s_%s" % (self.pk, slugify(self.date_modified))
        if use_cache:
            logger.info("Hit the cache for %s" % key)
            cached_result = cache.get(key)
            if cached_result: 
                return cached_result

        log = open(os.path.join(self.outdir,"output","wp_log.dat"),'r').read()

        wids = [int(x.strip()) for x  in self.output_units.split(',')]
        wshds = Watershed.objects.filter(huc12__in=wids)
        num_units = len(wshds)
        sum_area = 0
        for w in wshds:
            sum_area += w.area

        species = self.species
        time = open(os.path.join(self.outdir,"output","wp_log.dat"),'r').readlines()[-3]
        time = time.replace("Time passed so far is ","")
        best = [x.split(',') for x in open(os.path.join(self.outdir,"output","wp_mvbest.csv"),'r').readlines()][1:]
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
            cf = [s for s in species if s.id == int(b[0])][0] 
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

        if use_cache:
            cache.set(key, r)
        return r

    @property
    def status_html(self):
        code, status_html = self.status
        return status_html

    @property
    def status_code(self):
        code, status_html = self.status
        return code
    
    @property
    def status(self):
        url = self.get_absolute_url()
        if process_is_running(url):
            status = """Analysis for <em>%s</em> is currently running.</p>
            <p>%s of %s model runs completed.""" % (self.name,
                     self.progress[0], self.progress[1])
            code = 2
        elif process_is_complete(url):
            status = "%s processing is done. Refresh to see results." % self.name
            code = 3
        elif process_is_pending(url):
            status = "%s is in the queue but not yet running." % self.name
            res = get_process_result(url)
            code = 1
            if res is not None:
                status += "... "
                status += str(res)
        else:
            status = "An error occured while running this analysis..."
            code = 0
            res = get_process_result(url)
            status += str(res)

        return (code, "<p>%s</p>" % status)

    def process_results(self):
        if process_is_complete(self.get_absolute_url()):
            chosen = get_process_result(self.get_absolute_url())
            wshds = PlanningUnits.filter(pk__in=chosen)
            self.output_units = json.dumps([str(x.pk) for x in wshds])
            self.output_geometry = wshds.collect()
            super(Analysis, self).save() # save without calling save()
            #first_run = self.marxan

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
        return """%s
          <Folder id='%s'>
            <name>%s</name>
            %s
          </Folder>""" % (self.kml_style, 
                          self.uid, 
                          escape(self.name), 
                          '\n'.join([x.kml for x in wshds]))

    @property 
    def kml_working(self):
        code = self.status_code
        if code == 3: txt = "completed"
        elif code == 2: txt = "in progress"
        elif code == 1: txt = "in queue"
        elif code == 0: txt = "error occured"
        else: txt = "status unknown"

        return """
        <Placemark id="%s">
            <visibility>0</visibility>
            <name>%s (%s)</name>
        </Placemark>
        """ % (self.uid, escape(self.name), txt)

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
        links = (
            alternate('Shapefile',
                'arp.views.watershed_shapefile',
                select='single',
                type='application/zip',
            ),
        )

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
        show_template = 'folder/show.html'

    @classmethod
    def css(klass):
        return """li.%(uid)s > .icon { 
        background: url('%(media)skmltree/dist/images/sprites/kml.png?1302821411') no-repeat -231px 0px ! important;
        } """ % { 'uid': klass.model_uid(), 'media': settings.MEDIA_URL }
