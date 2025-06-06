# Generated by Django 4.1.2 on 2025-03-21 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_profile_life_expectancy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categories_Quest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default=None, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Quest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateField(auto_now=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quest', to='backend.profile', verbose_name='Профиль')),
                ('tests', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.categories_quest')),
            ],
        ),
    ]
