import os
import glob
import random
import shutil
import math
from django import forms
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry 
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.utils.html import escape
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from madrona.features.models import PointFeature, LineFeature, PolygonFeature, FeatureCollection
from madrona.features import register, alternate
from madrona.layers.models import PrivateLayerList
from madrona.unit_converter.models import area_in_display_units
from madrona.analysistools.models import Analysis
from madrona.analysistools.widgets import SliderWidget
from madrona.common.utils import get_class
from madrona.features import register
from madrona.common.utils import asKml
from madrona.async.ProcessHandler import *
from madrona.common.utils import get_logger
from seak.tasks import marxan_start
from seak.marxan import MarxanError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from madrona.common.models import KmlCache

logger = get_logger()

def cachemethod(cache_key, timeout=3600):
    '''
    http://djangosnippets.org/snippets/1130/    
    Cacheable class method decorator
    from madrona.common.utils import cachemethod

    @property
    @cachemethod("SomeClass_get_some_result_%(id)s")
    '''
    def paramed_decorator(func):
        def decorated(self):
            if not settings.USE_CACHE:
                res = func(self)
                return res

            key = cache_key % self.__dict__
            #logger.debug("\nCACHING %s" % key)
            res = cache.get(key)
            if res == None:
                #logger.debug("   Cache MISS")
                res = func(self)
                cache.set(key, res, timeout)
                #logger.debug("   Cache SET")
                if cache.get(key) != res:
                    logger.error("*** Cache GET was NOT successful, %s" % key)
            return res
        return decorated 
    return paramed_decorator


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

# http://south.readthedocs.org/en/latest/customfields.html#extending-introspection
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^seak\.models\.JSONField"])

class ConservationFeature(models.Model):
    name = models.CharField(max_length=99)
    level1 = models.CharField(max_length=99)
    level2 = models.CharField(max_length=99,null=True,blank=True)
    level3 = models.CharField(max_length=99,null=True,blank=True)
    level4 = models.CharField(max_length=99,null=True,blank=True)
    level5 = models.CharField(max_length=99,null=True,blank=True)
    dbf_fieldname = models.CharField(max_length=15,null=True,blank=True)
    units = models.CharField(max_length=90, null=True, blank=True)
    uid = models.IntegerField(primary_key=True)

    @property
    def level_string(self):
        """ All levels concatenated with --- delim """
        levels = [self.level1, self.level2, self.level3, self.level4, self.level5]
        return '---'.join([slugify(x.lower()) for x in levels])

    @property
    def id_string(self):
        """ Relevant levels concatenated with --- delim """
        levels = [self.level1, self.level2, self.level3, self.level4, self.level5]
        return '---'.join([slugify(x.lower()) for x in levels if x not in ['', None]])

    def __unicode__(self):
        return u'%s' % self.name

class Cost(models.Model):
    name = models.CharField(max_length=99)
    uid = models.IntegerField(primary_key=True)
    dbf_fieldname = models.CharField(max_length=15,null=True,blank=True)
    units = models.CharField(max_length=16, null=True, blank=True)
    desc = models.TextField()

    @property
    def slug(self):
        return slugify(self.name.lower())

    def __unicode__(self):
        return u'%s' % self.name

class PlanningUnit(models.Model):
    fid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=99)
    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, 
            null=True, blank=True, verbose_name="Planning Unit Geometry")
    objects = models.GeoManager()
    date_modified = models.DateTimeField(auto_now=True)

    @property
    @cachemethod("PlanningUnit_%(fid)s_area")
    def area(self):
        # assume storing meters and returning km^2 (TODO)
        area = self.geometry.area / float(1000*1000)
        return area

    @property
    @cachemethod("PlanningUnit_%(fid)s_centroid")
    def centroid(self):
        centroid = self.geometry.point_on_surface.coords
        return centroid

    def __unicode__(self):
        return u'%s' % self.name

    @property
    @cachemethod("PlanningUnit_%(fid)s_cffields")
    def conservation_feature_fields(self):
        cfs = PuVsCf.objects.filter(pu=self, amount__isnull=False).select_related()
        return [x.cf.dbf_fieldname for x in cfs]

    @property
    @cachemethod("PlanningUnit_%(fid)s_costfields")
    def cost_fields(self):
        cfs = PuVsCost.objects.filter(pu=self, amount__isnull=False).select_related()
        return [x.cost.dbf_fieldname for x in cfs]

class DefinedGeography(models.Model):
    name = models.CharField(max_length=99)
    planning_units = models.ManyToManyField(PlanningUnit)

    @property
    def planning_unit_fids(self):
        return json.dumps([x.fid for x in self.planning_units.all()])

    @property
    def slug(self):
        return slugify(self.name)

    def __unicode__(self):
        return self.name

class PuVsCf(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    cf = models.ForeignKey(ConservationFeature)
    amount = models.FloatField(null=True, blank=True)
    class Meta:
        unique_together = ("pu", "cf")

class PuVsCost(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    cost = models.ForeignKey(Cost)
    amount = models.FloatField(null=True, blank=True)
    class Meta:
        unique_together = ("pu", "cost")

def scale_list(vals, low, high):
    """
    Scales a list of floats linearly between low and high
    """
    if len(vals) < 1:
        return []
    minval = min(vals)
    maxval = max(vals)
    if maxval == minval: 
        return [0] * len(vals)
    scaled = [z / float(maxval - minval) for z in 
                [(high - low) * y for y in 
                    [x - minval for x in vals]]] 
    return scaled

@register
class Scenario(Analysis):
    input_targets = JSONField(verbose_name='Target Percentage of Habitat')
    input_penalties = JSONField(verbose_name='Penalties for Missing Targets') 
    input_relativecosts = JSONField(verbose_name='Relative Costs')
    input_geography = JSONField(verbose_name='Input Geography fids')
    input_scalefactor = models.FloatField(default=0.0) 
    description = models.TextField(default="", null=True, blank=True, verbose_name="Description/Notes")

    # All output fields should be allowed to be Null/Blank
    output_best = JSONField(null=True, blank=True, verbose_name="Watersheds in Optimal Reserve")
    output_pu_count = JSONField(null=True, blank=True)

    @property
    def outdir(self):
        return os.path.realpath(os.path.join(settings.MARXAN_OUTDIR, "%s_" % (self.uid,) ))
        # This is not asycn-safe! A new modificaiton will clobber the old. 
        # What happens if new and old are both still running - small chance of a corrupted mix of output files? 

    @property
    def expired(self):
        if self.date_modified < PlanningUnit.objects.latest('date_modified').date_modified:
            return True
        else:
            return False

    def copy(self, user):
        """ Override the copy method to make sure the marxan files get copied """
        orig = self.outdir
        copy = super(Scenario, self).copy(user)
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
        for cf in ConservationFeature.objects.all():
            # TODO don't assume fields are valid within the selected geography
            levels = cf.level_string
            val = 0
            for k,v in d.items():
                if levels.startswith(k.lower()):
                    val = v
                    break
            ndict[cf.pk] = val
        return ndict

    def invalidate_cache(self):
        keys = ["%s_results",]
        keys = [x % self.uid for x in keys]
        cache.delete_many(keys)
        for key in keys:
            assert cache.get(key) == None
        logger.debug("invalidated cache for %s" % str(keys))
        return True

    def run(self):
        from seak.marxan import MarxanAnalysis
        from django.db.models import Sum
         
        self.invalidate_cache()

        # create the target and penalties
        logger.debug("Create targets and penalties")
        targets = self.process_dict(json.loads(self.input_targets))
        penalties = self.process_dict(json.loads(self.input_penalties))
        cost_weights = json.loads(self.input_relativecosts)
        geography_fids = json.loads(self.input_geography)

        assert len(targets.keys()) == len(penalties.keys()) #== len(ConservationFeature.objects.all())
        assert max(targets.values()) <= 1.0
        assert min(targets.values()) >=  0.0

        nonzero_pks = [k for k,v in targets.items() if v > 0] 
        nonzero_targets = []
        nonzero_penalties = []
        for nz in nonzero_pks:
            nonzero_targets.append(targets[nz])
            nonzero_penalties.append(penalties[nz])
            
        maxtarget = max(nonzero_targets)
        try:
            meantarget = sum(nonzero_targets) / float(len(nonzero_targets))
        except ZeroDivisionError:
            meantarget = 0
        try:
            meanpenalty = sum(nonzero_penalties) / float(len(nonzero_penalties))
        except ZeroDivisionError:
            meanpenalty = 0
        numspecies = len(nonzero_targets)

        # ignore input, choose a scalefactor automatically
        self.input_scalefactor = maxtarget * 4 + 2  # effectively scales from 2.5 to 6.5, the sweet spot

        # Apply the target and penalties
        logger.debug("Apply the targets and penalties")
        cfs = []
        sum_penalties = 0
        pus = PlanningUnit.objects.filter(fid__in=geography_fids)
        for cf in ConservationFeature.objects.all():
            total = sum([x.amount for x in cf.puvscf_set.filter(pu__in=pus) if x.amount])
            target = total * targets[cf.pk]
            penalty = penalties[cf.pk] * self.input_scalefactor
            if target > 0:
                sum_penalties += penalty
            # MUST include all species even if they are zero
            cfs.append((cf.pk, target, penalty, cf.name))

        final_cost_weights = {}
        for cost in Cost.objects.all():
            costkey = cost.slug
            try:
                final_cost_weights[costkey] = cost_weights[costkey]
            except KeyError:
                final_cost_weights[costkey] = 0

        wcosts = []
        pus = []
        # First loop, calc the cumulative costs per planning unit
        for pu in PlanningUnit.objects.filter(fid__in=geography_fids):
            weighted_cost = 0.1  # TODO Constant: lowest possible cost
            puc = PuVsCost.objects.filter(pu=pu)
            for c in puc:
                costkey = c.cost.slug
                weighted_cost += final_cost_weights[costkey] * c.amount
            wcosts.append(weighted_cost)
            pus.append(pu.pk)

        # scale the costs 0 to 100
        sum_costs = sum(wcosts)
        scaled_costs = scale_list(wcosts, 0.0, 100.0)
        pucosts = zip(pus, scaled_costs)

        logger.debug("Creating the MarxanAnalysis object")
        m = MarxanAnalysis(pucosts, cfs, self.outdir)

        logger.debug("Firing off the process")
        check_status_or_begin(marxan_start, task_args=(m,), polling_url=self.get_absolute_url())
        self.process_results()
        return True

    @property
    def numreps(self):
        try:
            with open(os.path.join(self.outdir,"input.dat")) as fh:
                for line in fh.readlines():
                    if line.startswith('NUMREPS'):
                        return int(line.strip().replace("NUMREPS ",""))
        except IOError:
            # probably hasn't started processing yet
            return settings.MARXAN_NUMREPS

    @property
    def progress(self):
        path = os.path.join(self.outdir,"output","nplcc_r*.csv")
        outputs = glob.glob(path)
        numreps = self.numreps
        if len(outputs) == numreps:
            if not self.done:
                return (0, numreps)
        return (len(outputs), numreps)

    def geojson(self, srid):
        # Note: no reprojection support here 
        rs = self.results
        if 'units' in rs:
            selected_fids = [r['fid'] for r in rs['units']]
        else:
            selected_fids = []
        
        try:
            bbox = rs['bbox']
        except:
            bbox = None
   
        fullname = self.user.get_full_name()
        if fullname == '':
            fullname = self.user.username

        error = False
        if self.status_code == 0:
            error = True

        serializable = {
            "type": "Feature",
            "bbox": bbox,
            "geometry": None,
            "properties": {
               'uid': self.uid, 
               'bbox': bbox,
               'name': self.name, 
               'done': self.done, 
               'error': error,
               'sharing_groups': [x.name for x in self.sharing_groups.all()],
               'expired': self.expired,
               'description': self.description,
               'date_modified': self.date_modified.strftime("%m/%d/%y %I:%M%P"),
               'user': self.user.username,
               'user_fullname': fullname,
               'selected_fids': selected_fids,
               'potential_fids': json.loads(self.input_geography)
            }
        }
        return json.dumps(serializable)

    @property
    @cachemethod("seak_scenario_%(id)s_results")
    def results(self):
        targets = json.loads(self.input_targets)
        penalties = json.loads(self.input_penalties)
        cost_weights = json.loads(self.input_relativecosts)
        geography = json.loads(self.input_geography)
        targets_penalties = {}
        for k, v in targets.items():
            targets_penalties[k] = {'label': k.replace('---', ' > ').title(), 'target': v, 'penalty': None}
        for k, v in penalties.items():
            try:
                targets_penalties[k]['penalty'] = v
            except KeyError:
                # this should never happen but just in case
                targets_penalties[k] = {'label': k.replace('---', ' > ').title(), 'target': None, 'penalty': v}

        species_level_targets = self.process_dict(targets)
        if not self.done:
            return {'targets_penalties': targets_penalties, 'costs': cost_weights}

        bestjson = json.loads(self.output_best)
        bestpks = [int(x) for x in bestjson['best']]
        bestpus = PlanningUnit.objects.filter(pk__in=bestpks).order_by('name')
        potentialpus = PlanningUnit.objects.filter(fid__in=geography)
        bbox = None
        if bestpus:
            bbox = potentialpus.extent()
        best = []
        logger.debug("looping through bestpus queryset")
        
        scaled_costs = {}
        all_costs = Cost.objects.all()
        for costslug, weight in cost_weights.iteritems():
            if weight <= 0:
                continue
            try:
                cost = [x for x in all_costs if x.slug == costslug][0] 
            except IndexError:
                continue
            all = PuVsCost.objects.filter(cost=cost, pu__in=bestpus)
            vals = [x.amount for x in all]
            fids = [x.pu.fid for x in all]
            scaled_values = [int(x) for x in scale_list(vals, 0.0, 100.0)]
            pucosts = dict(zip(fids, scaled_values))
            scaled_costs[costslug] = pucosts

        for pu in bestpus:
            centroid = pu.centroid 
            costs = {}
            for cname, pucosts in scaled_costs.iteritems():
                costs[cname] = pucosts[pu.fid]

            best.append({'name': pu.name, 
                         'fid': pu.fid, 
                         'costs': costs,
                         'centroidx': centroid[0],
                         'centroidy': centroid[1]})

        sum_area = sum([x.area for x in bestpus])

        # Parse mvbest
        fh = open(os.path.join(self.outdir,"output","nplcc_mvbest.csv"), 'r')
        lines = [x.strip().split(',') for x in fh.readlines()[1:]]
        fh.close()
        species = []
        num_target_species = 0
        num_met = 0
        for line in lines:
            sid = int(line[0])
            try:
                consfeat = ConservationFeature.objects.get(pk=sid)
            except ConservationFeature.DoesNotExist:
                logger.error("ConservationFeature %s doesn't exist; refers to an old scenario?" % sid)
                continue
            sname = consfeat.name
            sunits = consfeat.units
            slevel1 = consfeat.level1
            scode = consfeat.dbf_fieldname
            starget = float(line[2])
            try:
                starget_prop = species_level_targets[consfeat.pk]
            except KeyError:
                continue
            sheld = float(line[3])
            try:
                stotal = float(starget/starget_prop)
                spcttotal = sheld/stotal 
            except ZeroDivisionError:
                stotal = 0
                spcttotal = 0
            smpm = float(line[9])
            if starget == 0:
                smpm = 0.0
            smet = False
            if line[8] == 'yes' or smpm > 1.0:
                smet = True
                num_met += 1
            s = {'name': sname, 'id': sid, 'target': starget, 'units': sunits, 'code': scode, 
                    'held': sheld, 'met': smet, 'pct_target': smpm, 'level1': slevel1, 
                    'pcttotal': spcttotal, 'target_prop': starget_prop }
            species.append(s)      
            if starget > 0:
                num_target_species += 1

        species.sort(key=lambda k:k['name'].lower())

        res = {
            'costs': cost_weights,
            'geography': geography,
            'targets_penalties': targets_penalties,
            'area': sum_area, 
            'num_units': len(best),
            'num_met': num_met,
            'num_species': num_target_species, #len(species),
            'units': best,
            'species': species, 
            'bbox': bbox,
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
            status = """Analysis for <em>%s</em> is currently running.""" % (self.name,)
            code = 2
        elif process_is_complete(url):
            status = "%s processing is done." % self.name
            code = 3
        elif process_is_pending(url):
            status = "%s is in the queue but not yet running." % self.name
            res = get_process_result(url)
            code = 1
            if res is not None:
                status += ".. "
                status += str(res)
        else:
            status = "An error occured while running this analysis."
            code = 0
            res = get_process_result(url)
            if res is not None:
                status += "..<br/> "
                status += str(res)
            status += "<br/>Please edit the scenario and try again. If the problem persists, please contact us."

        return (code, "<p>%s</p>" % status)

    def process_results(self):
        if process_is_complete(self.get_absolute_url()):
            chosen = get_process_result(self.get_absolute_url())
            wshds = PlanningUnit.objects.filter(pk__in=chosen)
            self.output_best = json.dumps({'best': [str(x.pk) for x in wshds]})
            ssoln = [x.strip().split(',') for x in 
                     open(os.path.join(self.outdir,"output","nplcc_ssoln.csv"),'r').readlines()][1:]
            selected = {}
            for s in ssoln:
                num = int(s[1])
                if num > 0:
                    selected[int(s[0])] = num
            self.output_pu_count = json.dumps(selected) 
            super(Analysis, self).save() # save without calling save()
            self.invalidate_cache()

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
    def color(self):
        # colors are ABGR
        colors = [
         'aa0000ff',
         'aaff0000',
         'aa00ffff',
         'aaff00ff',
        ]
        return colors[self.pk % len(colors)]

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
        method = "best" 
        #method = "all"
        if method == "best":
            wshds = PlanningUnit.objects.filter(pk__in=wids)
        elif method == "all":
            wshds = PlanningUnit.objects.all()

        kmls = []
        color = self.color
        #color = "cc%02X%02X%02X" % (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        for ws in wshds:
            try:
                hits = puc[str(ws.pk)] 
            except:
                hits = 0

            if method == "all":
                numruns = settings.MARXAN_NUMREPS
                prop = float(hits)/numruns
                scale = (1.4 * prop * prop) 
                if scale > 0 and scale < 0.5: 
                    scale = 0.5
                desc = "<description>Included in %s out of %s runs.</description>" % (hits, numruns)
            else:
                prop = 1.0
                scale = 1.2
                desc = ""

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
                %s
                <styleUrl>style_%s</styleUrl>
                %s
            </Placemark>
            """ % (ws.fid, color, scale, ws.fid, ws.name, desc, ws.fid, asKml(ws.geometry.point_on_surface)))


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
        form = 'seak.forms.ScenarioForm'
        verbose_name = 'Prioritization Scenario' 
        show_template = 'nplcc/show.html'
        form_template = 'nplcc/form.html'
        form_context = {
            'cfs': ConservationFeature.objects.all(),
            'defined_geographies': DefinedGeography.objects.all(),
            'costs': Cost.objects.all(),
        }
        icon_url = 'common/images/watershed.png'
        links = (
            alternate('Shapefile',
                'seak.views.watershed_shapefile',
                select='single multiple',
                type='application/zip',
            ),
            alternate('Input Files',
                'seak.views.watershed_marxan',
                select='single',
                type='application/zip',
            ),
        )

# Post-delete hooks to remove the marxan files
@receiver(post_delete, sender=Scenario)
def _scenario_delete(sender, instance, **kwargs):
    if os.path.exists(instance.outdir):
        try:
            shutil.rmtree(instance.outdir)
            logger.debug("Deleting %s at %s" % (instance.uid, instance.outdir))
        except OSError:
            logger.debug("Can't deleting %s; forging ahead anyway..." % (instance.uid, instance.outdir))

@register
class Folder(FeatureCollection):
    description = models.TextField(default="", null=True, blank=True)
        
    class Options:
        verbose_name = 'Folder'
        valid_children = ( 
                'seak.models.Folder',
                'seak.models.Scenario',
                )
        form = 'seak.forms.FolderForm'
        show_template = 'folder/show.html'
        icon_url = 'common/images/folder.png'

class PlanningUnitShapes(models.Model):
    pu = models.ForeignKey(PlanningUnit)
    stamp = models.FloatField()
    bests = models.IntegerField(default=0) 
    hits = models.IntegerField(default=0) 
    fid = models.IntegerField(null=True)
    name = models.CharField(max_length=99, null=True)
    geometry = models.MultiPolygonField(srid=settings.GEOMETRY_DB_SRID, 
            null=True, blank=True, verbose_name="Planning Unit Geometry")
