from app.dashboard.models import Document, UserProfile
from django.utils import timezone

document = Document.objects.get_or_create(object_id=0, 
         upload_time=timezone.now(), 
         file='userprofile/0/avatar.png',
         content_object = UserProfile)