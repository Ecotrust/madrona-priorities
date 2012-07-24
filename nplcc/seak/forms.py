from madrona.features.forms import FeatureForm, SpatialFeatureForm
from models import *
from django import forms

class FolderForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Folder

class ScenarioForm(FeatureForm):
    input_scalefactor = forms.FloatField(widget=forms.TextInput(attrs={'class': 'slidervalue'}), initial=1.0)
    class Meta(FeatureForm.Meta):
        model = Scenario
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)

