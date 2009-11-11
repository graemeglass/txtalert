from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.utils import simplejson
from django.views.decorators.http import require_POST, require_GET
from opera.gateway import gateway
from opera.models import SendSMS, PleaseCallMe
from opera.utils import (process_receipts_xml, require_POST_parameters, 
                            require_GET_parameters)
from opera.resource import SendSMSResource, PleaseCallMeResource
from opera.auth import has_perm_or_basicauth
from datetime import datetime, timedelta
import logging

@require_POST
def receipt(request):
    """Process a POSTed XML receipt from Opera, this is what it looks like:
    
        <?xml version="1.0"?>
        <!DOCTYPE receipts>
        <receipts>
          <receipt>
            <msgid>26567958</msgid>
            <reference>001efc31</reference>
            <msisdn>+44727204592</msisdn>
            <status>D</status>
            <timestamp>20080831T15:59:24</timestamp>
            <billed>NO</billed>
          </receipt>
          <receipt>
            <msgid>26750677</msgid>
            <reference>001f4041</reference>
            <msisdn>+44733476814</msisdn>
            <status>D</status>
            <timestamp>20080907T09:42:28</timestamp>
            <billed>NO</billed>
          </receipt>
        </receipts>
    
    """
    logging.debug(request.raw_post_data)
    success, fail = process_receipts_xml(request.raw_post_data)
    return HttpResponse(simplejson.dumps({
        'success': map(lambda rcpt: rcpt._asdict(), success),
        'fail': map(lambda rcpt: rcpt._asdict(), fail)
    }), content_type='text/json')


@has_perm_or_basicauth('opera.can_send_sms')
@require_POST
@require_POST_parameters('number','smstext')
def send_sms(request, format):
    numbers = request.POST.getlist('number')
    smstext = request.POST.get('smstext')
    if len(smstext) <= 160:
        sent_smss = gateway.send_sms(numbers, (smstext,) * len(numbers))
        return HttpResponse(SendSMSResource(sent_smss).publish(format), \
                                                content_type='text/%s' % format)
    else:
        return HttpResponseBadRequest("Too many characters")


@has_perm_or_basicauth('opera.can_view_sms_statistics')
@require_GET
@require_GET_parameters('since', reveal=True)
def send_sms_statistics(request, format):
    """Present SendSMS statistics over an HTTP API."""
    since = datetime.strptime(request.GET['since'], SendSMS.TIMESTAMP_FORMAT)
    sent_smss = SendSMS.objects.filter(delivery__gte=since)
    return HttpResponse(SendSMSResource(sent_smss).publish(format), \
                                        content_type='text/%s' % format)


@require_GET
@require_GET_parameters('number', 'sms_id')
def pcm(request):
    """Receive a please call me message from somewhere, probably FrontlineSMS"""
    sms_id = request.GET.get('sms_id')
    number = request.GET.get('number')
    message = request.GET.get('message', '')
    
    pcm = PleaseCallMe.objects.create(sms_id=sms_id, number=number, \
                                                                message=message)
    return HttpResponse('Your PCM has been received')


@has_perm_or_basicauth('opera.can_view_pcm_statistics')
@require_GET
@require_GET_parameters('since', reveal=True)
def pcm_statistics(request, format):
    """Present PCM statistics over an HTTP API. """
    since = datetime.strptime(request.GET['since'], SendSMS.TIMESTAMP_FORMAT)
    pcms = PleaseCallMe.objects.filter(created_at__gte=since)
    return HttpResponse(PleaseCallMeResource(pcms).publish(format), \
                                        content_type='text/%s' % format)
