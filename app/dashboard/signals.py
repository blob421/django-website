from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from dashboard.models import UserProfile, WeekRange, Schedule

user_model = get_user_model()


@receiver(post_save, sender=user_model)
def assign_admin_group(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile') and instance.userprofile.role.name == 'Secretary':
        group, _ = Group.objects.get_or_create(name='Administration')
        group.user_set.add(instance)

@receiver(post_save, sender=UserProfile)
def create_schedule(sender, instance, **kwargs):
       
        has_schedule = Schedule.objects.filter(user=instance).exists()

        if not has_schedule:
      
                
            week_ranges = WeekRange.objects.all().order_by('-end_day')[:4]
            for week in week_ranges:
                
                
                Schedule.objects.create(user=instance, week_range=week)
        
