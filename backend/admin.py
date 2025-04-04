from django.contrib import admin
from .models import Profile,Categories_Quest,Quest,Tests,Chat



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
