# Generated by Django 5.2.4 on 2025-07-22 01:05

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_userprofile_recipients_alter_userprofile_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='recipients',
            field=models.ManyToManyField(blank=True, default='----', related_name='many_relation', to=settings.AUTH_USER_MODEL),
        ),
    ]
