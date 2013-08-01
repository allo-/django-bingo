from django.conf.urls import patterns, include, url

import views

urlpatterns = patterns('',
    url('^$', views.bingo),
    url('^bingo/(?P<bingo_id>[0-9]*)/$', views.bingo),
)
