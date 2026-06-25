from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from datetime import date,timedelta
import uuid
from django_q.tasks import async_task
from django.db.models import Sum
from django.utils import timezone
from .update import update_life_expectancy_decorator,health_recommendations_decorator,environmental_risk_decorator,monthly_report_only_tests_decorator,pulse_diary_decorator,pet_risk_analysis_decorator,health_recommendations_start_decorator
from django.db import models

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
    text = models.CharField(max_length=255, verbose_name="Вариант ответа")


    def __str__(self):
        return self.text
@environmental_risk_decorator
@update_life_expectancy_decorator
@health_recommendations_start_decorator
class Profile(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram_id=models.IntegerField(default=0)
    name=models.CharField(max_length=200,null=True,blank=True,default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True,default=None)
    middle_name=models.CharField(max_length=200, null=True, blank=True,default=None)
    nickname=models.CharField(max_length=200, null=True, blank=True,default=None)
    gender=models.CharField(max_length=200, null=True, blank=True,default=None)
    place_of_residence=models.CharField(max_length=200, null=True, blank=True,default=None)
    date_birth=models.DateField(null=True,blank=True,default=None)
    photo = models.ImageField(blank=True, upload_to='pictures/')
    balance=models.IntegerField(default=0)
    health_system=models.JSONField(null=True,default=None)
    life_expectancy=models.IntegerField(null=True,default=None,blank=True)
    family_ref = models.UUIDField(default=uuid.uuid4, unique=True)
    ref = models.UUIDField(default=uuid.uuid4, unique=True)
    height=models.IntegerField(default=0,blank=True)
    weight = models.FloatField(default=0, blank=True)
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
    pressure_test=models.TextField(null=True,default=None)
    health_recommendations=models.TextField(null=True,default=None)
    risk_test=models.TextField(null=True,default=None)
    pressure_plus=models.TextField(null=True,default=None)
    diary_plus=models.TextField(null=True,default=None)
    analysis_risk=models.TextField(null=True,default=None)

    #Overall_tone=models.IntegerField(default=0)


    def __str__(self):
        return self.name
# class Calories(models.Model):
#

# class Relationship(models.Model):
#     profile = models.ForeignKey(
#         'Profile', on_delete=models.CASCADE, related_name='relationship', verbose_name="Профиль"
#     )
#     who_is=models.CharField(max_length=150)
#     name = models.CharField(max_length=200, null=True, blank=True, default=None)
#     lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
#     middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
#     gender = models.CharField(max_length=200, null=True, blank=True, default=None)
#     photo = models.ImageField(blank=True)
#     place_of_residence = models.CharField(max_length=200, null=True, blank=True, default=None)
#     date_birth = models.DateField(null=True, blank=True, default=None)
#     health_system = models.JSONField(null=True, default=None)

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
@pulse_diary_decorator
@update_life_expectancy_decorator
@monthly_report_only_tests_decorator
class Tests(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='tests', verbose_name="Профиль"
    )
    name = models.CharField(max_length=200, db_index=True)
    read = models.BooleanField(default=False)
    message = models.TextField(null=True, default=None)

    created_at = models.DateField(auto_now_add=True)
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
class Chat(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='chat', verbose_name="Профиль"
    )
    question=models.TextField(null=True, default=None)
    answer=models.TextField(null=True, default=None)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.profile.name

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
@pet_risk_analysis_decorator(fields_to_track=['gender', 'health_system','age','pet'])
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
    family_ref = models.UUIDField(default=uuid.uuid4,unique=True,blank=True)
    medical_history = models.JSONField(default=dict, blank=True, verbose_name="Медицинская карта")


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


