from django.contrib import admin
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Habit,Tracking_Habit,Drugs,Check_Drugs,Daily_check,Rentgen,Rentgen_Image,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,PetDaily_check,PetRentgen,PetRentgen_Image
@admin.register(PetRentgen_Image)
class PetRentgen_Image(admin.ModelAdmin):
    pass

@admin.register(PetDaily_check)
class PetDaily_check(admin.ModelAdmin):
    pass

@admin.register(PetRentgen)
class PetRentgen(admin.ModelAdmin):
    pass

@admin.register(Pet_Drugs)
class Pet_Drugs(admin.ModelAdmin):
    pass

@admin.register(Pet_Check_Drugs)
class Pet_Check_Drugs(admin.ModelAdmin):
    pass


@admin.register(PetChat)
class PetChat(admin.ModelAdmin):
    list_display = ['pet']

@admin.register(Calories)
class Calories(admin.ModelAdmin):
    list_display = ['profile']
@admin.register(Pet)
class Pet(admin.ModelAdmin):
    list_display = ['profile']

class Rentgen(admin.ModelAdmin):
    list_display = ['profile']

@admin.register(Rentgen_Image)
class Rentgen_Image(admin.ModelAdmin):
    list_display = ['rentgen']

@admin.register(Daily_check)
class Daily_check(admin.ModelAdmin):
    list_display = ['profile']
@admin.register(Check_Drugs)
class Drugss(admin.ModelAdmin):
    list_display = ['profile','created_at']

@admin.register(Drugs)
class Drugss(admin.ModelAdmin):
    list_display = ['profile']
# @admin.register(Relationship)
# class Relationship(admin.ModelAdmin):
#     list_display = ['profile']
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
