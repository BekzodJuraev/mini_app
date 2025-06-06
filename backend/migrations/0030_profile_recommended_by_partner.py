# Generated by Django 4.1.2 on 2025-06-05 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0029_alter_profile_family_ref_alter_profile_ref'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='recommended_by_partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ref_system', to='backend.profile'),
        ),
    ]
