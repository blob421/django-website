from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from dashboard.models import (UserProfile, WeekRange, Schedule, Users, LogginRecord, Messages,
                              Day, Agenda)
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in
from dateutil.relativedelta import relativedelta

from .utility import notify
user_model = get_user_model()


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    date = timezone.now()
    target_week_range = WeekRange.objects.order_by('-starting_day')[3]                
    last_schedule = Schedule.objects.get(user=user.userprofile, week_range=target_week_range)
    notify.delay(user.userprofile.id, 'login')
    LogginRecord.objects.create(user=user.userprofile, timestamp = date, schedule=last_schedule)
    

@receiver(post_save, sender=user_model)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserProfile)
def assign_admin_group(sender, instance, **kwargs):
    role_name = getattr(instance.role, 'name', None)
    if role_name and role_name.lower().strip() == 'secretary':
        group, _ = Group.objects.get_or_create(name='Administration')
        group.user_set.add(instance.user)


@receiver(post_save, sender=UserProfile)
def create_schedule(sender, instance, **kwargs):
       
        has_schedule = Schedule.objects.filter(user=instance).exists()
        if not has_schedule:
      
                
            week_ranges = WeekRange.objects.all().order_by('-end_day')[:4]
            for week in week_ranges:
                        
                Schedule.objects.create(user=instance, week_range=week)


        has_days = Day.objects.filter(user=instance).last()
        if not has_days:
            current_date = timezone.now().date()
            days_to_create = [
            Day(user = instance, date=current_date + relativedelta(days=n + 1)) for n in range(180)
                ]
            
            days = Day.objects.bulk_create(days_to_create)
            days_list = list(days)
            agenda = Agenda.objects.create(user=instance)  
            agenda.days.set(days_list)
    
