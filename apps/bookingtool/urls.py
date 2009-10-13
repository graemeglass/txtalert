from django.conf.urls.defaults import *
from bookingtool import views

urlpatterns = patterns('',
    (r'risk\.js', views.risk),
    (r'calendar/(?P<year>\d{4})/(?P<month>\d{1,2})\.html', views.calendar, {}, 'calendar'),
    (r'calendar/today.html', views.today, {}, 'calendar-today'),
)
