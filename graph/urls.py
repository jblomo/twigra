# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('graph.views',
    (r'^$', 'list_messages'),
    (r'^process_messages$', 'process_messages'),
    (r'^insert_test_messages/(?P<months>\d+)$', 'insert_test_messages'),
    (r'^user/(?P<screen_name>\w+)$', 'follower_detail'),
    (r'^user/(?P<screen_name>\w+)\.(?P<json>json)$', 'follower_detail'),
    (r'^atimeline/(?P<screen_name>\w+)/(?P<metric>\w+)$', 'follower_metric_detail'),
    (r'^atimeline/(?P<screen_name>\w+)/(?P<metric>\w+)\.json$', 'follower_metric_detail_json'),
    (r'^update_followers$', 'update_followers'),
    # (r'^delete/(?P<key>.+)$', 'delete_person'),
    # (r'^download/(?P<key>.+)/(?P<name>.+)$', 'download_file'),
)
