from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.decorators import permission_required

from piston.utils import require_mime
from utils import process_receipts_xml
from django.settings import LOGGER as logging

# @permission_required('gateway.can_place_sms_receipt')
# @require_mime('xml')
def sms_receipt_handler(self, request):
    logging.info(request)
    logging.info(request.META)
    success, fail = process_receipts_xml(request.raw_post_data)
    return HttpResponse(simplejson.dumps({
        'success': map(lambda rcpt: rcpt._asdict(), success),
        'fail': map(lambda rcpt: rcpt._asdict(), fail)
    }), status=201, content_type='application/json; charset=utf-8')
