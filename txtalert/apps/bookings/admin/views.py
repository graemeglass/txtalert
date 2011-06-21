from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from txtalert.apps.bookings.admin import forms
from txtalert.apps.bookings.views import effective_page_range_for
from txtalert.core.models import Patient, Visit, ChangeRequest
from txtalert.core.utils import normalize_msisdn
import logging
from datetime import datetime, date

LOGIN_PERMISSION = 'core.add_patient'
LOGIN_URL = '/bookings/admin/sign-in/'

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def index(request):
    return render_to_response('admin/index.html', {},
        context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def new_patient(request):
    if request.POST:
        form = forms.MSISDNForm(request.POST)
        if form.is_valid():
            msisdn = form.cleaned_data['msisdn']
            logging.error("Send SMS via VUMI to %s" % msisdn)
            messages.add_message(request, messages.INFO, 
                        'A verification SMS has been sent to %s.' % msisdn)
            
            return HttpResponseRedirect("%s?msisdn=%s" % (
                reverse('bookings:admin:new_patient_details'), msisdn))
    else:
        form = forms.MSISDNForm()
    return render_to_response("admin/patient/new.html", {
        'form': form
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def new_patient_details(request):
    if request.POST:
        form = forms.PatientForm(request.POST)

        if form.is_valid():
            patient = form.save(commit=False)
            patient.owner = request.user
            # TODO: possible race condition
            patient.te_id = 'bookings-%s' % Patient.objects.count()
            patient.save()
            logging.debug('Created new patient: %s' % patient)
            messages.add_message(request, messages.INFO, 'Patient %(name)s '
                '%(surname)s registered' % form.cleaned_data)
            return HttpResponseRedirect(reverse('bookings:admin:index'))
        else:
            messages.add_message(request, messages.ERROR,
                'Registration failed. Please see errors below.')
    else:
        form = forms.PatientForm(initial={
            'active_msisdn': request.GET.get('msisdn')
        })
    return render_to_response('admin/patient/new_details.html', {
        'form': form
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def find_patient(request):
    if 'patient_id' in request.GET:
        
        msisdn = request.GET.get('msisdn', '')
        if msisdn:
            msisdn = normalize_msisdn(msisdn)
        
        patients = Patient.objects.filter(
            Q(te_id__icontains=request.GET.get('patient_id','')) |
            Q(active_msisdn__msisdn=msisdn))
            # TODO: add surname to patient model field
        return render_to_response('admin/patient/results.html', {
            'patients': patients,
            'next': request.GET.get('next')
        }, context_instance=RequestContext(request))
    else:
        return render_to_response('admin/patient/find.html', {
            'next': request.GET.get('next')
        }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def new_appointment(request):
    return render_to_response('admin/appointment/new.html', {
        'patient': get_object_or_404(Patient, pk=request.GET.get('patient_id'))
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def new_appointment_details(request):
    
    date = datetime.strptime(request.GET.get('date'), '%d-%b-%Y')
    patient = get_object_or_404(Patient, pk=request.GET.get('patient_id'))
    
    if request.POST:
        form = forms.VisitForm(request.POST, initial={
            'date': date
        })
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.date = date
            visit.te_visit_id = 'bookings-visit-%s' % Visit.objects.count()
            visit.status = 's' # scheduled
            visit.save()
            messages.add_message(request, messages.INFO, 'Appointment made')
            return HttpResponseRedirect(reverse('bookings:admin:view_appointment', 
                kwargs={'visit_id': visit.pk}))
        else:
            messages.add_message(request, messages.ERROR, 'Please correct '
                'the errors below')
    else:
        form = forms.VisitForm(initial={
            'visit_type': 'arv',
            'clinic': patient.get_last_clinic(),
            'date': date
        })
    return render_to_response('admin/appointment/new_details.html', {
        'date': date,
        'patient': patient,
        'form': form
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def view_appointment(request, visit_id):
    visit = get_object_or_404(Visit, pk=visit_id)
    return render_to_response('admin/appointment/details.html', {
        'visit': visit
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def change_appointment(request, visit_id):
    visit = get_object_or_404(Visit, pk=visit_id)
    if request.POST:
        form = forms.EditVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Appointment changed')
    else:
        form = forms.EditVisitForm(instance=visit)
    return render_to_response('admin/appointment/change.html', {
        'visit': visit,
        'patient': visit.patient,
        'form': form
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def appointments(request):
    date_parts = ['year', 'month', 'day']
    if all(['date_%s' % p in request.GET for p in date_parts]):
        day = date(*[int(request.GET.get('date_%s' % v)) for v in date_parts])
        day_label = day.strftime('%d %B %Y')
    else:
        day = date.today()
        day_label = 'Today'
    
    form = forms.SimpleDateForm(initial={
        'date': day
    })
    
    visits = Visit.objects.filter(date=day)
    try:
        first_upcoming_visit = Visit.objects.upcoming()[0]
    except IndexError:
        first_upcoming_visit = None
    
    paginator = Paginator(visits, 5)
    page = paginator.page(request.GET.get('p', 1))
    
    return render_to_response('admin/appointment/index.html', {
        'day': day,
        'day_label': day_label,
        'paginator': paginator,
        'page': page,
        'effective_page_range': effective_page_range_for(page, paginator),
        'form': form,
        'first_upcoming_visit': first_upcoming_visit,
        'query_string': '&'.join(['date_%s=%s' % (part, getattr(day, part)) 
            for part in date_parts])
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def view_patient(request):
    patient = get_object_or_404(Patient, pk=request.GET.get('patient_id'))
    return HttpResponseRedirect(reverse('bookings:admin:edit_patient', kwargs={
        'patient_id': patient.pk
    }))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    visits = patient.visit_set.all()
    attended = visits.filter(status='a').count()
    missed = visits.filter(status='m').count()
    rescheduled = visits.filter(status='r').count()
    total = visits.filter(date__lt=date.today()).count()
    if attended > 0:
        attendance = int(float(attended) / float(total) * 100)
    else: 
        attendance = 0
    
    if request.POST:
        form = forms.PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save()
            messages.add_message(request, messages.INFO, 'Patient updated')
            return HttpResponseRedirect(reverse('bookings:admin:edit_patient', kwargs={
                'patient_id': patient.pk
            }))
    else:
        form = forms.PatientForm(instance=patient, initial={
            'active_msisdn': patient.active_msisdn.msisdn
        })
    return render_to_response('admin/patient/view.html', {
        'patient': patient,
        'form': form,
        'attendance': attendance,
        'attended': attended,
        'rescheduled': rescheduled,
        'missed': missed,
        'total': total,
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def change_requests(request):
    change_requests = ChangeRequest.objects.all()
    
    paginator = Paginator(change_requests, 5)
    page = paginator.page(request.GET.get('p', 1))
    
    return render_to_response('admin/change_request/index.html', {
        'paginator': paginator,
        'page': page
    }, context_instance=RequestContext(request))

@permission_required(LOGIN_PERMISSION, login_url=LOGIN_URL)
def change_request_details(request, change_request_id):
    change_request = get_object_or_404(ChangeRequest, pk=change_request_id)
    return render_to_response('admin/change_request/date.html', {
        'change_request': change_request,
        'visit': change_request.visit,
        'patient': change_request.visit.patient,
    }, context_instance=RequestContext(request))