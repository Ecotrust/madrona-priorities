from lingcod.features.forms import FeatureForm, SpatialFeatureForm
from models import *
from django import forms

class FolderForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Folder

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

