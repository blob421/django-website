from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
user_model = get_user_model()

@receiver(post_save, sender=user_model)
def assign_admin_group(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile') and instance.userprofile.role.name == 'Secretary':
        group, _ = Group.objects.get_or_create(name='Administration')
        group.user_set.add(instance)
