from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from general.settings.models import Setting
from therapyedge.importer import Importer
from core.models import Clinic

class Command(BaseCommand):
    help = "Can be run as a cronjob or directly to send import TherapyEdge data."
    def handle(self, *args, **kwargs):
        importer = Importer(
            uri='https://%s:%s@196.36.218.99/tools/ws/sms/patients/server.php' % (
                Setting.objects.get(name='THERAPYEDGE_USERNAME').value,
                Setting.objects.get(name='THERAPYEDGE_PASSWORD').value
            ),
            verbose=settings.DEBUG
        )
        for clinic in Clinic.objects.all():
            # from midnight
            since = datetime.now().replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) - timedelta(days=1)
            # until 24 hrs later
            until = since + timedelta(days=1)
            print clinic.name, 'from', since, 'until', until
            for key, value in importer.import_all_changes(
                    clinic, 
                    since=since,
                    until=until
                ).items():
                print "\t%s: %s" % (key, value)