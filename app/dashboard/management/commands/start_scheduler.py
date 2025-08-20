from django.core.management.base import BaseCommand
from dashboard.scheduler import start

class Command(BaseCommand):
    help = 'Starts the APScheduler job'

    def handle(self, *args, **kwargs):
        start()
