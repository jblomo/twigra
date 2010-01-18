# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.simple import redirect_to, direct_to_template
# TODO -- This will eventually be moved out of labs namespace
from google.appengine.ext import db
from graph.models import Datapoint, Follower
from mimetypes import guess_type
from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response
from gviz_api import gviz_api
import logging
import random
import re
from django.utils import simplejson
from datetime import datetime, timedelta
import urllib2

def install_opener():
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, 'https://twitter.com/', settings.TWNAME, settings.TWPASSWORD)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(urllib2.HTTPHandler, handler)
    urllib2.install_opener(opener)

def list_messages(request):
    url = 'https://twitter.com/direct_messages.json'
    install_opener()
    response = simplejson.load(urllib2.urlopen(url))
    logging.info("loaded " + str(response))
    
    return direct_to_template(request, 'graph/messages.html', extra_context={'response_json': response})

def show_datapoint(request, key):
    return object_detail(request, Datapoint.all(), key)

def process_messages(request):
    most_recent = Datapoint.all().order('-created_at').get()
    url = 'https://twitter.com/direct_messages.json?since_id=%u' % (most_recent.message_id if most_recent else 0)
    install_opener()
    response = simplejson.load(urllib2.urlopen(url))

    for tweet in response:
        dp = dict(
            message_id = tweet['id'],
            sender_screen_name = tweet['sender_screen_name'].lower(),
            created_at = datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y"),
        )

        (metric, sep, value) = tweet['text'].partition(':')
        if sep != ':':
            logging.warn("Tweet " + str(tweet) + " improperly formatted")
            continue

        dp['metric'] = metric.lower()

        match = re.match("-?\d+(\.\d+)?", value.lstrip())
        if match:
            dp['numerical'] = float(match.group())
            dp['annotation'] = value.lstrip()[match.end():].strip()
        else:
            logging.warn("Tweet " + str(tweet) + " improperly formatted")
            continue

        follower = Follower.get_or_insert(str(tweet['sender']['id']),
                use_id = tweet['sender']['id'],
                screen_name = tweet['sender_screen_name'].lower(),
                metrics = [dp['metric']])
        if dp['metric'] not in follower.metrics:
            follower.metrics.append(dp['metric'])
            follower.put()
        dp['follower'] = follower

        Datapoint(**dp).put()

    return direct_to_template(request, 'graph/messages.html', extra_context={'response_json': response})


def update_followers(request):
    url = 'http://twitter.com/followers/ids/%s.json' % ( settings.TWNAME )
    # don't need authentication for followers
    response = simplejson.load(urllib2.urlopen(url))
    install_opener()

    followers = map(lambda k: int(k.name()), Follower.all(keys_only=True).fetch(5000))
    follow_url = 'https://twitter.com/friendships/create.json?user_id=%s'
    show_user_url = 'http://twitter.com/users/show.json?user_id=%s'
    for new_follower in filter(lambda f: f not in followers, response):
        try:
            success = simplejson.load(urllib2.urlopen(follow_url % (new_follower), ''))
        except urllib2.HTTPError, e:
            if hasattr(e, 'code') and e.code == 403:
                logging.warn("Apparently we're already following %s, just getting info" % (new_follower))
                success = simplejson.load(urllib2.urlopen(show_user_url % (new_follower)))

        if not success:
            logging.warn("Could not follow %s" % (new_follower))
            continue;

        Follower( key_name = str(new_follower),
                user_id = new_follower,
                screen_name = success['screen_name'].lower(),
                ).put()

    return direct_to_template(request, 'graph/update_followers.html', 
            extra_context={'response_json': response, 'followers': followers})


def insert_test_messages(request,months):
    update = datetime.now()
    mid = 0
    follower = Follower.all().filter('screen_name = ', 'jimblomo').get()
    while update > datetime.now() - timedelta(int(months)*30):
        Datapoint(
                message_id = mid,
                sender_screen_name = 'jimblomo',
                follower = follower,
                metric = 'test',
                numerical = float(random.randrange(1,10)),
                created_at = update,
                annotation = 'annotation' if random.randrange(1,10) % 7 == 0 else '',
                ).put()
        update -= timedelta(1)
        mid += 1
    return redirect_to(request, reverse('graph.views.follower_metric_detail', 
        kwargs=dict(screen_name='jimblomo', metric='test')))
        

def follower_metric_detail_json(request, screen_name, metric):
    follower = Follower.all().filter('screen_name = ', screen_name.lower()).get()
    if follower:
        description = {
                "created_at": ("datetime", "date"),
                "numerical": ("number", metric),
                "title1": ("string", "Annotation")}
        data = []
        for datapoint in Datapoint.all().filter('follower =', follower).filter('metric = ', metric.lower()).order('created_at'):
            data.append({'created_at': datapoint.created_at, 'numerical': datapoint.numerical, 'title1': datapoint.annotation})

        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)
        json = data_table.ToJSonResponse(columns_order=("created_at", "numerical", "title1"))

        return HttpResponse(json, mimetype='application/json')
    else:
        raise Http404


def follower_metric_detail(request, screen_name, metric):
    follower = Follower.all().filter('screen_name = ', screen_name.lower()).get()
    if follower:
        return direct_to_template(request, 'graph/follower_metric_detail.html', 
            extra_context={
                'metric': metric,
                'follower': follower,
                'not_much_data': Datapoint.all().filter('follower =', follower).filter('metric = ', metric.lower()).order('created_at').count(5) < 3,
                'most_recent':   Datapoint.all().filter('follower =', follower).filter('metric = ', metric.lower()).order('created_at').get()
            })
    else:
        return direct_to_template(request, 'graph/follower_404.html')


def follower_detail(request, screen_name, json=False):
    follower = Follower.all().filter('screen_name = ', screen_name.lower()).get()
    if follower:
        dp_of_follower = Datapoint.all().filter('follower = ', follower)
        if json:
            data = []
            current_value = {}
            display_metrics = set()
            recent_metrics = dp_of_follower.order('-created_at').fetch(500)
            recent_metrics.reverse()
            for datapoint in recent_metrics:
                display_metrics.add(datapoint.metric)
                current_value[datapoint.metric] = datapoint.numerical
                data.append(current_value.copy())

            description = {}
            for metric_name in display_metrics:
                description[metric_name] = ('number', metric_name)
    
            data_table = gviz_api.DataTable(description)
            data_table.LoadData(data)
            json = data_table.ToJSonResponse()
    
            return HttpResponse(json, mimetype='application/json')
        else:
            last_metrics = {}
            for metric in follower.metrics:
                last = Datapoint.all().filter('follower = ', follower).filter('metric = ', metric).order('-created_at').get()
                last_metrics[metric] = {
                        'created_at': last.created_at.isoformat(), 
                        'numerical': last.numerical, 
                        'annotation': last.annotation }

            return direct_to_template(request, 'graph/follower_detail.html', extra_context = { 
                'object': follower, 
                'last_metrics': simplejson.dumps(last_metrics)
                })
    else:
        return direct_to_template(request, 'graph/follower_404.html', extra_context={ 'screen_name' : screen_name })
    
