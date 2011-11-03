from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(os.path.join('..','wp',__file__)))

import settings
setup_environ(settings)

#==================================#
from arp.models import ConservationFeature as F
from arp.models import Cost
from django.template.defaultfilters import slugify

def output(level,val,crumbs, target=0.5, penalty=0.5):
    id = '---'.join([slugify(x) for x in crumbs])
    print "  "*level, '<span class="specieslabel">', val,'</span>'
    print "  "*level, '''<span class="sliders" id="span---%(id)s">
    <table>
    <tr>
    <td class="treelabel">Proportion of Total Value</td>
    <td><input type="text" class="slidervalue targetvalue" id="target---%(id)s" value="%(target)s"/></td>
    <td><div class="slider" id="slider_target---%(id)s"></div></td>
    </tr>
    <tr>
    <td class="treelabel">Importance Weighting</td>
    <td><input type="text" class="slidervalue penaltyvalue" id="penalty---%(id)s" value="%(penalty)s"/></td>
    <td><div class="slider" id="slider_penalty---%(id)s"></div></td>
    </tr>
    </table>
    </span>''' % {'id': id, 'target': target, 'penalty': penalty}

def header():
    print """{% extends "common/panel.html" %}
{% block title %}{{title}}{% endblock %}
{% block panel %}
<script type="text/javascript" charset="utf-8">
    lingcod.onShow(function(){
        var params_impute = function() {
            // If the input json is not null, 
            // Use them to restore the state of the tree
            if ($('#id_input_targets').val() && 
                $('#id_input_penalties').val() && 
                $('#id_input_relativecosts').val()) { 
                 
                console.log("Restoring Costs slider state...");
                var in_costs = JSON.parse($('#id_input_relativecosts').val());
                $.each(in_costs, function(key, val) {
                    $("#cost---" + key).val(val);
                });

                console.log("Restoring Targets slider state...");
                var in_targets = JSON.parse($('#id_input_targets').val());
                $.each(in_targets, function(key, val) {
                    $("#target---" + key).val(val);
                });

                console.log("Restoring Penalties slider state...");
                var in_penalties = JSON.parse($('#id_input_penalties').val());
                $.each(in_penalties, function(key, val) {
                    $("#penalty---" + key).val(val);
                });

                // Restore tree state
                var already_done_clicks = [];
                $.each(in_targets, function(key, val) {
                    //remove the last '---blah' from the key
                    b = key.split('---');
                    b.pop();
                    var id = b.join('---');

                    // If not already done, do a click
                    if (already_done_clicks.indexOf(id) == -1) {
                        $('span#span---' + id).click();
                        already_done_clicks.push(id);
                    }
                });
            };
        }; 

        lingcod.setupForm($('#featureform'));
        $("#focalspecies_tree").treeview({
            collapsed: true
        });

        params_impute();
       
        var params_collect = function() {
            var targets = {};
            var penalties = {};
            var costs = {};
            $('.targetvalue:visible').each( function(index) {
                var xid = $(this).attr("id");
                var id = "#" + xid;
                xid = xid.replace(/^target---/,''); //  Remove preceding identifier
                xid = xid.replace(/---$/,''); // Remove trailing ---
                targets[xid] = parseFloat($(id).val());
            });
            $('.penaltyvalue:visible').each( function(index) {
                var xid = $(this).attr("id");
                var id = "#" + xid;
                xid = xid.replace(/^penalty---/,''); //  Remove preceding identifier
                xid = xid.replace(/---$/,''); // Remove trailing ---
                penalties[xid] = parseFloat($(id).val());
            });
            $('.costvalue:visible').each( function(index) {
                var xid = $(this).attr("id");
                var id = "#" + xid;
                xid = xid.replace(/^cost---/,''); //  Remove preceding identifier
                costs[xid] = parseFloat($(id).val());
            });
            $('#id_input_targets').val( JSON.stringify(targets) ); 
            $('#id_input_penalties').val( JSON.stringify(penalties) );
            $('#id_input_relativecosts').val( JSON.stringify(costs) );
        };

        $('.slidervalue').each( function(index) {
            var id = $(this).attr("id");
            var slider_id = "slider_" + id;
            $('#' + slider_id).slider({
                range: 'min',
                min : 0, 
                max : 1,
                step : 0.01,
                change : function(event, ui) {
                    var theval = $(this).slider('value');
                    $('#' + id).val(theval);
                    $('div.slider[id^="' + slider_id + '---"]').each( function() {
                        $(this).slider('value', theval);
                    });
                },
                slide : function(event, ui) {
                    $('#' + id).val($(this).slider('value'));
                }
            });
            $('#' + slider_id).slider('value', $('#' + id).val());
            $('#' + id).change( function(){
                $('#' + slider_id).slider('value', $('#' + id).val());
            });
        });

        $('.submit_button').click(function(event){ 
            params_collect(); 
            $('#wp_form').trigger('submit');
        });
    });
</script>

<link rel="stylesheet" href="/media/common/js/treeview/jquery.treeview.css" />
<link rel="stylesheet" href="/media/common/js/treeview/jquery-widgets.css" />

    <h1>{{title}} input parameters</h1>


    <form id="featureform" action="{{action}}" method="post"> 
            <div class="field required">
                {{ form.name.label_tag }}
                {{ form.name.errors }}
                {{ form.name }}
            </div>
            <div class="hidden field required">
                {{ form.input_penalties.label_tag }}
                {{ form.input_penalties.errors }}
                {{ form.input_penalties }}            
                {{ form.input_targets.label_tag }}
                {{ form.input_targets.errors }}
                {{ form.input_targets }}            
                {{ form.input_relativecosts.label_tag }}
                {{ form.input_relativecosts.errors }}
                {{ form.input_relativecosts }}            
            </div>
            <p><input type="submit" value="submit"></p>
    </form>

<div class="tabs">
    <ul>
        <li>
            <a href="#speciestab">
                <span>Species</span>
            </a>
        </li>
    <li>
        <a href="#coststab">
            <span>Costs</span>
        </a>
    </li>
    </ul>

    <div id="speciestab">
    <h3>Set Proptions and Weights for Focal Fish Species</h3>
    <br/>
    <form action="#" id="focalspecies_form">
"""

def main():
    """
    Dear lord someone should be shot for writing this
    """
    L1 = F.objects.values_list('level1',flat=True).distinct()
    print "<ul id='focalspecies_tree'>"
    for val1 in L1:
        print "  <li>"
        output(1,val1,[val1])
        L2 = F.objects.filter(level1=val1).values_list('level2',flat=True).distinct().exclude(level2=None).exclude(level2='')
        print "  <ul>"
        for val2 in L2:
            print "    <li>"
            output(2,val2,[val1,val2])
            L3 = F.objects.filter(level2=val2).values_list('level3',flat=True).distinct().exclude(level3=None).exclude(level3='')
            if len(L3) > 0: print "    <ul>"
            for val3 in L3:
                print "      <li>"
                output(3,val3,[val1,val2,val3])
                L4 = F.objects.filter(level3=val3).values_list('level4',flat=True).distinct().exclude(level4=None).exclude(level4='')
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

def footer():
    print """ 
    </form></div> <!-- End species tab -->
    <div id="coststab">
        <h3>Set Relative Weights for Costs</h3>
        <br />
        <form action="#" id="costs_form">
           <div>
            <table>
    """
    for c in Cost.objects.all(): 
        cname = slugify(c.name.lower())
        print """
                <tr>
                <td><label for="cost---%(cname)s">%(full)s</label></td>
                <td><input type="text" class="slidervalue costvalue" id="cost---%(cname)s" value="0.5"/></td>
                <td><div class="slider" id="slider_cost---%(cname)s"></div></td>
                </tr>
        """ % {'cname': cname, 'full': c.name}

    print """
             </table>
           </div>
        </form>
    </div>
  </div>

    <br class="clear" />
    <div class="form_controls">
        <a href="#" class="submit_button button" onclick="this.blur(); return false;"><span>Submit</span></a>
        <a href="#" class="cancel_button button red" onclick="this.blur(); return false;"><span>Cancel</span></a>
        <br class="clear" />
    </div>
{% endblock panel %}"""


if __name__ == '__main__':
    header()
    main()
    footer()
