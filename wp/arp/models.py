import os
import glob
import random
import shutil
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
from lingcod.common.models import KmlCache

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
        # Actually we'll just return the string
        # need to explicitly call json.loads(X) in your code
        # reason: converting to dict then repr that dict in a form is invalid json
        # i.e. {"test": 0.5} becomes {u'test': 0.5} (not unicode and single quotes)
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
    units = models.CharField(max_length=90, null=True, blank=True)

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
    input_scalefactor = models.FloatField()
    description = models.TextField(default="", null=True, blank=True, verbose_name="Description/Notes")

    # All output fields should be allowed to be Null/Blank
    output_best = JSONField(null=True, blank=True, verbose_name="Watersheds in Optimal Reserve")
    output_pu_count = JSONField(null=True, blank=True)

    @property
    def outdir(self):
        return os.path.realpath(os.path.join(settings.MARXAN_OUTDIR, "%s_" % (self.uid,) ))
        # TODO this is not asycn-safe!!!
        # slugify(self.date_modified))

    def copy(self, user):
        """ Override the copy method to make sure the marxan files get copied """
        orig = self.outdir
        copy = super(WatershedPrioritization, self).copy(user)
        shutil.copytree(orig, copy.outdir, symlinks=True)
        copy.save(rerun=False)
        return copy

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
        logger.debug("Create targets and penalties")
        targets = self.process_dict(json.loads(self.input_targets))
        penalties = self.process_dict(json.loads(self.input_penalties))
        cost_weights = json.loads(self.input_relativecosts)

        assert len(targets.keys()) == len(penalties.keys()) == len(ConservationFeature.objects.all())
        assert max(targets.values()) <= 1.0
        assert min(targets.values()) >=  0.0

        # Apply the target and penalties
        logger.debug("Apply the targets and penalties")
        cfs = []
        sum_penalties = 0
        for cf in ConservationFeature.objects.annotate(Sum('puvscf__amount')):
            try:
                total = float(cf.puvscf__amount__sum)
            except TypeError: 
                total = 0.0
            target = total * targets[cf.pk]
            penalty = penalties[cf.pk] * self.input_scalefactor
            if target > 0:
                sum_penalties += penalty
            # MUST include all species even if they are zero
            cfs.append((cf.pk, target, penalty, cf.name))

        # conditional .. turn invasives on/off depending
        final_cost_weights = {}
        for cost in Cost.objects.all():
            costkey = slugify(cost.name.lower())
            try:
                final_cost_weights[costkey] = cost_weights[costkey]
            except KeyError:
                final_cost_weights[costkey] = 0
                if costkey == 'watershed-condition-no-ais' and cost_weights['watershed-condition'] > 0: 
                    # Use the `no AIS` version if
                    #   - watershed-condition is checked
                    #   - invasives is checked
                    if cost_weights['invasives'] > 0: 
                        final_cost_weights[costkey] = 1
                elif costkey == 'watershed-condition-with-ais' and cost_weights['watershed-condition'] > 0: 
                    # Use the `AIS` version if
                    #   - watershed-condition is checked
                    #   - invasives is NOT checked
                    if cost_weights['invasives'] == 0: 
                        final_cost_weights[costkey] = 1
        if cost_weights['invasives'] > 0:
            assert final_cost_weights['watershed-condition-with-ais'] != final_cost_weights['watershed-condition-no-ais']

        # Calc costs for each planning unit
        pucosts = []
        sum_costs = 0
        # First loop, calc sum of costs 
        for pu in PlanningUnit.objects.all():
            puc = PuVsCost.objects.filter(pu=pu)
            weighted_cost = 0.0
            for c in puc:
                costkey = slugify(c.cost.name.lower())
                weighted_cost += final_cost_weights[costkey] * c.amount
                # TODO CONSTANT ALERT
                # Add 100 constant to each cost
                # Effectively scales each cost from 100 to 200
                # Assuming original costs are scaled 0 to 100
                weighted_cost += final_cost_weights[costkey] * 100
            sum_costs += weighted_cost
            pucosts.append( (pu.pk, weighted_cost) )


        # Apply ratio to costs to 'pre-scale' the total costs to equal the total penalties
        ##### Marxan has it's own cost scaling strategy so this won't work!
        ##### SEE APPENDIX B-1.3 for 
        #penalty_cost_ratio = float(sum_penalties) / float(sum_costs)
        #new_pucosts = []
        #for pucost in pucosts:
        #    new_pucost = (pucost[0], pucost[1] * penalty_cost_ratio )# self.input_scalefactor)
        #    new_pucosts.append(new_pucost)
        #pucosts = new_pucosts

        # Pull the puvscf table
        # This takes and insanely long time and is not stable
        # resort to a horrible hack of exporting the data directly to csv via SQL query
        #puvscf = [(r.cf.pk, r.pu.pk, r.amount) for r in PuVsCf.objects.all().order_by('pu__pk')]

        logger.debug("Creating the MarxanAnalysis object")
        m = MarxanAnalysis(pucosts, cfs, self.outdir)

        logger.debug("Firing off the asycn process")
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
        targets = json.loads(self.input_targets)
        penalties = json.loads(self.input_penalties)
        cost_weights = json.loads(self.input_relativecosts)
        targets_penalties = {}
        for k, v in targets.items():
            targets_penalties[k] = {'target': v, 'penalty': None}
        for k, v in penalties.items():
            try:
                targets_penalties[k]['penalty'] = v
            except KeyError:
                # this should never happen but just in case
                targets_penalties[k] = {'target': None, 'penalty': v}

        if not self.done:
            return {'targets_penalties': targets_penalties, 'costs': cost_weights}

        bestjson = json.loads(self.output_best)
        bestpks = [int(x) for x in bestjson['best']]
        bestpus = PlanningUnit.objects.filter(pk__in=bestpks)
        best = []
        for pu in bestpus:
            bcosts = {}
            for x in PuVsCost.objects.filter(pu=pu):
                bcosts[x.cost.name.lower().replace(" ","")] = x.amount
            best.append( {'name': pu.name, 'costs': bcosts})

        sum_area = sum([x.area for x in bestpus])

        # Parse mvbest
        fh = open(os.path.join(self.outdir,"output","wp_mvbest.csv"), 'r')
        lines = [x.strip().split(',') for x in fh.readlines()[1:]]
        fh.close()
        species = []
        num_met = 0
        for line in lines:
            sid = int(line[0])
            consfeat = ConservationFeature.objects.get(pk=sid)
            sname = consfeat.name
            sunits = consfeat.units
            slevel1 = consfeat.level1
            scode = consfeat.dbf_fieldname
            starget = float(line[2])
            sheld = float(line[3])
            smpm = float(line[9])
            if starget == 0:
                smpm = 0.0
            smet = False
            if line[8] == 'yes' or smpm > 1.0:
                smet = True
                num_met += 1
            s = {'name': sname, 'id': sid, 'target': starget, 'units': sunits, 'code': scode, 
                 'held': sheld, 'met': smet, 'pct_target': smpm, 'level1': slevel1 }
            species.append(s)      

        species.sort(key=lambda k:k['name'].lower())

        res = {
            'costs': cost_weights,
            'targets_penalties': targets_penalties,
            'area': sum_area, 
            'num_units': len(best),
            'num_met': num_met,
            'num_species': len(species),
            'units': best,
            'species': species, 
        }
        return res
        
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
            self.output_pu_count = json.dumps(selected) 
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
        key = "watershed_kmldone_%s_%s" % (self.uid, slugify(self.date_modified))
        kmlcache, created = KmlCache.objects.get_or_create(key=key)
        kml = kmlcache.kml_text
        if not created and kml:
            logger.warn("%s ... kml cache found" % key)
            return kml
        logger.warn("%s ... NO kml cache found ... seeding" % key)

        ob = json.loads(self.output_best)
        wids = [int(x.strip()) for x in ob['best']]
        puc = json.loads(self.output_pu_count)
        # WARNING this only shows them if they were in the 'best' run!
        # wshds = PlanningUnit.objects.filter(pk__in=wids)
        # instead, do all
        wshds = PlanningUnit.objects.all()

        kmls = []
        color = 'aa0000ff'
        #color = "cc%02X%02X%02X" % (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        for ws in wshds:
            try:
                hits = puc[str(ws.pk)] 
            except:
                hits = 0
            numruns = settings.MARXAN_NUMREPS
            prop = float(hits)/numruns
            scale = (1.4 * prop * prop) 
            if scale > 0 and scale < 0.5: 
                scale = 0.5
            if prop > 0:
                kmls.append( """
            <Style id="style_%s">
                <IconStyle>
                    <color>%s</color>
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
                <description>Included in %s out of %s runs.</description>
                <styleUrl>style_%s</styleUrl>
                %s
            </Placemark>
            """ % (ws.fid, color, scale, ws.fid, ws.name, hits, numruns, ws.fid, asKml(ws.geometry.point_on_surface)))


        fullkml = """%s
          <Folder id='%s'>
            <name>%s</name>
            %s
          </Folder>""" % (self.kml_style, 
                          self.uid, 
                          escape(self.name), 
                          '\n'.join(kmls))

        kmlcache.kml_text = fullkml
        kmlcache.save()
        return fullkml
       

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
                select='single multiple',
                type='application/zip',
            ),
            alternate('Input Files',
                'arp.views.watershed_marxan',
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
                'arp.models.Folder',
                'arp.models.WatershedPrioritization',
                )
        form = 'arp.forms.FolderForm'
        show_template = 'folder/show.html'

    @classmethod
    def css(klass):
        return """li.%(uid)s > .icon { 
        background: url('%(media)skmltree/dist/images/sprites/kml.png?1302821411') no-repeat -231px 0px ! important;
        } """ % { 'uid': klass.model_uid(), 'media': settings.MEDIA_URL }

class PlanningUnitShapes(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    stamp = models.FloatField()
    bests = models.IntegerField(default=0) 
    hits = models.IntegerField(default=0) 
    fid = models.IntegerField(null=True)
    name = models.CharField(max_length=99, null=True)
    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, 
    #geometry = models.PointField(srid=settings.GEOMETRY_DB_SRID, 
            null=True, blank=True, verbose_name="Planning Unit Geometry")
