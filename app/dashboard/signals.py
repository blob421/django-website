from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from dashboard.models import UserProfile, WeekRange, Schedule, Users


user_model = get_user_model()

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
        
