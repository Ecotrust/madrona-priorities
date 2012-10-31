# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DefinedGeography'
        db.create_table('seak_definedgeography', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=99)),
        ))
        db.send_create_signal('seak', ['DefinedGeography'])

        # Adding M2M table for field planning_units on 'DefinedGeography'
        db.create_table('seak_definedgeography_planning_units', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('definedgeography', models.ForeignKey(orm['seak.definedgeography'], null=False)),
            ('planningunit', models.ForeignKey(orm['seak.planningunit'], null=False))
        ))
        db.create_unique('seak_definedgeography_planning_units', ['definedgeography_id', 'planningunit_id'])


    def backwards(self, orm):
        
        # Deleting model 'DefinedGeography'
        db.delete_table('seak_definedgeography')

        # Removing M2M table for field planning_units on 'DefinedGeography'
        db.delete_table('seak_definedgeography_planning_units')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 7, 19, 9, 43, 46, 965579)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 7, 19, 9, 43, 46, 965425)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'seak.conservationfeature': {
            'Meta': {'object_name': 'ConservationFeature'},
            'dbf_fieldname': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'level1': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'level2': ('django.db.models.fields.CharField', [], {'max_length': '99', 'null': 'True', 'blank': 'True'}),
            'level3': ('django.db.models.fields.CharField', [], {'max_length': '99', 'null': 'True', 'blank': 'True'}),
            'level4': ('django.db.models.fields.CharField', [], {'max_length': '99', 'null': 'True', 'blank': 'True'}),
            'level5': ('django.db.models.fields.CharField', [], {'max_length': '99', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'uid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '90', 'null': 'True', 'blank': 'True'})
        },
        'seak.cost': {
            'Meta': {'object_name': 'Cost'},
            'dbf_fieldname': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'desc': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'uid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'})
        },
        'seak.definedgeography': {
            'Meta': {'object_name': 'DefinedGeography'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'}),
            'planning_units': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['seak.PlanningUnit']", 'symmetrical': 'False'})
        },
        'seak.folder': {
            'Meta': {'object_name': 'Folder'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'seak_folder_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'seak_folder_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'seak_folder_related'", 'to': "orm['auth.User']"})
        },
        'seak.planningunit': {
            'Meta': {'object_name': 'PlanningUnit'},
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'fid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99'})
        },
        'seak.planningunitshapes': {
            'Meta': {'object_name': 'PlanningUnitShapes'},
            'bests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'fid': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'geometry': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857', 'null': 'True', 'blank': 'True'}),
            'hits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '99', 'null': 'True'}),
            'pu': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seak.PlanningUnit']"}),
            'stamp': ('django.db.models.fields.FloatField', [], {})
        },
        'seak.puvscf': {
            'Meta': {'unique_together': "(('pu', 'cf'),)", 'object_name': 'PuVsCf'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seak.ConservationFeature']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pu': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seak.PlanningUnit']"})
        },
        'seak.puvscost': {
            'Meta': {'unique_together': "(('pu', 'cost'),)", 'object_name': 'PuVsCost'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cost': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seak.Cost']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pu': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['seak.PlanningUnit']"})
        },
        'seak.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'seak_scenario_related'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_geography': ('seak.models.JSONField', [], {}),
            'input_penalties': ('seak.models.JSONField', [], {}),
            'input_relativecosts': ('seak.models.JSONField', [], {}),
            'input_scalefactor': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'input_targets': ('seak.models.JSONField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'255'"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'output_best': ('seak.models.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'output_pu_count': ('seak.models.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'sharing_groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'seak_scenario_related'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'seak_scenario_related'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['seak']
