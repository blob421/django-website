from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from dashboard.models import UserProfile, Stats, Team
from django.contrib.contenttypes.models import ContentType
user_model = get_user_model()

@receiver(post_save, sender=user_model)
def assign_admin_group(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile') and instance.userprofile.role.name == 'Secretary':
        group, _ = Group.objects.get_or_create(name='Administration')
        group.user_set.add(instance)


@receiver(post_save, sender=UserProfile)
def ensure_stats_exists(sender, instance, **kwargs):
    if not instance.stats.exists():
        Stats.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )

@receiver(post_save, sender=Team)
def ensure_stats_exists(sender, instance, **kwargs):
    if not instance.stats.exists():
        Stats.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )