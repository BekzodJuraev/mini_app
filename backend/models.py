from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from datetime import date,timedelta
import uuid
from django_q.tasks import async_task
from django.db.models import Sum
from django.utils import timezone
from .update import update_life_expectancy_decorator,health_recommendations_decorator,environmental_risk_decorator,monthly_report_only_tests_decorator,pet_risk_analysis_decorator,health_recommendations_start_decorator
from django.db import models
from .validators import validate_face_photo
# 1. Система здоровья (например, Пищеварительная)
class Test(models.Model):
    ROLE_CHOICES = [
        ('human', 'Взрослый'),
        ('baby', 'Ребенок'),
        ('animal', 'Животное'),
    ]

    # Список систем (Верхний уровень)
    SYSTEM_CHOICES = [
        ('others', '📁 Другие'),
        ('respiratory', 'Дыхательная система'),
        ('cardio', 'Сердечно-сосудистая система'),
        ('skeletal', 'Опорно-двигательный аппарат'),
        ('endocrine', 'Эндокринная система'),
        ('digestive', 'Пищеварительная система'),
        ('reproductive', 'Половая система'),
        ('nervous', 'Нервная система'),
        ('excretory', 'Выделительная система'),
        ('dental', 'Зубочелюстная система'),
        ('sensory', 'Органы чувств'),
        ('hematopoietic', 'Органы кроветворения'),
        ('immune', 'Иммунная система'),
        ('psychological', 'Психологическое состояние'),
    ]
    ANIMAL_CHOICES = [
        ('cat', 'Кошка'),
        ('dog', 'Собака'),
        ('rat', 'Крыса'),
        ('mouse', 'Мышь'),
        ('svinka', 'Морск.свинка'),
        ('xomyak', 'Хомяк'),
        ('shinshila', 'Шиншилла'),
    ]


    # Список подразделов (Нижний уровень)
    SUBSECTION_CHOICES = [
        # Общий тонус

        # Дыхательная система

        ('lungs', 'Легкие'),
        ('trachea', 'Трахея'),
        ('nasopharynx', 'Носоглотка'),
        ('bronchi', 'Бронхи'),
        ('ribs', 'Рёбра'),
        ('diaphragm', 'Диафрагма'),

        # Сердечно-сосудистая система
        ('pulse', 'Пульс'),
        ('systolic', 'Систолическое давление'),
        ('diastolic', 'Диастолическое давление'),

        # Опорно-двигательный аппарат
        ('skeleton', 'Скелет'),
        ('muscles', 'Мышцы'),
        ('spine', 'Позвоночник'),
        ('protection', 'Защита'),
        ('joint_flexibility', 'Гибкость суставов'),
        ('cushioning', 'Амортизация'),

        # Эндокринная система
        ('thyroid', 'Щитовидная железа'),
        ('pineal', 'Шишковидная железа'),
        ('adrenals', 'Надпочечники'),
        ('pancreas', 'Поджелудочная железа'),
        ('thymus', 'Вилочковая железа'),
        ('gonads', 'Половые железы'),

        # Пищеварительная система

        ('esophagus', 'Пищевод'),
        ('liver', 'Печень'),
        ('stomach', 'Желудок'),
        ('large_intestine', 'Толстый кишечник'),
        ('small_intestine', 'Тонкий кишечник'),
        ('oral_cavity', 'Ротовая полость'),

        # Половая система

        ('testicles', 'Тестикулы'),
        ('prostate', 'Простата'),
        ('hormonal', 'Гормональная система'),
        ('function', 'Функциональность'),

        # Остальные системы и состояния (из конца JSON)

    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='human', verbose_name="Роль")
    which_animal = models.CharField(
        max_length=20,
        choices=ANIMAL_CHOICES,
        blank=True,
        null=True,
        verbose_name="Вид животного"
    )

    system = models.CharField(
        max_length=50,
        choices=SYSTEM_CHOICES,
        default='others',
        verbose_name="Система"
    )

    subsection = models.CharField(
        max_length=50,
        choices=SUBSECTION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Подсистема"
    )

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    example_answer = models.TextField(
        blank=True,
        verbose_name="Пример ответа"  # Правильный падеж
    )


    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"

    def save(self, *args, **kwargs):
        # Если роль не животное, сбрасываем вид животного в None
        if self.role in ['human', 'baby']:
            self.which_animal = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.system})"
# 4. Вопрос
class Question(models.Model):
    # Типы вопросов как на картинке
    TYPE_CHOICES = [
        ('slider', 'Слайдер (Плохо - Хорошо)'),
        ('binary', 'Да/Нет'),
        ('radio', 'Несколько вариантов'),
        ('text', 'Текстовый ответ (Поле ввода)'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name="Текст вопроса")
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='radio')




    def __str__(self):
        return self.text


class Notification(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='notification', verbose_name="Профиль"
    )
    notification_name = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    check_is = models.BooleanField(default=False)

    def __str__(self):
        return self.profile.name
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255, verbose_name="Вариант ответа",null=True,blank=True)


    def __str__(self):
        return self.text
#asd
@environmental_risk_decorator
@update_life_expectancy_decorator
@health_recommendations_start_decorator
class Profile(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram_id = models.IntegerField(default=0, null=True, blank=True)
    name=models.CharField(max_length=200,null=True,blank=True,default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True,default=None)
    middle_name=models.CharField(max_length=200, null=True, blank=True,default=None)
    nickname=models.CharField(max_length=200, null=True, blank=True,default=None)
    gender=models.CharField(max_length=200, null=True, blank=True,default=None)
    place_of_residence=models.CharField(max_length=200, null=True, blank=True,default=None)
    date_birth=models.DateField(null=True,blank=True,default=None)

    photo = models.ImageField(
        upload_to='pictures/',
        validators=[validate_face_photo],  # <-- АВТОМАЧЕСКИ РАБОТАЕТ В DRF
        null=True,
        blank=True
    )
    balance=models.IntegerField(default=0)
    health_system=models.JSONField(null=True,default=None)
    life_expectancy=models.IntegerField(null=True,default=None,blank=True)
    family_ref = models.UUIDField(default=uuid.uuid4, unique=True)
    ref = models.UUIDField(default=uuid.uuid4, unique=True)
    height=models.IntegerField(default=0,blank=True)
    weight = models.FloatField(default=0, blank=True)
    previous_health_system = models.JSONField(null=True, default=None)
    medical_history = models.JSONField(default=dict, blank=True, verbose_name="Медицинская карта")
    family = models.ForeignKey("Profile", on_delete=models.CASCADE,
                                               related_name='family_family',
                                               null=True, blank=True)
    recommended_by_partner = models.ForeignKey("Profile", on_delete=models.CASCADE,
                                               related_name='ref_system',
                                               null=True, blank=True)
    recommended_by_family = models.ForeignKey("Profile", on_delete=models.CASCADE,
                                               related_name='ref_system_family',
                                               null=True, blank=True)

    who_is = models.CharField(max_length=150,null=True, blank=True, default=None)
    IK = models.FloatField(null=True,blank=True)
    timezone = models.CharField(max_length=50, null=True,blank=True)
    water_goal=models.FloatField(default=0)

    life_expectancy_json=models.TextField(null=True,default=None)
    health_recommendations=models.TextField(null=True,default=None)
    risk_test=models.TextField(null=True,default=None)

    pressure_test = models.TextField(null=True, default=None)


    pressure_plus=models.TextField(null=True,default=None)
    diary_plus=models.TextField(null=True,default=None)

    analysis_risk=models.TextField(null=True,default=None)
    notification_drugs=models.BooleanField(default=True)
    notification_health = models.BooleanField(default=True)
    notification_calories = models.BooleanField(default=True)
    notification_habit = models.BooleanField(default=True)
    notification_female=models.BooleanField(default=True)
    food_percentage=models.FloatField(default=100)
    generated_avatars = models.JSONField(default=list, blank=True)
    system_avatars = models.JSONField(default=list, blank=True)

    is_pregnant = models.BooleanField(
        default=False,
        verbose_name="Беременность"
    )

    pregnancy_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата начала беременности"
    )



    #половая систем male








    #Overall_tone=models.IntegerField(default=0)


    def __str__(self):
        return self.name


class ChildHealthAnalysisProfile(models.Model):
    """
    Модель анализа и рекомендаций для ребёнка, привязанная к Profile через OneToOneField.
    """
    profile = models.OneToOneField(
        'Profile',
        on_delete=models.CASCADE,
        related_name="child_health_analysis",
    )
    anaylis_chilld = models.TextField(
        verbose_name="Анализ и рекомендации для ребенка",
    )
    created_at = models.DateField(
        auto_now=True,
        verbose_name="Дата создания",
    )

    def __str__(self):
        return f"Анализ здоровья ребенка для профиля {self.profile_id}"



class GeneralHealthReportProfile(models.Model):
    """
    OneToOne модель только для 4 текстовых блоков ИИ
    на странице 'Сводка состояния здоровья на основе всех шкал'.
    """
    profile = models.OneToOneField(
        'Profile',
        on_delete=models.CASCADE,
        related_name='general_health_report',
        verbose_name="Профиль"
    )

    brief_summary = models.TextField(blank=True, null=True)
    dynamics_analysis = models.TextField(blank=True, null=True)
    norms_comparison = models.TextField(blank=True, null=True)
    personal_recommendations = models.TextField(blank=True, null=True)

    # MD5-отпечаток данных, чтобы не вызывать ИИ без изменений
    data_hash = models.CharField(max_length=64, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Сводка по шкалам для {self.profile}"


class ChildIllnessReport(models.Model):
    """
        Блок опроса 'Ребёнку нездоровится'.
        """
    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name="illness_surveys",
    )
    # Основные жалобы (множественный выбор)
    main_complaints = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Основные жалобы",
    )
    started_at = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Когда началось",
    )
    # Интенсивность (множественный выбор списком)
    intensity = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Интенсивность",
    )
    # Фото или файл
    file_attachment = models.FileField(
        upload_to="illness_files/",
        blank=True,
        null=True,
        verbose_name="Фото или файл",
    )
    # Что уже предприняли (просто текстовое поле)
    actions_taken = models.TextField(
        blank=True,
        null=True,
        verbose_name="Что уже предприняли",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    def __str__(self):
        return f"Опрос от {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class ChildCalendarEvent(models.Model):
    EVENT_TYPES = (
        ('vaccine', 'Прививка'),       # Синяя отметка в календаре
        ('checkup', 'Осмотр'),         # Зеленая отметка в календаре
    )

    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name="child_calendar_events",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        verbose_name="Тип события",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название прививки или направление врача",
    )
    description = models.TextField(
        verbose_name="Описание, зачем нужно",
    )
    scheduled_date = models.DateField(
        verbose_name="Назначенная дата",
    )

    # Статус прохождения ("Прививка пройдена" / "Осмотр пройден")
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Пройдено",
    )
    completed_at = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата фактического прохождения",
    )

    # Поля для Осмотра (комментарий родителя и файл при прохождении)
    parent_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий родителя (результаты осмотра)",
    )
    file_attachment = models.FileField(
        upload_to="checkup_files/",
        blank=True,
        null=True,
        verbose_name="Фото или файл осмотра",
    )

    # Поля для Реакции на прививку (темно-зеленая отметка в календаре)
    reaction_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание реакции на прививку",
    )
    reaction_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Дата фиксации реакции",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'id']

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title} ({self.scheduled_date})"

class ChildMeasurement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает заполнения'),
        ('completed', 'Заполнено'),
        ('missed', 'Данные не внесены'),
    ]

    child = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='measurements')
    scheduled_date = models.DateField(verbose_name="Запланированная дата")
    actual_date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )

    # === JSON ПОЛЯ С DEFAULT=DICT ===
    physical_development = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Физическое развитие"
    )
    vital_signs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Витальные показатели"
    )
    regime_and_behavior = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Режим и поведение"
    )

    created_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date']

class MenHealthProfile(models.Model):
    """Модель для хранения AI-анализа мужского здоровья."""

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="men_health",
    )
    hormone_profile = models.TextField(
        verbose_name="Гормональный профиль",

    )
    hormone_function = models.TextField(
        verbose_name="Функциональность половой системы",

    )
    hormone_prostate = models.TextField(
        verbose_name="Состояние простаты и онкориски",

    )
    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Men's Health Profile for Profile #{self.profile}"

class FemaleHealthProfile(models.Model):


    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="female_health",
    )
    report = models.TextField(
        verbose_name="Отчет профиль",

    )
    recommendation = models.TextField(
        verbose_name="Рекомендация ",

    )


    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Female Health Profile for Profile #{self.profile}"

class NotificationFemale(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notificationfemale')
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateField()
    three_days_before = models.BooleanField(default=False)

    def __str__(self):
        return self.profile

class CyclePeriod(models.Model):

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='periods')
    start_date = models.DateField(verbose_name="Дата начала")

    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Период менструации"
        verbose_name_plural = "Периоды менструаций"



    def __str__(self):
        return f"{self.profile} | {self.start_date} — {self.end_date or 'по н.в.'}"


class DailyLog(models.Model):

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='daily_logs')
    created_at = models.DateField(verbose_name="Дата записи")
    note = models.TextField(blank=True, verbose_name="Текстовая заметка")
    pain = models.JSONField(default=dict)
    mood = models.JSONField(default=dict)
    activities = models.JSONField(default=dict)
    pregnancy = models.JSONField(default=dict)



    class Meta:
        # Одна запись на одного пользователя в один день
        unique_together = ['profile', 'created_at']
        ordering = ['-created_at']

    def __str__(self):
        return f"Заметка {self.profile} от {self.created_at}"


class Critical_analysis(models.Model):
    SYSTEM_CHOICES = [
        ('reproductive', 'Половая система - мужчина'),
    ]
    SUBSECTION_CHOICES = [
        ('critical_tests', 'Критические анализы'),
    ]
    system = models.CharField(
        max_length=50,
        choices=SYSTEM_CHOICES,
        default='others',
        verbose_name="Система"
    )

    sub_section = models.CharField(
        max_length=50,
        choices=SUBSECTION_CHOICES,
        default='others',
        verbose_name="Подсистема"
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    example_answer = models.TextField(
        blank=True,
        verbose_name="Пример ответа"  # Правильный падеж
    )

    def __str__(self):
        return self.title

    class Meta:

        verbose_name="Тесты Kритические анализы"
        verbose_name_plural = "Тесты Kритические анализы"





class Question_critical(models.Model):
    # Типы вопросов как на картинке
    TYPE_CHOICES = [
        ('slider', 'Слайдер (Плохо - Хорошо)'),
        ('binary', 'Да/Нет'),
        ('radio', 'Несколько вариантов'),
        ('text', 'Текстовый ответ (Поле ввода)'),
    ]

    test = models.ForeignKey(Critical_analysis, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500, verbose_name="Текст вопроса")
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='radio')




    def __str__(self):
        return self.text
class Choice_critical(models.Model):
    question = models.ForeignKey(Question_critical, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255, verbose_name="Вариант ответа",null=True,blank=True)


    def __str__(self):
        return self.text

@update_life_expectancy_decorator
class Habit(models.Model):
    profile=models.ForeignKey(
            'Profile', on_delete=models.CASCADE, related_name='habit', verbose_name="Профиль"
        )
    name_habit=models.CharField(max_length=200)
    lenght=models.CharField(max_length=200)
    type = models.CharField(max_length=50, null=True, blank=True)


    def __str__(self):
        return self.name_habit


class Tracking_Habit(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='tracking', verbose_name="Профиль"
    )
    habit=models.ForeignKey('Habit',on_delete=models.CASCADE, related_name='habit_tracking')
    created_at=models.DateField()
    check_is=models.BooleanField(null=True, default=None)



    def __str__(self):
        return self.profile.name


class Categories_Quest(models.Model):
    name=models.CharField(max_length=200,null=True,blank=True,default=None)


    def __str__(self):
        return self.name


class Quest(models.Model):
    profile = models.ForeignKey(
            'Profile', on_delete=models.CASCADE, related_name='quest', verbose_name="Профиль"
        )
    tests=models.ForeignKey(Categories_Quest,on_delete=models.CASCADE)
    created_at=models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        Profile.objects.filter(id=self.profile.pk).update(balance=F('balance') + 150)  # ✅ Fast
        super().save(*args, **kwargs)

@pet_risk_analysis_decorator(fields_to_track=['message'])
class Tests_Pet(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='tests_pet', verbose_name="Профиль"
    )
    name = models.CharField(max_length=200, db_index=True)
    read = models.BooleanField(default=False)
    message = models.TextField(null=True, default=None)
    created_at = models.DateField(auto_now_add=True)

@health_recommendations_decorator
@update_life_expectancy_decorator
@monthly_report_only_tests_decorator
class Tests(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='tests', verbose_name="Профиль"
    )
    name = models.CharField(max_length=200, db_index=True)
    read = models.BooleanField(default=False)
    message = models.TextField(null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
@update_life_expectancy_decorator
class BloodPressure(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='pressure_history', verbose_name="Профиль"
    )
    pressure_top = models.PositiveIntegerField(verbose_name="Систолическое (верхнее)")
    pressure_bottom = models.PositiveIntegerField(verbose_name="Диастолическое (нижнее)")
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.name}: {self.systolic}/{self.diastolic}"

    class Meta:
        verbose_name = "Давление"
        verbose_name_plural = "История давления"
@monthly_report_only_tests_decorator
class Chat(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='chat', verbose_name="Профиль"
    )
    question=models.TextField(null=True, default=None)
    answer=models.TextField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.profile.name


class PetShare(models.Model):
    profile = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='shared_pets_links', verbose_name="Кто добавил питомца")
    pet = models.ForeignKey("Pet", on_delete=models.CASCADE, related_name='shared_profiles_links', verbose_name="Привязанный питомец")
    #created_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'pet') # Защита, чтобы нельзя было добавить одного питомца дважды
        verbose_name = "Совместный доступ к питомцу"
        verbose_name_plural = "Совместный доступ к питомцам"
class Notification_Pet_drugs(models.Model):
    # Specific time of day to take the drug
    time = models.CharField(max_length=255)
    drugs = models.ForeignKey(
        "Pet_Drugs", on_delete=models.CASCADE, related_name="notifications_pet_drugs"
    )

    def __str__(self):
        return f"{self.drugs.name} at {self.time}"
class Pet_Drugs(models.Model):
    pet = models.ForeignKey(
        "Pet", on_delete=models.CASCADE, related_name='pet_drugs', verbose_name="Питомец"
    )
    catigories = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    time_day = models.IntegerField()
    day = models.IntegerField()
    intake = models.CharField(max_length=200)
    interval = models.DurationField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.interval = timedelta(days=self.time_day)
        super().save(*args, **kwargs)


class Pet_Check_Drugs(models.Model):
    created_at=models.DateField(auto_now_add=True)
    notification = models.ForeignKey(
        Notification_Pet_drugs, on_delete=models.CASCADE, related_name='checks'
    )

    date = models.DateField(auto_now_add=True,null=True)
    is_taken = models.BooleanField(default=True)

    class Meta:
        unique_together = ('notification', 'date')

    def __str__(self):
        return f"{self.notification} taken on {self.date}"

class Notification_drugs(models.Model):
    # Specific time of day to take the drug
    time = models.CharField(max_length=255)
    drugs = models.ForeignKey(
        "Drugs", on_delete=models.CASCADE, related_name="notifications_drugs"
    )

    def __str__(self):
        return f"{self.drugs.name} at {self.time}"


class Drugs(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='drugs', verbose_name="Профиль"
    )
    catigories=models.CharField(max_length=200)
    name=models.CharField(max_length=200)
    time_day=models.IntegerField()
    day=models.IntegerField()
    intake=models.CharField(max_length=200)
    interval=models.DurationField(null=True,blank=True)

    created_at=models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.interval=timedelta(days=self.time_day)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.profile.name


class Check_Drugs(models.Model):

    notification = models.ForeignKey(
        Notification_drugs, on_delete=models.CASCADE, related_name='checks'
    )

    date = models.DateField(auto_now_add=True)
    is_taken = models.BooleanField(default=True)

    class Meta:

        unique_together = ('notification', 'date')

    def __str__(self):
        return f"{self.notification} taken on {self.date}"


class Daily_check(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='daily_check', verbose_name="Профиль"
    )
    message=models.TextField(null=True, default=None)
    created_at = models.DateField(auto_now_add=True,null=True)


    def __str__(self):
        return self.profile.name


class PetDaily_check(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='pet_daily_check', verbose_name="Питомец"
    )
    message=models.TextField(null=True, default=None)
    created_at = models.DateField(auto_now_add=True,null=True)


class PetRentgen(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='rentgen_pet', verbose_name="Питомец"
    )
    message=models.TextField(null=False, default="")
    answer = models.TextField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)


class PetRentgen_Image(models.Model):
    rentgen = models.ForeignKey(
        'PetRentgen', on_delete=models.CASCADE, related_name='rentgen_image', verbose_name="Rentgen"
    )
    images=models.ImageField(upload_to='rentgen/',default=None)




@health_recommendations_decorator
class Rentgen(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='rentgen', verbose_name="Профиль"
    )
    message=models.TextField(null=False, default="")
    answer = models.TextField(null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.profile.name

class Rentgen_Image(models.Model):
    rentgen = models.ForeignKey(
        'Rentgen', on_delete=models.CASCADE, related_name='rentgen_image', verbose_name="Rentgen"
    )
    images=models.FileField(upload_to='rentgen/',default=None)


    def __str__(self):
        return self.rentgen.profile.name
@pet_risk_analysis_decorator(fields_to_track=['gender', 'health_system','age','pet','medical_history'])
class Pet(models.Model):
    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name='pet',
        verbose_name="Профиль"
    )
    klichka=models.CharField(max_length=200)
    pet=models.CharField(max_length=200)
    age = models.DateField(null=True, blank=True)
    photo = models.ImageField(blank=True, upload_to='pictures/')
    gender = models.CharField(max_length=200, null=True, blank=True, default=None)
    health_system = models.JSONField(null=True, default=None)
    risk_test=models.TextField(null=True,default=None)
    analysis_risk = models.TextField(null=True, default=None)
    pet_family_ref = models.UUIDField(default=uuid.uuid4,unique=True,blank=True)
    medical_history = models.JSONField(default=dict, blank=True, verbose_name="Медицинская карта")
    food_percentage = models.FloatField(default=100)


    def __str__(self):
        return self.klichka


class NutritionGoalPet(models.Model):
    pet = models.OneToOneField(
        'Pet', on_delete=models.CASCADE, related_name='nutrition_goal_pet'
    )
    calories = models.PositiveIntegerField(default=0)
    proteins = models.PositiveIntegerField(default=0)
    fats = models.PositiveIntegerField(default=0)
    carbs = models.PositiveIntegerField(default=0)
    fiber = models.PositiveIntegerField(default=0)
    vitamin=models.PositiveIntegerField(default=0)
    mineral=models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Цели для {self.pet}"
class NutritionGoal(models.Model):
    profile = models.OneToOneField(
        'Profile', on_delete=models.CASCADE, related_name='nutrition_goal'
    )
    calories = models.PositiveIntegerField(default=0)
    proteins = models.PositiveIntegerField(default=0)
    fats = models.PositiveIntegerField(default=0)
    carbs = models.PositiveIntegerField(default=0)
    fiber = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Цели для {self.profile.name}"
@health_recommendations_decorator
class Calories(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='cal', verbose_name="Профиль"
    )
    created_at=models.DateTimeField(auto_now_add=True)
    detail=models.JSONField(null=True, default=None)
    total=models.JSONField(null=True, default=None)
    images = models.ImageField(upload_to='calories/', default=None,null=True)
    water_intake = models.FloatField(default=0, verbose_name="Выпито воды")


    saved=models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # 1. Сохраняем текущую запись
        super().save(*args, **kwargs)

        # 2. Проверяем только если запись подтверждена
        if self.saved:
            try:
                goal = self.profile.nutrition_goal
                today = timezone.now().date()

                # Считаем сумму калорий за СЕГОДНЯ
                # Предполагаем, что в JSONField 'total' калории лежат как {"calories": 500}
                # Мы пройдем по всем записям пользователя за сегодня
                todays_records = Calories.objects.filter(
                    profile=self.profile,
                    created_at__date=today,
                    saved=True
                )

                total_calories_today = 0
                for record in todays_records:
                    if record.total and isinstance(record.total, dict):
                        total_calories_today += record.total.get('ккал', 0)

                # 3. Сравниваем дневную сумму с целью
                if total_calories_today > goal.calories:
                    # Отправляем уведомление
                    async_task(
                        'backend.tasks.send_calorie_limit_warning',
                        self.profile.telegram_id
                    )

            except Exception as e:
                # Логируем ошибку, если что-то пошло не так (например, нет NutritionGoal)
                print(f"Error checking calories: {e}")


    def __str__(self):
        return self.profile.name


class CaloriesReportProfile(models.Model):
    """
    OneToOne модель для хранения готового ИИ-анализа питания за 30 дней (для PDF-отчёта).
    Обновляется при подтверждении приёма пищи (PATCH).
    """
    profile = models.OneToOneField(
        'Profile',
        on_delete=models.CASCADE,
        related_name='calories_report',
        verbose_name="Профиль"
    )
    diet_report = models.TextField(
        blank=True,
        null=True,
        verbose_name="Отчёт о вредности/полезности рациона"
    )
    general_recommendations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Общие рекомендации"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Отчёт питания для {self.profile}"
class PetCalories(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='pet_calories', verbose_name="Питомец"
    )
    created_at=models.DateTimeField(auto_now_add=True)
    detail=models.JSONField(null=True, default=None)
    total=models.JSONField(null=True, default=None)
    images = models.ImageField(upload_to='calories/', default=None,null=True)
    saved = models.BooleanField(default=False)





    def __str__(self):
        return self.pet.klichka

@pet_risk_analysis_decorator(fields_to_track=['question'])
class PetChat(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='chat', verbose_name="Питомец"
    )
    question=models.TextField(null=True, default=None)
    answer=models.TextField(null=True, default=None)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pet.klichka

class ConsultationSettings(models.Model):
    """
    Единые настройки консультаций в Django Admin (комиссия сервиса для всех врачей).
    """
    commission_percent = models.PositiveIntegerField(
        default=30,
        verbose_name="Единая комиссия сервиса (%)"
    )

    class Meta:
        verbose_name = "Настройки комиссии сервиса"
        verbose_name_plural = "Настройки комиссии сервиса"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_commission(cls) -> int:
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'commission_percent': 30})
        return obj.commission_percent

    def __str__(self):
        return f"Комиссия сервиса: {self.commission_percent}%"
class DoctorProfile(models.Model):
    """
    Отдельная независимая модель врача (идентификация строго по telegram_id).
    """
    telegram_id = models.BigIntegerField(
        unique=True,
        db_index=True,
        verbose_name="Telegram ID врача"
    )
    full_name = models.CharField(max_length=255, verbose_name="ФИО врача")
    photo = models.ImageField(
        upload_to='doctors/photos/',
        null=True,
        blank=True,
        verbose_name="Фотография"
    )
    specialization = models.CharField(max_length=200, verbose_name="Специализация (например: Терапевт)")
    short_description = models.TextField(blank=True, default="", verbose_name="Коротко о себе")
    education = models.TextField(blank=True, default="", verbose_name="Образование")
    qualification = models.CharField(max_length=255, blank=True, default="", verbose_name="Квалификация")
    practice_start_date = models.DateField(verbose_name="Дата начала медицинской практики")

    # Финансы и рейтинг
    consultation_price = models.PositiveIntegerField(
        default=1500,
        verbose_name="Стоимость консультации для клиента (₽)"
    )
    balance = models.PositiveIntegerField(
        default=0,
        verbose_name="Текущий баланс к выводу (₽)"
    )
    total_earned = models.PositiveIntegerField(
        default=0,
        verbose_name="Общий заработок за всё время (₽)"
    )
    rating = models.FloatField(default=5.0, verbose_name="Рейтинг")

    # Статусы
    is_online = models.BooleanField(default=False, verbose_name="Статус Online / Offline")
    is_active = models.BooleanField(default=True, verbose_name="Профиль активен (не отключен админом)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    @property
    def experience_years(self) -> int:
        if not self.practice_start_date:
            return 0
        today = date.today()
        years = today.year - self.practice_start_date.year - (
            (today.month, today.day) < (self.practice_start_date.month, self.practice_start_date.day)
        )
        return max(years, 0)

    @property
    def experience_display(self) -> str:
        y = self.experience_years
        if y % 10 == 1 and y % 100 != 11:
            word = "год"
        elif 2 <= y % 10 <= 4 and (y % 100 < 10 or y % 100 >= 20):
            word = "года"
        else:
            word = "лет"
        return f"{y} {word} стажа"

    @property
    def service_commission_percent(self) -> int:
        return ConsultationSettings.get_commission()

    @property
    def doctor_payout(self) -> int:
        comm = self.service_commission_percent
        return int(round(self.consultation_price * (100 - comm) / 100.0))

    def __str__(self):
        return f"{self.full_name} ({self.specialization}) [TG: {self.telegram_id}]"


class Consultation(models.Model):
    """
    Заявка / сессия онлайн-консультации между Пациентом (Profile) и Врачом (DoctorProfile).
    """
    STATUS_CHOICES = (
        ('waiting_payment', 'Ожидает оплаты'),
        ('active', 'Активна'),
        ('completed', 'Сессия завершена'),
        ('cancelled', 'Отменена'),
    )

    CALL_STATUS_CHOICES = (
        ('none', 'Нет звонка'),
        ('offered', 'Врач предложил звонок'),
        ('accepted', 'Звонок принят (идет разговор)'),
        ('declined', 'Пациент отклонил звонок'),
        ('ended', 'Звонок завершен'),
    )

    client = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name='client_consultations',
        verbose_name="Пациент"
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='doctor_consultations',
        verbose_name="Врач"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус"
    )

    # Первичное описание проблемы и файл от клиента (Скрин 2)
    initial_complaint = models.TextField(
        blank=True,
        default="",
        verbose_name="Краткое описание проблемы от пациента"
    )
    initial_file = models.FileField(
        upload_to='consultations/initial_files/',
        null=True,
        blank=True,
        verbose_name="Прикрепленный файл к проблеме (анализ/фото/документ)"
    )

    # Таймер консультации (30 минут с момента первого действия врача — Скрин 5)
    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="Длительность консультации (мин)"
    )
    timer_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время старта таймера (первый ответ врача)"
    )

    # Звонок LiveKit (Скрины 6 и 7)
    room_name = models.CharField(max_length=100, unique=True, editable=False)
    call_offered = models.BooleanField(default=False, verbose_name="Врач предложил звонок")
    call_status = models.CharField(
        max_length=20,
        choices=CALL_STATUS_CHOICES,
        default='none',
        verbose_name="Статус аудиозвонка"
    )

    # Финансы
    price_for_client = models.PositiveIntegerField(default=0, verbose_name="Цена для клиента (₽)")
    commission_percent = models.PositiveIntegerField(default=30, verbose_name="Комиссия сервиса (%)")
    doctor_earning = models.PositiveIntegerField(default=0, verbose_name="Доход врача с консультации (₽)")
    payment_method = models.CharField(max_length=50, blank=True, default="", verbose_name="Способ оплаты")
    is_paid = models.BooleanField(default=True, verbose_name="Оплачено")

    # Заключение врача после завершения (Скрин 8)
    doctor_conclusion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Заключение врача (Совет по улучшению состояния и Лекарства)"
    )
    conclusion_file = models.FileField(
        upload_to='consultations/conclusions/',
        blank=True,
        null=True,
        verbose_name="Файл с заключением"
    )
    needs_in_person_visit = models.BooleanField(
        default=False,
        verbose_name="Требуется ли очная встреча с врачом?"
    )

    # Оценка и отзыв от клиента после завершения (Скрин 9)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Оценка пациента (1-5 звезд)"
    )
    review_comment = models.TextField(
        blank=True,
        default="",
        verbose_name="Комментарий пациента к оценке"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"

    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"consult_{uuid.uuid4().hex[:12]}"
        if not self.pk and self.doctor:
            self.price_for_client = self.doctor.consultation_price
            self.commission_percent = self.doctor.service_commission_percent
            self.doctor_earning = self.doctor.doctor_payout
        super().save(*args, **kwargs)

    @property
    def remaining_seconds(self) -> int:
        """
        Сколько секунд осталось до конца 30-минутной консультации.
        Если врач ещё не ответил (timer_started_at is None), возвращает полные 1800 секунд (30:00).
        """
        total_sec = self.duration_minutes * 60
        if self.status == 'completed':
            return 0
        if not self.timer_started_at:
            return total_sec
        from django.utils import timezone
        elapsed = int((timezone.now() - self.timer_started_at).total_seconds())
        return max(total_sec - elapsed, 0)

    @property
    def remaining_time_display(self) -> str:
        """Формат для шапки чата: '29:48'"""
        sec = self.remaining_seconds
        mins = sec // 60
        rem_sec = sec % 60
        return f"{mins:02d}:{rem_sec:02d}"

    def start_timer_if_needed(self):
        """Запускает 30-минутный таймер при первом действии врача"""
        if not self.timer_started_at:
            from django.utils import timezone
            self.timer_started_at = timezone.now()
            self.save(update_fields=['timer_started_at'])

    def __str__(self):
        return f"Консультация #{self.id}: {self.doctor.full_name} — {self.client.name}"

class ConsultationMessage(models.Model):
    SENDER_CHOICES = (
        ('client', 'Пациент'),
        ('doctor', 'Врач'),
        ('system', 'Система'),
    )

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Консультация"
    )
    sender_role = models.CharField(max_length=15, choices=SENDER_CHOICES, verbose_name="Отправитель")
    text = models.TextField(blank=True, default="", verbose_name="Текст сообщения")
    file_attachment = models.FileField(
        upload_to='consultations/chat_files/',
        null=True,
        blank=True,
        verbose_name="Прикрепленный файл"
    )
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Сообщение консультации"
        verbose_name_plural = "Сообщения консультаций"


class DoctorWithdrawal(models.Model):
    """
    История операций по выводу средств врачом.
    """
    STATUS_CHOICES = (
        ('approved', 'Одобрено'),
        ('processing', 'В обработке'),
        ('rejected', 'Отклонено'),
    )

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='withdrawals',
        verbose_name="Врач"
    )
    amount = models.PositiveIntegerField(verbose_name="Сумма вывода (₽)")
    card_number = models.CharField(max_length=30, verbose_name="Номер банковской карты")
    cardholder_name = models.CharField(max_length=255, verbose_name="ФИО держателя карты (Получатель)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='approved',  # Для теста без платежки сразу ставим 'Одобрено'
        verbose_name="Статус операции"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата операции")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Вывод средств врача"
        verbose_name_plural = "История выводов средств врачей"

    @property
    def clean_digits(self) -> str:
        """Оставляет только цифры номера карты"""
        return "".join(ch for ch in (self.card_number or "") if ch.isdigit())

    @property
    def short_masked_card(self) -> str:
        """Формат для списка 'История вывода средств': '**** 4242'"""
        digits = self.clean_digits
        last4 = digits[-4:] if len(digits) >= 4 else digits
        return f"**** {last4}"

    @property
    def full_masked_card(self) -> str:
        """Формат для экрана 'Детали транзакции': '4276 3800 **** 4242'"""
        digits = self.clean_digits
        if len(digits) >= 16:
            return f"{digits[:4]} {digits[4:8]} **** {digits[-4:]}"
        elif len(digits) >= 4:
            return f"0000 0000 **** {digits[-4:]}"
        return self.card_number

    def __str__(self):
        return f"{self.doctor.full_name} — {self.amount} ₽ ({self.get_status_display()})"