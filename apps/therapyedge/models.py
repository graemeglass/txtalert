#  This file is part of TxtAlert.
#
#  TxtALert is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  TxtAlert is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with TxtAlert.  If not, see <http://www.gnu.org/licenses/>.


from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group
from dirtyfields import DirtyFieldsMixin
from history.models import HistoricalRecords

VISIT_STATUS_CHOICES = (
    ('m', 'Missed'),
    ('r', 'Rescheduled'),
    ('s', 'Scheduled'),
    ('a', 'Attended'),
)


class MSISDN(models.Model):
    msisdn = models.CharField('MSISDN', max_length=32, unique=True)

    class Meta:
        verbose_name = 'Mobile Number'
        verbose_name_plural = 'Mobile Numbers'

    def __unicode__(self):
        return self.msisdn


class Language(models.Model):
    name = models.CharField('Name', max_length=50)
    missed_message = models.TextField('Missed Message')
    attended_message = models.TextField('Attended Message')
    tomorrow_message = models.TextField('Tomorrow Message')
    twoweeks_message = models.TextField('Two Weeks Message')
    
    def __unicode__(self):
        return self.name
    


class Clinic(models.Model):
    te_id = models.CharField('TE ID', max_length=2, unique=True)
    name = models.CharField('Name', max_length=100)
    group = models.ForeignKey(Group, related_name='clinic', blank=True, 
                                null=True)
    
    class Meta:
        verbose_name = 'Clinic'
        verbose_name_plural = 'Clinics'
    
    def __unicode__(self):
        return self.name
    


class FilteredQuerySetManager(models.Manager):
    
    def __init__(self, *args, **kwargs):
        super(FilteredQuerySetManager, self).__init__()
        self.args = args
        self.kwargs = kwargs
    
    def get_query_set(self):
        return super(FilteredQuerySetManager, self) \
                .get_query_set() \
                .filter(*self.args, **self.kwargs)

class Patient(DirtyFieldsMixin,models.Model):
    SEX_CHOICES = (
        ('m', 'male'),
        ('f', 'female'),
        ('t', 'transgender'),
        ('f>m', 'transgender f>m'),
        ('m>f', 'transgender m>f'),
    )
    
    te_id = models.CharField('MRS ID', max_length=10, unique=True)
    msisdns = models.ManyToManyField(MSISDN, related_name='contacts')
    active_msisdn = models.ForeignKey(MSISDN, verbose_name='Active MSISDN', 
                                        null=True, blank=True)
    
    age = models.IntegerField('Age')
    sex = models.CharField('Sex', max_length=3, choices=SEX_CHOICES)
    opted_in = models.BooleanField('Opted In', default=False)
    disclosed = models.BooleanField('Disclosed', default=False)
    deceased = models.BooleanField('Deceased', default=False)
    last_clinic = models.ForeignKey(Clinic, verbose_name='Last Clinic', 
                                        blank=True, null=True)
    risk_profile = models.FloatField('Risk Profile', blank=True, null=True)
    language = models.ForeignKey(Language, verbose_name='Language', default=1)
    
    # soft delete & modification audit trail methods
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # custom manager that excludes all deleted patients
    objects = FilteredQuerySetManager(deleted=False)
    
    # normal custom manager, including deleted patients
    all_objects = models.Manager()
    
    # history of all patients
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
    
    def __unicode__(self):
        return self.te_id
    
    # Fixme: ugly on so many levels
    def save(self, *args, **kwargs):
        # save so that we have a PK
        if self.is_dirty(): super(Patient, self).save(*args, **kwargs)
        # Update the patients active_msisdn with the first in the list
        # of available options if none have been set yet
        if not self.active_msisdn and self.msisdns.count():
            # there is no ordering, depend on the database to specify
            # auto incrementing primary keys
            self.active_msisdn = self.msisdns.latest('id')
            self.save()
    
    def delete(self):
        """
        Implementing soft delete, this isn't possible with signals as far
        as I know since there isn't a way to cancel the delete to be executed
        """
        if not self.deleted:
            self.deleted = True
            self.save()
    
    def clinics(self):
        return [visit.clinic for visit in self.visit_set.order_by('-date')]
    
    def get_last_clinic(self):
        if self.visit_set.count(): 
            return self.visit_set.latest('date').clinic
        return None
    

class Visit(models.Model):
    
    VISIT_TYPES = (
        ('arv', 'ARV'),
        ('medical', 'Medical'), 
        ('counselor', 'Counselor'),
        ('pediatric', 'Pediatric'),
    )
    
    patient = models.ForeignKey(Patient)
    te_visit_id = models.CharField('TE Visit id', max_length=20, unique=True,
                                    null=True)
    date = models.DateField('Date')
    status = models.CharField('Status', max_length=1, 
                                choices=VISIT_STATUS_CHOICES)
    comment = models.TextField('Reason', default='')
    clinic = models.ForeignKey(Clinic)
    visit_type = models.CharField('Visit Type', blank=True, max_length=80, 
                                    choices=VISIT_TYPES)
    
    # soft delete & modification audit trail methods
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # custom manager that excludes all deleted patients
    objects = FilteredQuerySetManager(deleted=False)
    
    # normal custom manager, including deleted patients
    all_objects = models.Manager()
    
    # keep track of Visit changes over time
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Visit'
        verbose_name_plural = 'Visits'
        ordering = ['date']
    
    def delete(self):
        """
        Implementing soft delete, this isn't possible with signals as far
        as I know since there isn't a way to cancel the delete to be executed
        """
        if not self.deleted:
            self.deleted = True
            self.save()
    
    def __unicode__(self):
        return self.get_visit_type_display()
    


# class ImportEvent(models.Model):
#     content_type = models.ForeignKey(ContentType)
#     clinic = models.ForeignKey(Clinic, related_name='importevents')
#     stamp = models.DateTimeField('Date & Time', auto_now_add=True)
#     new = models.IntegerField('New Records')
#     updated = models.IntegerField('Updated Records')
#     errors = models.IntegerField('Errors')
# 
#     def __init__(self, *args, **kwargs):
#         if 'events' in kwargs.keys():
#             events = kwargs['events']
#             del kwargs['events']
#             kwargs.update({'new':events.new, 'updated':events.updated, 'errors':events.errors})
#         super(ImportEvent, self).__init__(*args, **kwargs)
# 
#     class Meta:
#         verbose_name = 'Import Event'
#         verbose_name_plural = 'Import Events'
# 
#     def __unicode__(self):
#         return '%s - New: %s, Updated: %s, Errors: %s' % (self.stamp, self.new, self.updated, self.errors)


class PleaseCallMe(models.Model):
    REASON_CHOICES = (
        ('nc', 'Not Called'),
        ('na', 'No Answer'),
        ('rm', 'Reschedule missed appointment'),
        ('rf', 'Reschedule future appointment'),
        ('ca', 'Confirm appointment'),
        ('vm', 'Voicemail'),
        ('ot', 'Other (fill in notes)'),
    )

    msisdn = models.ForeignKey(MSISDN, related_name='pcms', verbose_name='Mobile Number')
    timestamp = models.DateTimeField('Date & Time', auto_now_add=False)
    reason = models.CharField('Reason', max_length=2, choices=REASON_CHOICES, default='nc')
    notes = models.TextField('Notes', blank=True)
    clinic = models.ForeignKey(Clinic, related_name='pcms', blank=True, null=True)

    class Meta:
        verbose_name = 'Please Call Me'
        verbose_name_plural = 'Please Call Me(s)'

    def __unicode__(self):
        return '%s - %s' % (self.msisdn, self.timestamp)
    


# signals
from django.db.models.signals import post_save, pre_save
from therapyedge import signals
from gateway.models import PleaseCallMe as OperaPleaseCallMe

pre_save.connect(signals.check_for_opt_in_changes_handler, sender=Patient)
pre_save.connect(signals.find_clinic_for_please_call_me_handler, sender=PleaseCallMe)

post_save.connect(signals.track_please_call_me_handler, sender=OperaPleaseCallMe)
post_save.connect(signals.calculate_risk_profile_handler, sender=Visit)
