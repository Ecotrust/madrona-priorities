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
    input_target_coho = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label="Target Percentage of Coho Habitat")
    input_target_chinook = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label="Target Percentage of Chinook Habitat")
    input_target_steelhead = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label = "Taget Percentage of Steelhead Habitat")
    input_penalty_coho = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label="Penalty for missing Coho Habitat")
    input_penalty_chinook = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label="Penalty for missing Chinook Habitat")
    input_penalty_steelhead = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label = "Penalty for missing Steelhead Habitat")
    input_cost_climate = forms.FloatField(min_value=0, max_value=1.0, initial=0.5,
            widget=SliderWidget(min=0,max=1,step=0.01),
            label="Relative Cost of Climate Change")

    class Meta(FeatureForm.Meta):
        model = WatershedPrioritization
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)


class BufferPointsForm(FeatureForm):
    input_lat = forms.FloatField(max_value=90, min_value=-90, 
            widget=SliderWidget(min=43,max=44,step=0.001,image='analysistools/img/lat.gif'),
            label="Latitude")
    input_lon = forms.FloatField(max_value=180, min_value=-180, 
            widget=SliderWidget(min=-124.5,max=-122.5,step=0.001,image='analysistools/img/lon.gif'),
            label="Longitude")
    input_buffer_distance = forms.FloatField(
            widget=SliderWidget(min=10, max=50000,step=1,
                image = 'analysistools/img/buffer.png' ),
            label = "Buffer Distance (m)",
            min_value=0.0001, max_value=50000)

    class Meta(FeatureForm.Meta):
        # TODO put all this in AnalysisForm and inherit
        # requires lots of Metaprogramming complexity
        model = BufferPoint
        exclude = list(FeatureForm.Meta.exclude)
        for f in BufferPoint.output_fields():
            exclude.append(f.attname)
