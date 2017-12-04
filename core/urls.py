from django.conf.urls import url
from django.contrib import admin
from leave_bot.views import (
    index, listen_events, ask_leave, oauth,
    SignView, LogView, out, settings, StatisticsView, invite, invited
)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # bot internal urls
    url(r'^events/$', listen_events),
    url(r'^ask_leave/$', ask_leave),
    url(r'^oauth/$', oauth),
    # customer urls
    url(r'^index/$', index, name='index'),
    url(r'^settings/(?P<team_id>[A-Z0-9]+)/$', settings, name='settings'),
    url(r'^statistics/(?P<team_id>[A-Z0-9]+)/$', StatisticsView.as_view(), name='statistics'),
    url(r'^invited/(\S+)/$', invited),
    url(r'^invite/(?P<team_id>[A-Z0-9]+)/$', invite),
    # auth
    url(r'^register/$', SignView.as_view(), name='registration'),
    url(r'^logout$/', out, name='logout'),
    url(r'^', LogView.as_view(), name='login'),
]
