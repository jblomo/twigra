# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import redirect_to, direct_to_template
from google.appengine.ext import db
from graph.models import Datapoint
from mimetypes import guess_type
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response
from gviz_api import gviz_api
import logging
import random
import re
import simplejson
from datetime import datetime, timedelta
import urllib2

def install_opener():
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, 'http://twitter.com/', settings.TWNAME, settings.TWPASSWORD)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(urllib2.HTTPHandler, handler)
    urllib2.install_opener(opener)

def list_messages(request):
    url = 'http://twitter.com/direct_messages.json'
    install_opener()
    response = simplejson.load(urllib2.urlopen(url))
    logging.info("loaded " + str(response))
    
    return direct_to_template(request, 'graph/messages.html', extra_context={'response_json': response})

def show_datapoint(request, key):
    return object_detail(request, Datapoint.all(), key)

def process_messages(request):
    most_recent = Datapoint.all().order('-created_at').get()
    url = 'http://twitter.com/direct_messages.json?since_id=%u' % (most_recent.message_id if most_recent else 0)
    install_opener()
    response = simplejson.load(urllib2.urlopen(url))

    for tweet in response:
        dp = dict(
            message_id = tweet['id'],
            sender_screen_name = tweet['sender_screen_name'],
            created_at = datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y"),
        )

        (metric, sep, value) = tweet['text'].partition(':')
        if sep != ':':
            logger.warn("Tweet " + str(tweet) + " improperly formatted")
            continue

        dp['metric'] = metric
        match = re.match("-?\d+(\.\d+)?", value.lstrip())
        dp['numerical'] = float(match.group())
        dp['annotation'] = value.lstrip()[match.end():].strip()

        Datapoint(**dp).put()

    return direct_to_template(request, 'graph/messages.html', extra_context={'response_json': response})

def insert_test_messages(request,months):
    update = datetime.now()
    mid = 0
    while update > datetime.now() - timedelta(int(months)*30):
        Datapoint(
                message_id = mid,
                sender_screen_name = 'jimblomo',
                metric = 'test',
                numerical = float(random.randrange(-100,100)),
                created_at = update,
                annotation = 'annotation' if random.randrange(-100,100) % 7 == 0 else '',
                ).put()
        update -= timedelta(1)
        mid += 1

def user_metric_detail(request, screen_name, metric):
    description = {
            "created_at": ("Date", "date"),
            "numerical": ("number", metric),
            "title1": ("string", "Annotation")}
    data = []
    for datapoint in Datapoint.all().filter('sender_screen_name =', screen_name).filter('metric = ', metric).order('created_at'):
        data.append({'created_at': datapoint.created_at, 'numerical': datapoint.numerical, 'title1': datapoint.annotation})

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    jscode = data_table.ToJSCode("jscode_data", columns_order=("created_at", "numerical", "title1"))

    return direct_to_template(request, 'graph/user_metric_detail.html', 
            extra_context={
                'table_json': jscode,
                'metric': metric,
                'screen_name': screen_name,
                })
    
# def add_person(request):
#     return create_object(request, form_class=PersonForm,
#         post_save_redirect=reverse('myapp.views.show_person',
#                                    kwargs=dict(key='%(key)s')))
# 
# def edit_person(request, key):
#     return update_object(request, object_id=key, form_class=PersonForm,
#         post_save_redirect=reverse('myapp.views.show_person',
#                                    kwargs=dict(key='%(key)s')))
# 
# def delete_person(request, key):
#     return delete_object(request, Person, object_id=key,
#         post_delete_redirect=reverse('myapp.views.list_people'))
# 
# def download_file(request, key, name):
#     file = get_object_or_404(File, key)
#     if file.name != name:
#         raise Http404('Could not find file with this name!')
#     return HttpResponse(file.file,
#         content_type=guess_type(file.name)[0] or 'application/octet-stream')
# 
# def create_admin_user(request):
#     user = User.get_by_key_name('admin')
#     if not user or user.username != 'admin' or not (user.is_active and
#             user.is_staff and user.is_superuser and
#             user.check_password('admin')):
#         user = User(key_name='admin', username='admin',
#             email='admin@localhost', first_name='Boss', last_name='Admin',
#             is_active=True, is_staff=True, is_superuser=True)
#         user.set_password('admin')
#         user.put()
#     return render_to_response(request, 'myapp/admin_created.html')
