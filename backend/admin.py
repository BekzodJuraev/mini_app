from django.contrib import admin
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Habit,Tracking_Habit,Relationship,Drugs,Check_Drugs

@admin.register(Check_Drugs)
class Drugss(admin.ModelAdmin):
    list_display = ['profile']

@admin.register(Drugs)
class Drugss(admin.ModelAdmin):
    list_display = ['profile']
@admin.register(Relationship)
class Relationship(admin.ModelAdmin):
    list_display = ['profile']
@admin.register(Habit)
class Habit(admin.ModelAdmin):
    list_display = ['profile']

@admin.register(Tracking_Habit)
class Tracking_Habit(admin.ModelAdmin):
    list_display = ['profile','created_at']


@admin.register(Chat)
class Chat(admin.ModelAdmin):
    list_display = ['profile']

@admin.register(Tests)
class Tests(admin.ModelAdmin):
    list_display = ['name','read','created_at']

# Register your models here.
@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ['username','name']

@admin.register(Categories_Quest)
class Categories_Quest(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Quest)
class Quest(admin.ModelAdmin):
    list_display = ['profile', 'created_at']
