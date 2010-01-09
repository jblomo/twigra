# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('graph.views',
    (r'^$', 'list_messages'),
    (r'^process_messages$', 'process_messages'),
    (r'^insert_test_messages/(?P<months>\d+)$', 'insert_test_messages'),
    (r'^atimeline/(?P<screen_name>.+)/(?P<metric>.+)$', 'user_metric_detail'),
    # (r'^edit/(?P<key>.+)$', 'edit_person'),
    # (r'^delete/(?P<key>.+)$', 'delete_person'),
    # (r'^download/(?P<key>.+)/(?P<name>.+)$', 'download_file'),
)
