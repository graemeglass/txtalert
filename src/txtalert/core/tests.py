from django.test import TestCase
from txtalert.core.models import *
from datetime import datetime

class ModelTestCase(TestCase):
    
    fixtures = ['patients', 'clinics', 'visits']
    
    def test_language_unicode(self):
        self.assertEquals(
            unicode(Language(name='english')),
            u'english'
        )
    
    def test_clinic_unicode(self):
        self.assertEquals(
            unicode(Clinic(name='clinic')),
            u'clinic'
        )
    
    def test_visit_unicode(self):
        self.assertEquals(
            unicode(Visit(visit_type='arv')),
            u'ARV'
        )
    
    def test_please_call_me_unicode(self):
        timestamp = datetime.now()
        msisdn = MSISDN.objects.create(msisdn='27123456789')
        self.assertEquals(
            unicode(PleaseCallMe(
                msisdn=msisdn,
                timestamp=timestamp
            )),
            u'%s - %s' % (msisdn, timestamp)
        )
    
    def test_patient_soft_delete(self):
        patient = Patient.objects.all()[0]
        patient.delete()
        # regular get fails because it is flagged as deleted
        self.assertRaises(
            Patient.DoesNotExist,
            Patient.objects.get,
            pk=patient.pk
        )
        # the all_objects manager however, should expose it
        self.assertEquals(patient, Patient.all_objects.get(pk=patient.pk))
    
    def test_patient_clinics(self):
        patient = Patient.objects.filter(last_clinic=None)[0]
        self.assertEquals(patient.get_last_clinic(), None)
        self.assertEquals(patient.clinics(), set([]))
        
        visit = patient.visit_set.create(
            clinic=Clinic.objects.all()[0],
            date=datetime.now(),
            status='s'
        )
        
        self.assertTrue(visit.clinic in patient.clinics())
        self.assertEquals(visit.clinic, patient.get_last_clinic())


from django.test import TestCase
from txtalert.apps.gateway.models import PleaseCallMe as GatewayPleaseCallMe
from txtalert.core.models import PleaseCallMe, Patient, Clinic, MSISDN
from datetime import datetime, timedelta

class PleaseCallMeTestCase(TestCase):
    
    fixtures = ['patients', 'clinics', 'visits']
    
    def setUp(self):
        # use dummy gateway
        from txtalert.apps import gateway
        gateway.load_backend('txtalert.apps.gateway.backends.dummy')
        
        self.patient = Patient.objects.all()[0]
        self.patient.save() # save to specify the active_msisdn
        
        # create a number of visits for this patient at a clinic
        for i in range(0,10):
            self.patient.visit_set.create(
                clinic=Clinic.objects.get(name='Crosby'),
                date=datetime.now() + timedelta(days=i),
                status='s'
            )
        
        self.assertTrue(self.patient.visit_set.all())
        self.assertTrue(self.patient.active_msisdn) # make sure that actually worked
        self.assertTrue(self.patient.get_last_clinic())
        self.assertTrue(self.patient.last_clinic)
        
    
    def tearDown(self):
        pass
    
    def test_please_call_me_from_gateway(self):
        # we should have non registered
        self.assertEquals(PleaseCallMe.objects.count(), 0)
        
        gpcm = GatewayPleaseCallMe.objects.create(
            sms_id='sms_id',
            sender_msisdn=self.patient.active_msisdn.msisdn,
            recipient_msisdn='27123456789',
            message='Please Call Me',
        )
        
        # we should have one registered through the signals
        self.assertEquals(PleaseCallMe.objects.count(), 1)
        pcm = PleaseCallMe.objects.latest('timestamp')
        self.assertEquals(pcm.msisdn, self.patient.active_msisdn)
        self.assertEquals(pcm.clinic, self.patient.last_clinic)
        self.assertEquals(pcm.notes, "Original SMS: %s" % gpcm.message)
    
    def test_please_call_me_from_therapyedge(self):
        pcm = PleaseCallMe.objects.create(
            msisdn = self.patient.active_msisdn,
            timestamp = datetime.now()
        )
        # the signals should track the clinic for this pcm if it hasn't
        # been specified automatically yet
        self.assertEquals(pcm.clinic, Clinic.objects.get(name='Crosby'))
    
    def test_pcm_for_nonexistent_msisdn(self):
        # verify this nr doesn't exist in the db
        self.assertRaises(
            MSISDN.DoesNotExist,
            MSISDN.objects.get,
            msisdn='27123456789'
        )
        # this shouldn't raise an error, it should fail silently leaving
        # message in the log file
        gpcm = GatewayPleaseCallMe.objects.create(
            sms_id='sms_id',
            sender_msisdn='27123456789' # this shouldn't exist in the db
        )
    
    def test_multiple_patients_for_one_msisdn(self):
        msisdn = MSISDN.objects.create(msisdn='27123456789')
        for i in range(0,2):
            Patient.objects.create(
                active_msisdn = msisdn,
                te_id='06-%s2345' % i,
                age=23
            )
        # we have two patients for the same msisdn
        self.assertEquals(
            Patient.objects.filter(active_msisdn=msisdn).count(),
            2
        )
        # this shouldn't raise an error, it should fail silently leaving
        # message in the log file
        gpcm = GatewayPleaseCallMe.objects.create(
            sms_id='sms_id',
            sender_msisdn=msisdn.msisdn
        )
    
