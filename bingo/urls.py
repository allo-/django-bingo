from django.conf.urls import patterns, include, url

import views

urlpatterns = patterns('',
    url('^$', views.main),
    url('^bingo/reclaim/$', views.reclaim_board),
    url('^bingo/create/$', views.create_board),
    url('^bingo/(?P<board_id>[0-9]*)/$', views.bingo),
)
