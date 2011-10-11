from lingcod.features.forms import FeatureForm, SpatialFeatureForm
from models import *
from django import forms

class FolderForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = Folder

class WatershedPrioritizationForm(FeatureForm):
    class Meta(FeatureForm.Meta):
        model = WatershedPrioritization
        exclude = list(FeatureForm.Meta.exclude)
        for f in model.output_fields():
            exclude.append(f.attname)

