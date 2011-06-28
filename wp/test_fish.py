from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(__file__))

import settings
setup_environ(settings)

#==================================#
from arp.models import FocalSpecies as F
from django.template.defaultfilters import slugify

def output(level,val,crumbs):
    id = '---'.join([slugify(x) for x in crumbs])
    print "  "*level, "<span>", val,'</span>'
    print "  "*level, '''<span class="sliders">
    <table>
    <tr>
    <td>Target</td>
    <td><input type="text" class="slidervalue" id="target---%(id)s" value="%(default)s"/></td>
    <td><div class="slider" id="slider_target---%(id)s"></div></td>
    </tr>
    <tr>
    <td>Penalty</td>
    <td><input type="text" class="slidervalue" id="penalty---%(id)s" value="%(default)s"/></td>
    <td><div class="slider" id="slider_penalty---%(id)s"></div></td>
    </tr>
    </table>
    </span>''' % {'id': id, 'default': 0.5}

def header():
    print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>

    <meta http-equiv="content-type" content="text/html; charset=iso-8859-1"/>
    <title>Focal Species</title>
    
    <!--
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.2.6/jquery.min.js"></script>
    -->
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.5/jquery.min.js" type="text/javascript"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.11/jquery-ui.min.js" type="text/javascript"></script> 
    <script type="text/javascript" src="http://jqueryui.com/ui/jquery.ui.slider.js"></script> 
    <script src="./treeview/jquery.treeview.js" type="text/javascript"></script>
    
    <script type="text/javascript">
$(document).ready(function(){
    $("#focalspecies").treeview({
        collapsed: true
    });
      
      var params_update = function() {
        var html = "";
        $('#params_out').html(html);
        $('.slidervalue:visible').each( function(index) {
            var xid = $(this).attr("id");
            var id = "#" + xid;
            html += "<tr><td>" + xid + "</td><td>" + $(id).val() + "</td></tr>";
        });
        $('#params_out').html("<table>" + html + "</table>");
      };

      $('.slidervalue').each( function(index) {
        var id = $(this).attr("id");
        var slider_id = "#slider_" + id;
        id = "#" + id;
        $(slider_id).slider({
                range: 'min',
                min : 0, 
                max : 1,
                step : 0.01,
                change : function(event, ui) {
                    $(id).val($(this).slider('value'));
                },
                slide : function(event, ui) {
                    $(id).val($(this).slider('value'));
                }
        });
        $(slider_id).slider('value', $(id).val());
        $(id).change( function(){
            $(slider_id).slider("value", $(id).val());
        });
      });

            $('#refresh_params').click(function(event){ 
                params_update();
                event.preventDefault();
            });
});
    </script>

    <style type="text/css">
        li.collapsable > span.sliders { display: none; }
        li.expandable > span.sliders { color: black; display: inline; }
        .slider { margin-bottom: 5px;   }
        td { padding-right:6px; font-size: 80%; }
        .slidervalue { font-size: 80% }
        #params { float: right; padding: 10px; border: 1px black solid; margin: 10px; width:500px; }
    </style>
    <link rel="stylesheet" href="./treeview/jquery.treeview.css" />
    <link rel="stylesheet" href="./treeview/jquery-widgets.css" />

    </head>
    <body> 
     
    <div id="params">
      <span> Parameters to be submitted </span> <a href="#" id="refresh_params">[Refresh]</a>
      <hr/>
      <div id="params_out"></div>
    </div>

    <h3>Set Targets and Penalties for Focal Fish Species</h3>
    <p style="width: 400px;"> If you expand the list to get more detail, you must set values for all visible categories. 
        Only those species/groups that are visible (expanded) will be passed to the prioritization analysis.
        The box at the far-right shows the parameters that will be passed given the current state. </p>
    <span>Focal Fish Species</span>
"""

def footer():
    print """ </body></html>"""

def main():
    L1 = F.objects.values_list('level1',flat=True).distinct()
    print "<ul id='focalspecies'>"
    for val1 in L1:
        print "  <li>"
        output(1,val1,[val1])
        L2 = F.objects.filter(level1=val1).values_list('level2',flat=True).distinct().exclude(level2=None)
        print "  <ul>"
        for val2 in L2:
            print "    <li>"
            output(2,val2,[val1,val2])
            L3 = F.objects.filter(level2=val2).values_list('level3',flat=True).distinct().exclude(level3=None)
            if len(L3) > 0: print "    <ul>"
            for val3 in L3:
                print "      <li>"
                output(3,val3,[val1,val2,val3])
                L4 = F.objects.filter(level3=val3).values_list('level4',flat=True).distinct().exclude(level4=None)
                if len(L4) > 0: print "      <ul>"
                for val4 in L4:
                    print "        <li>"
                    output(4,val4,[val1,val2,val3,val4])
                    print "        </li>"
                if len(L4) > 0: print "      </ul>"
                print "      </li>"
            if len(L3) > 0: print "    </ul>"
            print "  </li>"
        if len(L2) > 0: print "  </ul>"
        print "  </li>"
    print "</ul>"

if __name__ == '__main__':
    header()
    main()
    footer()
