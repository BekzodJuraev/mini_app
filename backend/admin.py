from django.contrib import admin
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Habit,Tracking_Habit,Drugs,Check_Drugs,Daily_check,Rentgen,Rentgen_Image,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,PetDaily_check,PetRentgen,PetRentgen_Image,Test, Question, Choice,Notification_drugs,NutritionGoal,Notification,NutritionGoalPet,PetCalories
import nested_admin
@admin.register(PetCalories)
class PetCalories(admin.ModelAdmin):
    pass
@admin.register(NutritionGoalPet)
class NutritionGoalPetadmin(admin.ModelAdmin):
    pass
@admin.register(Notification)
class Notification(admin.ModelAdmin):
    pass
class ChoiceInline(nested_admin.NestedTabularInline):
    model = Choice
    extra = 0  # Было 3, теперь пустых полей по умолчанию не будет
    # Если нужно, чтобы хотя бы один ответ был всегда:
    min_num = 1

class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 0  # Было 1
    inlines = [ChoiceInline]

@admin.register(Test)
class TestAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'role', 'which_animal', 'get_system', 'subsection','example_answer')
    list_filter = ('role', 'system', 'which_animal')
    search_fields = ('title',)
    inlines = [QuestionInline]

    fieldsets = (
        ("Основные настройки", {
            'fields': ('role', 'which_animal', 'system', 'subsection')
        }),
        ("Контент", {
            'fields': ('title', 'description','example_answer')
        }),
    )

    class Media:
        js = (
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/question_type_toggle.js',
        )

    def get_system(self, obj):
        return obj.get_system_display() # Используем display для красивого имени из choices
    get_system.short_description = 'Система'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type')
    list_filter = ('test', 'question_type')
    inlines = [ChoiceInline]

# Простая регистрация для категорий


@admin.register(NutritionGoal)
class NutritionGoaladmin(admin.ModelAdmin):
    pass


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
   pass
@admin.register(Notification_drugs)
class Drugss(admin.ModelAdmin):
   pass
@admin.register(Drugs)
class Drugss(admin.ModelAdmin):
    pass
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
