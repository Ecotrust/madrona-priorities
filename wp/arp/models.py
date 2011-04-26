from django.db import models
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
import os

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
        background: url('%(media)skmltree/dist/images/sprites/kml.png?1302821411') no-repeat 0px 0px ! important;
        } """ % { 'uid': klass.model_uid(), 'media': settings.MEDIA_URL }
    
@register
class UserKml(PrivateLayerList):
    class Options:
        verbose_name = "Uploaded KML"
        form = 'arp.forms.UserKmlForm'

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
    input_cost_climate = models.FloatField(verbose_name='Relative cost of Climate Change')

    # All output fields should be allowed to be Null/Blank
    output_units = models.TextField(null=True, blank=True,
            verbose_name="Watersheds in Optimal Reserve")
    output_geometry = models.MultiPolygonField(srid=settings.GEOMETRY_CLIENT_SRID, 
            null=True, blank=True, verbose_name="Watersheds")

    def run(self):
        from random import choice
        self.output_units = None
        hucs = [x.huc12 for x in Watershed.objects.all()]
        chosen = []
        for i in range(6):
            chosen.append(choice(hucs))
        self.output_units = ','.join([str(x) for x in chosen])
        wshds = Watershed.objects.filter(huc12__in=chosen)
        self.output_geometry = wshds.collect()
        return True

    @classmethod
    def mapnik_geomfield(self):
        return "output_geometry"

    @property 
    def kml_done(self):
        wids = [int(x.strip()) for x  in self.output_units.split(',')]
        wshds = Watershed.objects.filter(huc12__in=wids)
        return "%s\n\n<Folder id=\"%s\"><name>Optimal Reserve Units</name>%s</Folder>" % (self.kml_style, 
                self.uid,
                '\n'.join([x.kml for x in wshds]))

    @property 
    def kml_working(self):
        return """
        <Placemark id="%s">
            <visibility>0</visibility>
            <name>%s (WORKING)</name>
        </Placemark>
        """ % (self.uid, self.name)

    @property
    def elapsed_time(self):
        import datetime
        return str(datetime.datetime.now() - self.date_modified)

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
        show_template = 'analysis/show.html'
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
            <name>%s buffer</name>
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

