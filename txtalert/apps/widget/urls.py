from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView

urlpatterns = patterns('',
    (r'^$', TemplateView.as_view(template_name='index.html')),
    (r'^config\.xml$', TemplateView.as_view(template_name='config.xml')),
    (r'^widget\.html$', TemplateView.as_view(template_name='widget.html')),
)