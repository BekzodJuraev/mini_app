from django.contrib import admin
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Habit,Tracking_Habit,Drugs,Check_Drugs,Daily_check,Rentgen,Rentgen_Image,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,PetDaily_check,PetRentgen,PetRentgen_Image,Test, Question, Choice,Notification_drugs,NutritionGoal,Notification,NutritionGoalPet,PetCalories,Notification_Pet_drugs,Tests_Pet,PetShare,Critical_analysis,Question_critical,Choice_critical,CyclePeriod,DailyLog,MenHealthProfile,FemaleHealthProfile,ChildMeasurement,ChildIllnessReport,ChildCalendarEvent,CaloriesReportProfile,GeneralHealthReportProfile,DoctorProfile,ConsultationSettings,Consultation,DoctorWithdrawal,ChildHealthAnalysisProfile
from django.utils.html import format_html
import re

import nested_admin

@admin.register(DoctorWithdrawal)
class DoctorWithdrawalAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'amount', 'short_masked_card', 'cardholder_name', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('doctor__full_name', 'cardholder_name', 'card_number')
@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'client', 'status', 'doctor_earning', 'needs_in_person_visit', 'created_at')
    list_filter = ('status', 'needs_in_person_visit')
@admin.register(ConsultationSettings)
class ConsultationSettingsAdmin(admin.ModelAdmin):
    list_display = ('commission_percent',)
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "telegram_id",
        "specialization",
        "cabinet_status_display",
        "balance_display",
        "rating_display",

        "is_active",
    )

    readonly_fields = (
        "cabinet_status_display",
        "balance_display",
        "rating_display",
        "total_earned",
        "created_at",
        "short_description_readonly",
        "consultation_price_readonly",
    )

    def get_fields(self, request, obj=None):
        # При СОЗДАНИИ врача ("Добавить врача") скрываем то, что заполняет врач сам
        if obj is None:
            return (
                "telegram_id",
                "full_name",
                "photo",
                "specialization",
                "education",
                "qualification",
                "practice_start_date",
                "is_active",
                "cabinet_status_display",
                "balance_display",
                "rating_display",
            )
        # При ПРОСМОТРЕ/РЕДАКТИРОВАНИИ выводим все твои поля + статус кабинета
        return (
            "telegram_id",
            "full_name",
            "photo",
            "specialization",
            "education",
            "qualification",
            "practice_start_date",
            "is_active",
            "cabinet_status_display",
            "short_description_readonly",
            "consultation_price_readonly",
            "balance_display",
            "total_earned",
            "rating_display",

        )

    @admin.display(description="Статус кабинета врача")
    def cabinet_status_display(self, obj):
        if obj is None or not obj.pk or not obj.is_cabinet_ready:
            return format_html(
                '<span style="color: #e03131; font-weight: bold;">'
                'Кабинет недоступен (врач ещё не заполнил «Коротко о себе» и «Стоимость консультации» в своём кабинете)'
                '</span>'
            )
        return format_html('<span style="color: #2f9e44; font-weight: bold;">Кабинет активен и заполнен</span>')

    @admin.display(description="Текущий баланс к выводу")
    def balance_display(self, obj):
        if obj is None or not obj.pk or not obj.balance:
            return "0 ₽"
        return f"{obj.balance} ₽"

    @admin.display(description="Рейтинг")
    def rating_display(self, obj):
        if obj is None or not obj.pk or obj.rating is None:
            return "Нет оценок"
        return f"{float(obj.rating):.1f}"

    @admin.display(description="Коротко о себе (заполняется врачом)")
    def short_description_readonly(self, obj):
        return obj.short_description if (obj and obj.short_description) else "Не заполнено врачом"

    @admin.display(description="Стоимость консультации для клиента (заполняется врачом)")
    def consultation_price_readonly(self, obj):
        return f"{obj.consultation_price} ₽" if (obj and obj.consultation_price) else "Не указана врачом"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Меняет заголовок страницы редактирования на русский язык"""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['title'] = f"Редактирование врача: {obj.full_name}"
        else:
            extra_context['title'] = "Редактирование врача"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        """Меняет заголовок списка врачей на русский язык"""
        extra_context = extra_context or {}
        extra_context['title'] = "Выбор врача для изменения"
        # Передаем extra_context только один раз (по ключевому слову)
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ChildHealthAnalysisProfile)
class ChildHealthAnalysisProfileadmin(admin.ModelAdmin):
    pass
@admin.register(GeneralHealthReportProfile)
class GeneralHealthReportProfileadmin(admin.ModelAdmin):
    pass
@admin.register(CaloriesReportProfile)
class CaloriesReportProfileadmin(admin.ModelAdmin):
    pass
@admin.register(ChildCalendarEvent)
class ChildCalendarEventadmin(admin.ModelAdmin):
    pass
@admin.register(ChildIllnessReport)
class ChildIllnessReportadmin(admin.ModelAdmin):
    pass
@admin.register(ChildMeasurement)
class ChildMeasurement(admin.ModelAdmin):
    pass

class ChoiceInlinecritical(nested_admin.NestedTabularInline):
    model = Choice_critical
    extra = 0  # Было 3, теперь пустых полей по умолчанию не будет
    # Если нужно, чтобы хотя бы один ответ был всегда:
    min_num = 1

class QuestionInlinecritical(nested_admin.NestedStackedInline):
    model = Question_critical
    extra = 0  # Было 1
    inlines = [ChoiceInlinecritical]

@admin.register(Critical_analysis)
class CriticalAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title','get_system', 'example_answer')
    list_filter = ('system',)
    search_fields = ('title',)
    inlines = [QuestionInlinecritical]

    fieldsets = (
        ("Основные настройки", {
            'fields': ('system','sub_section')
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


@admin.register(FemaleHealthProfile)
class FemaleHealthProfile(admin.ModelAdmin):
    pass
@admin.register(MenHealthProfile)
class MenHealthProfile(admin.ModelAdmin):
    pass
@admin.register(CyclePeriod)
class CyclePeriod(admin.ModelAdmin):
    pass
@admin.register(DailyLog)
class DailyLog(admin.ModelAdmin):
    pass
@admin.register(PetShare)
class PetShare(admin.ModelAdmin):
    pass
@admin.register(Tests_Pet)
class Tests_Pet(admin.ModelAdmin):
    pass
@admin.register(Notification_Pet_drugs)
class Notification_Pet_drugs(admin.ModelAdmin):
    pass
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
    list_display = ['profile','created_at']
@admin.register(Pet)
class Pet(admin.ModelAdmin):
    list_display = ('klichka', 'pet', 'age', 'pet_family_ref')

@admin.register(Rentgen)
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
    list_display = ['profile','created_at']

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



SERVICE_MODELS_ORDER = {
    "doctorprofile": 1,         # Врачи
    "consultationsettings": 2,  # Настройки комиссии сервиса
    "test": 3,                  # Тесты
    "critical_analysis": 4,     # Тесты Kритические анализы
}

_original_get_app_list = admin.site.get_app_list


def custom_get_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label)

    # Если открыта отдельная страница конкретного приложения, не дублируем
    if app_label:
        return app_list

    service_models = []

    for app in app_list:
        # 1. Переводим название блока Backend на русский
        if app.get("app_label", "").lower() == "backend" or app.get("name", "").lower() == "backend":
            app["name"] = "Основной раздел"

        # 2. Забираем 4 нужные модели по точному имени класса из models.py
        remaining_models = []
        for model_dict in app.get("models", []):
            obj_name = str(model_dict.get("object_name", "")).strip().lower()

            if obj_name in SERVICE_MODELS_ORDER:
                service_models.append(model_dict)
            else:
                remaining_models.append(model_dict)

        app["models"] = remaining_models

    # 3. Сортируем ровно в том порядке, как в ТЗ:
    # Врачи -> Настройки комиссии сервиса -> Тесты -> Тесты Критические анализы
    service_models.sort(
        key=lambda m: SERVICE_MODELS_ORDER.get(str(m.get("object_name", "")).strip().lower(), 99)
    )

    # 4. Добавляем отдельный блок «Управление сервисом» в самый низ меню
    if service_models:
        app_list.append({
            "name": "Управление сервисом",
            "app_label": "service_management",
            "app_url": "/admin/",
            "has_module_perms": True,
            "models": service_models,
        })

    return app_list


admin.site.get_app_list = custom_get_app_list