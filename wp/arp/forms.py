from lingcod.features.forms import FeatureForm, SpatialFeatureForm
from models import *
from django import forms

class FolderForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Folder

class AOIForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = AOI

class LOIForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = LOI

class POIForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = POI

class WatershedPrioritizationForm(SpatialFeatureForm):
    class Meta(SpatialFeatureForm.Meta):
        model = WatershedPrioritization

class UserKmlForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = UserKml

class WatershedPrioritizationForm(FeatureForm):
    input_lat = forms.FloatField(max_value=90, min_value=-90, 
            widget=SliderWidget(min=-90,max=90,step=0.00001,image='analysistools/img/lat.gif'),
            label="Latitude")
    input_lon = forms.FloatField(max_value=180, min_value=-180, 
            widget=SliderWidget(min=-180,max=180,step=0.00001,image='analysistools/img/lon.gif'),
            label="Longitude")
    input_buffer_distance = forms.FloatField(
            widget=SliderWidget(min=10, max=50000,step=1,
                image = 'analysistools/img/buffer.png' ),
            label = "Buffer Distance (m)",
            min_value=0.0001, max_value=50000)

    class Meta(FeatureForm.Meta):
        model = WatershedPrioritization
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)


