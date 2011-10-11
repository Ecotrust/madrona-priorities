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

    @ property
    def level_string(self):
        levels = [self.level1, self.level2, self.level3, self.level4, self.level5]
        return '---'.join([slugify(x.lower()) for x in levels])

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
    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, 
            null=True, blank=True, verbose_name="Planning Unit Geometry")
    objects = models.GeoManager()

    def __unicode__(self):
        return u'%s' % self.name

    def kml(self, prop=0.5):
        import random
        prop = random.random()
        scale = (2.0 * prop) + 0.2  # from 0.2 to 2.2
        return """
        <Style id="style_%s">
            <IconStyle>
                <color>ff00ffaa</color>
                <scale>%s</scale>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>
                </Icon>
            </IconStyle>
            <LabelStyle>
                <color>0000ffaa</color>
                <scale>0.1</scale>
            </LabelStyle>
        </Style>
        <Placemark id="huc_%s">
            <visibility>1</visibility>
            <name>%s</name>
            <styleUrl>style_%s</styleUrl>
            %s
        </Placemark>
        """ % (self.fid, scale, self.fid, self.name, self.fid, asKml(self.geometry.point_on_surface))

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
    input_targets = JSONField(verbose_name='Target Percentage of Habitat')
    input_penalties = JSONField(verbose_name='Penalties for Missing Targets') 
    input_relativecosts = JSONField(verbose_name='Relative Costs')

    # All output fields should be allowed to be Null/Blank
    #output_calculated_target = JSONField(null=True, blank=True)
    output_best = JSONField(null=True, blank=True, verbose_name="Watersheds in Optimal Reserve")
    output_pu_count = JSONField(null=True, blank=True)
    #output_geometry = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
    #        null=True, blank=True, verbose_name="Watersheds")

    @property
    def outdir(self):
        return os.path.realpath(os.path.join(settings.MARXAN_OUTDIR, "%s_" % (self.uid,) ))
        # TODO this is not asycn-safe!!!
        # slugify(self.date_modified))

    def process_dict(self, d):
        """
        Use the levels in the ConservationFeature table to determine the 
        per-species value based on the specified levels.
        Input:
         {
             'widespread---trout': 0.5,
             'widespread---lamprey': 0.4,
             'widespread---salmon': 0.3,
             'widespread---steelhead': 0.2,
             'locally endemic': 0.1,
         }

        Return:
        species pk is the key
        { 1: 0.5, 2: 0.5, ......}
        """
        ndict = {}
        for s in ConservationFeature.objects.all():
            levels = s.level_string
            val = None
            for k,v in d.items():
                if levels.startswith(k.lower()):
                    val = v
                    break
            if val is None:
                raise Exception("Found no matching target for:  %s %s" % (s.name, s.level_string))
            ndict[s.pk] = val
        return ndict

    def run(self):
        from arp.marxan import MarxanAnalysis
        from django.db.models import Sum
         
        # create the target and penalties
        print "Create targets and penalties"
        targets = self.process_dict(self.input_targets)
        penalties = self.process_dict(self.input_penalties)
        cost_weights = self.input_relativecosts 

        assert len(targets.keys()) == len(penalties.keys()) == len(ConservationFeature.objects.all())
        assert max(targets.values()) < 1.0
        assert min(targets.values()) >=  0.0

        # Apply the target and penalties
        print "Apply the targets and penalties"
        cfs = []
        for cf in ConservationFeature.objects.annotate(Sum('puvscf__amount')):
            try:
                total = float(cf.puvscf__amount__sum)
            except TypeError: 
                total = 0.0
            target = total * targets[cf.pk]
            penalty = penalties[cf.pk]
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
    def results(self):
        return self.output_best

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
            wshds = PlanningUnit.objects.filter(pk__in=chosen)
            self.output_best = json.dumps({'best': [str(x.pk) for x in wshds]})
            ssoln = [x.strip().split(',') for x in 
                     open(os.path.join(self.outdir,"output","wp_ssoln.csv"),'r').readlines()][1:]
            selected = {}
            for s in ssoln:
                num = int(s[1])
                if num > 0:
                    selected[int(s[0])] = num
            print selected
            self.output_pu_count = json.dumps(selected) 
            #self.output_geometry = [x.geometry.centroid for x in wshds]
            super(Analysis, self).save() # save without calling save()
            #first_run = self.marxan

    @property
    def done(self):
        """ Boolean; is process complete? """
        done = True
        if self.output_best is None: done = False
        if self.output_pu_count is None: done = False

        if not done:
            done = True
            # only process async results if output fields are blank
            # this means we have to recheck after running
            self.process_results()
            if self.output_best is None: done = False
            if self.output_pu_count is None: done = False
        return done

    @classmethod
    def mapnik_geomfield(self):
        return "output_geometry"

    @property 
    def kml_done(self):
        wids = [int(x.strip()) for x in self.output_best['best']]
        wshds = PlanningUnit.objects.filter(pk__in=wids)
        kml = '' #TODO get ssoln
        return """%s
          <Folder id='%s'>
            <name>%s</name>
            %s
          </Folder>""" % (self.kml_style, 
                          self.uid, 
                          escape(self.name), 
                          '\n'.join([x.kml(1) for x in wshds]))

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
