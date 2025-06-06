# Generated by Django 4.1.2 on 2025-06-04 09:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0023_alter_drugs_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Check_Drugs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateField(auto_now_add=True)),
                ('drugs', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drugs_check', to='backend.drugs', verbose_name='Профиль')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drugs_check', to='backend.profile', verbose_name='Профиль')),
            ],
        ),
    ]
