# Generated by Django 5.2.4 on 2025-07-25 03:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0023_team_pinned_msg'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='team_lead',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='team_lead', to='dashboard.userprofile'),
        ),
    ]
