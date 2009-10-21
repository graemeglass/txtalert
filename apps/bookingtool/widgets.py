from django import forms
from django.contrib.admin import widgets
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import loader
from bookingtool.cal import risk_on_date

def url_path_for(path):
    """convert 'js/file.js' into a valid path for the current static route"""
    return reverse("static", urlconf='txtalert.urls', args=(path,)) 

def url_paths_for(*paths):
    return [url_path_for(path) for path in paths]


class RiskDateWidget(widgets.AdminDateWidget):
    class Media:
        css = { 'all': url_paths_for('css/risk.css') }
        js = url_paths_for('jquery/js/jquery.js', 'js/risk.js')
    
    def __init__(self, attrs={}):
        # call the super's super as AdminDateWidget itself overrides __init__ 
        # and loses the passed attrs
        attrs['class'] = 'risk-field'
        super(widgets.AdminDateWidget, self).__init__(attrs=attrs)
    
    def render(self, name, value, attrs=None):
        if value:
            self.attrs['class'] = self.attrs.get('class','') + ' ' + risk_on_date(value)
        return super(RiskDateWidget, self).render(name, value, attrs)


class SmsVerificationWidget(widgets.AdminTextInputWidget):
    class Media:
        css = {'all': url_paths_for('css/sms-verification.css')}
        js = url_paths_for('jquery/js/jquery.js', 'js/sms-verification.js')
    
    def render(self, name, value, attrs=None):
        input = super(SmsVerificationWidget, self).render(name, value, attrs)
        return loader.render_to_string('sms_verification.html', locals())