# Generated by Django 4.1.2 on 2025-03-13 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='balance',
            field=models.IntegerField(default=0),
        ),
    ]
