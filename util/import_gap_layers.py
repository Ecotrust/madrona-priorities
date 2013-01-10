from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','priorities',__file__)))

import settings
setup_environ(settings)
#==================================#
from madrona.layer_manager.models import Layer, Theme 
import csv

Layer.objects.filter(themes__name__startswith="gap_").delete()
Theme.objects.filter(name__startswith="gap_").delete()

with open("gap_services.csv",'r') as fh:
    species_list = csv.DictReader(fh)
    for sp in species_list:
        print sp['Common Name']
        url = sp['Model WMS'] + "/export"
        infourl = url.replace("/Mapserver/export", '')
        theme, created = Theme.objects.get_or_create(name="gap_%s" % sp['Category'], display_name="Northwest Gap Analysis - %s" % sp['Category'])
        lyr = Layer.objects.create(name=sp['Common Name'], layer_type="ArcRest", url=url, 
                opacity=0.5, description="%s (%s). <br/> For more info, see http://gap.uidaho.edu/index.php/species-modeling/" % (sp['Common Name'], 
                    sp['Scientific Name']), legend="/media/img/gap_legend.png", legend_title=sp['Common Name'] + " modeled presence/absence")
        lyr.themes.add(theme)
        lyr.save()
