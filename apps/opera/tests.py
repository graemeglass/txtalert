from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from opera.views import element_to_namedtuple
import xml.etree.ElementTree as ET
from opera.gateway import Gateway
from opera.models import SendSMS
from datetime import datetime
import base64

def basic_auth_string(username, password):
    b64 = base64.encodestring('%s:%s' % (username, password)).strip()
    return 'Basic %s' % b64

class OperaTestingGateway(object):
    """Dummy gateway we used to monkey patch the real RPC gateway so we can write
    our test code against something we control"""
    
    def use_identifier(self, identifier):
        """specify what identifier to return"""
        self.identifier = identifier
    
    def SendSMS(self, args):
        return {'Identifier': self.identifier}
    

class OperaTestCase(TestCase):
    """Testing the opera gateway interactions"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', \
                                                email='user@domain.com', \
                                                password='password')
        self.user.save()
        
        
        self.gateway = Gateway('http://testserver/', 'service_id', 'password', \
                                'channel', verbose=True)
        # specify the proxy's EAPIGateway, which is what Opera uses internally
        setattr(self.gateway.proxy, 'EAPIGateway', OperaTestingGateway())
        
        # add a helper function to set the identifier
        def use_identifier(identifier):
            self.gateway.proxy.EAPIGateway.use_identifier(identifier)
        setattr(self.gateway, 'use_identifier', use_identifier)
    
    def test_send_sms(self):
        """we've hijacked the EAPIGateway and tell it what to return as the 
        identifier. The SendSMS object should store that identifier after 
        communicating with the RPC gateway"""
        self.gateway.use_identifier('12345678')
        [send_sms,] = self.gateway.send_sms(['27764493806'],['testing'])
        self.assertEqual(send_sms.identifier, '12345678')
    
    def test_receipt_processing(self):
        """Test the receipt XML we get back from Opera when a message has been 
        sent successfully"""
        raw_xml_post = """
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
        
        # fake us having sent SMSs and having stored the proper identifiers
        tree = ET.fromstring(raw_xml_post.strip())
        receipts = map(element_to_namedtuple, tree.findall('receipt'))
        
        for receipt in receipts:
            self.gateway.use_identifier(receipt.reference)
            self.gateway.send_sms([receipt.msisdn], ['testing %s' % receipt.reference])
        
        # mimick POSTed receipt from Opera
        response = self.client.post(reverse('sms-receipt'), raw_xml_post.strip(), \
                                    content_type='text/xml')
        
        # it should return a JSON response
        self.assertEquals(response['Content-Type'], 'text/json')
        
        # test the json response
        from django.utils import simplejson
        data = simplejson.loads(response.content)
        self.assertTrue(data.keys(), ['fail','success'])
        # all should've succeeded
        self.assertEquals(len(data['success']), 2)
        # we should get the dict back representing the receipt
        self.assertEquals([r._asdict() for r in receipts], data['success'])
        
        # check database state
        for receipt in receipts:
            send_sms = SendSMS.objects.get(number=receipt.msisdn, identifier=receipt.reference)
            self.assertEquals(send_sms.delivery_timestamp.strftime(SendSMS.TIMESTAMP_FORMAT), receipt.timestamp)
            self.assertEquals(send_sms.status, 'D')
    
    def test_json_statistics_auth(self):
        response = self.client.get(reverse('sms-statistics',kwargs={"format":"json"}))
        self.assertEquals(response.status_code, 401)
        
        self.user.user_permissions.add(Permission.objects.get(codename='can_view_statistics'))
        
        response = self.client.get(reverse('sms-statistics',kwargs={'format':'json'}), \
                                    HTTP_AUTHORIZATION=basic_auth_string('user','password'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'text/json')
    
    def test_send_sms_json_response(self):
        self.user.user_permissions.add(Permission.objects.get(codename='can_send_sms'))
        response = self.client.post(reverse('sms-send', kwargs={'format':'json'}), \
                                    {
                                        'numbers': '27764493806',
                                        'smstexts': 'hello'
                                    }, \
                                    HTTP_AUTHORIZATION=basic_auth_string('user', 'password'))
        self.assertEquals(response.status_code, 200)