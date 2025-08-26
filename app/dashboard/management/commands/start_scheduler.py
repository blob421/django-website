from django.core.management.base import BaseCommand
from dashboard.scheduler import start      
from dashboard.models import Document, UserProfile
import time
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Starts the APScheduler job'

    def handle(self, *args, **kwargs):
        start()

        content_type = ContentType.objects.get_for_model(UserProfile)

        default_avatar = Document.objects.get(id=1)
        
        if not default_avatar:
            Document.objects.create(object_id=0, id=1,
                upload_time='2025-08-22 11:33:40.330439+00',
                file='userprofile/0/avatar.png',
                content_type= content_type)
            
        self.stdout.write("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            self.stdout.write("Scheduler stopped.")