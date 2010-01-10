# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from google.appengine.ext import db
from ragendja.dbutils import cleanup_relations

class Datapoint(db.Model):
    """Data point to graph with optional annotation"""
    message_id = db.IntegerProperty(required=True)
    sender_screen_name = db.StringProperty(required=True)
    metric = db.StringProperty(required=True)
    numerical = db.FloatProperty(required=True)
    created_at  = db.DateTimeProperty(None, False, True, required=True)
    annotation = db.StringProperty(required=False)
    location = db.GeoPtProperty(required=False)

    def __unicode__(self):
        return '%s %s:%f (%s) @ %s' % (self.sender_screen_name, self.metric, self.numerical, self.annotation, self.created_at)

    @permalink
    def get_absolute_url(self):
        return ('myapp.views.show_datapoint', (), {'key': self.key()})

class Follower(db.Model):
    """List of follower IDs"""
    user_id = db.IntegerProperty(required=True)
    screen_name = db.StringProperty(required=True)
    created_at  = db.DateTimeProperty(None, False, True, required=True)

    def __unicode__(self):
        return '%s (%s)' % (self.screen_name, self.user_id)

# signals.pre_delete.connect(cleanup_relations, sender=Person)
# 
# class File(db.Model):
#     owner = db.ReferenceProperty(Person, required=True, collection_name='file_set')
#     name = db.StringProperty(required=True)
#     file = db.BlobProperty(required=True)
# 
#     @permalink
#     def get_absolute_url(self):
#         return ('myapp.views.download_file', (), {'key': self.key(),
#                                                   'name': self.name})
# 
#     def __unicode__(self):
#         return u'File: %s' % self.name
# 
# class Contract(db.Model):
#     employer = db.ReferenceProperty(Person, required=True, collection_name='employee_contract_set')
#     employee = db.ReferenceProperty(Person, required=True, collection_name='employer_contract_set')
#     start_date = db.DateTimeProperty()
#     end_date = db.DateTimeProperty()
