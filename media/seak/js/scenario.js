
function scenariosViewModel() {
  var self = this;

  // this will get bound to the active scenario
  self.selectedFeature = ko.observable(false);
  // display the form panel entirely
  self.showScenarioPanels = ko.observable();
  // display initial help
  self.showScenarioHelp = ko.observable(true);
  // display form
  self.showScenarioFormPanel = ko.observable(false);
  // display list of scenarios
  self.showScenarioList = ko.observable(true);
  // list of all scenarios, primary viewmodel
  self.scenarioList = ko.observableArray();

  // pagination config will display x items 
  // from this zero based index
  self.listStart = ko.observable(0);
  self.listDisplayCount = 12;

  // paginated list
  self.scenarioListPaginated = ko.computed(function () {
    return self.scenarioList.slice(self.listStart(), self.listDisplayCount+self.listStart());
  });

  // this list is model for pagination controls 
  self.paginationList = ko.computed(function () {
    var list = [], listIndex = 0, displayIndex = 1, listIndex = 0;
    for (listIndex=0; listIndex < self.scenarioList().length; listIndex++) {
      if (listIndex % self.listDisplayCount === 0 && Math.abs(listIndex - self.listStart()) < 5 * self.listDisplayCount) {
        list.push({'displayIndex': 1 + (listIndex/self.listDisplayCount), 'listIndex': listIndex });
      }
    }
    if (list.length < self.scenarioList().length / self.listDisplayCount) {
      list.push({'displayIndex': '...', 'listIndex': null })
      list.push({'displayIndex': '»', 'listIndex': null });

    }
    if (self.listStart() > 10) {
      list.shift({'displayIndex': '&laquo;', 'listIndex': null });      
    }
    return list;
  });

  self.setListIndex = function (button, event) {
    var listStart = self.listStart();
    if (button.displayIndex === '»') {
      self.listStart(listStart + self.listDisplayCount * 5);
    } else {
    self.listStart(button.listIndex);
    }
    self.selectFeature(self.scenarioList()[button.listIndex || self.listStart()]);
  }

  self.addScenarioStart = function() {
    self.showScenarioList(false);
    self.showScenarioForm('create');
  }

  self.showScenarioForm = function(action, uid) {
    // get the form
    var formUrl;
    if (action === "create") {
      formUrl = app.workspace["feature-classes"][0]["link-relations"]["create"]["uri-template"]; 
    } else if (action === "edit") {
      formUrl = app.workspace["feature-classes"][0]["link-relations"]["edit"][0]["uri-template"]; 
      formUrl = formUrl.replace('{uid}', uid);
    }
    // clean up and show the form
    $.get(formUrl, function(data) {
      var $form = $(data).find('form');
      $form.find('input:submit').remove();
      // app.cleanupForm($form);
      $('#scenarios-form-container').empty().append(data);
      self.showScenarioFormPanel(true);
      $form.find('input:visible:first').focus();
      $form.bind('submit', function(event) {
        event.preventDefault();
      });
    })
   
  }

  self.updateScenario = function(scenario_id, isNew) {
    var updateUrl = '/features/generic-links/links/geojson/{uid}/'.replace('{uid}', scenario_id);
    $.get(updateUrl, function(data) {
      if (isNew) {
        //self.scenario_layer.addFeatures(app.geojson_format.read(data));
        self.scenarioList.unshift(ko.mapping.fromJS(data.features[0].properties));
        self.selectedFeature(self.scenarioList()[0]);
      } else {
        ko.mapping.fromJS(data.features[0].properties, self.selectedFeature());
        self.showScenarioFormPanel(false);
        self.showScenarioList(true);
      }
    });
  }

  self.associateScenario = function(scenario_id, property_id) {
    var url = "/features/folder/{folder_uid}/add/{scenario_uid}";
    url = url.replace('{folder_uid}', property_id).replace('{scenario_uid}', scenario_id);
    $.ajax({
      url: url,
      type: "POST",
      success: function(data) {
        self.updateScenario(JSON.parse(data)["X-Madrona-Select"], true);
        app.scenarios.viewModel.showScenarioFormPanel(false);
        app.scenarios.viewModel.showScenarioList(true);
        app.new_features.removeAllFeatures();
      }
    })

  }

  self.saveScenarioForm = function(self, event) {
  }

  self.OLDsaveScenarioForm = function(self, event) {
    var isNew, $dialog = $('#scenarios-form-container'),
      $form = $dialog.find('form'),
      actionUrl = $form.attr('action'),
      values = {},
      error = false;
    $form.find('input,select').each(function() {
      var $input = $(this);
      if ($input.closest('.field').hasClass('required') && $input.attr('type') !== 'hidden' && !$input.val()) {
        error = true;
        $input.closest('.control-group').addClass('error');
        $input.siblings('p.help-block').text('This field is required.');
      } else {
        values[$input.attr('name')] = $input.val();
      }
    });
    if (error) {
      return false;
    }
    if (self.modifyFeature.active) {
      values.geometry_final = values.geometry_orig = self.modifyFeature.feature.geometry.toString();
      self.modifyFeature.deactivate();
      isNew = false;
    } else {
      //values.geometry_final = values.geometry_orig = app.scenarios.geometry;
      values.geometry_orig = app.scenarios.geometry;
      isNew = true;
    }
    $form.addClass('form-horizontal');
    $.ajax({
      url: actionUrl,
      type: "POST",
      data: values,
      success: function(data, textStatus, jqXHR) {
        var scenario_uid = JSON.parse(data)["X-Madrona-Select"];
        if (isNew) {
          self.associateScenario(scenario_uid, self.property.uid());
        } else {
          self.updateScenario(scenario_uid, false);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        self.cancelAddScenario();
      }
    });
  };

  self.showDeleteDialog = function () {
    $("#scenario-delete-dialog").modal("show");
  };

  self.closeDialog = function () {
    $("#scenario-delete-dialog").modal("hide");
  }


  // pagination config will display x items 
  // from this zero based index
  self.listStart = ko.observable(0);
  self.listDisplayCount = 12;
  // paginated list
  self.scenarioListPaginated = ko.computed(function () {
    return self.scenarioList.slice(self.listStart(), self.listDisplayCount+self.listStart());
  });

  self.deleteFeature = function () {
    var url = "/features/generic-links/links/delete/{uid}/".replace("{uid}", self.selectedFeature().uid());
    $('#scenario-delete-dialog').modal('hide');
    $.ajax({
      url: url,
      type: "DELETE",
      success: function (data, textStatus, jqXHR) {
        self.scenario_layer.removeFeatures(self.scenario_layer.getFeaturesByAttribute("uid", self.selectedFeature().uid()));
        self.scenarioList.remove(self.selectedFeature());
      }  
    });
  };

  // start the scenario editing process
  self.editScenario = function() {
    self.showScenarioList(false);
    self.showScenarioForm("edit", self.selectedFeature().uid());
  };

  self.cancelAddScenario = function () {
    self.showScenarioFormPanel(false);
    self.showScenarioList(true);
  }

  self.selectControl = {
      unselectAll: function () { 
         //console.log("unselect all"); 
      },
      select: function (x) {
         console.log("select"); 
      }
   }

  self.selectFeature = function(feature, event) {
    self.selectControl.unselectAll();
    var uid = "seak_scenario_4"; // TODO hardcoded test
    self.selectControl.select(uid);
    self.selectedFeature(self.scenarioList()[0]);
  }

  self.selectFeatureById = function (id) {
    var pageSize = self.scenarioList().length / self.listDisplayCount;
    $.each(self.scenarioList(), function (i, feature) {
      if (feature.uid() === id) {
        // set list start to first in list page      
        self.listStart(Math.floor(i / self.listDisplayCount) * self.listDisplayCount);
        self.selectedFeature(this);
      }
    });
  }

  self.reloadScenarios = function(property) {
    self.scenario_layer.removeAllFeatures();
    self.scenarioList.removeAll();
    self.property_layer.removeAllFeatures();
    map.addLayer(self.property_layer);
    map.addLayer(self.scenario_layer);
    self.loadScenarios(property);
    self.showScenarioList(true);
    app.selectFeature.deactivate();
    self.progressBarWidth("0%");
    self.showProgressBar(false);
  }

  self.loadViewModel = function (data) {
    self.scenarioList($.map(data.features, function (feature, i) {
      console.log(feature);
      return ko.mapping.fromJS(feature.properties);
    }));
    console.log(self.scenarioList());
    self.selectFeature(self.scenarioList()[0]);
  }

  self.loadScenarios = function(property) {
    var process = function(data) {
      if (data.features && data.features.length) {
        self.loadViewModel(data);
      } else {
        console.log("NO DATA");
      }
    };
    $.get('/seak/scenarios.geojson', process);
  }

  return self;
}
