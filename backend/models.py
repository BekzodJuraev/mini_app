from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from datetime import date,timedelta
import uuid

from django.db import models

# 1. Система здоровья (например, Пищеварительная)
class Test(models.Model):
    ROLE_CHOICES = [
        ('human', 'Человек'),
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
        # Дыхательная
        ('lungs', 'Легкие'), ('trachea', 'Трахея'), ('nasopharynx', 'Носоглотка'),
        ('bronchi', 'Бронхи'), ('ribs', 'Рёбра'), ('diaphragm', 'Диафрагма'),
        # Сердечно-сосудистая
        ('pulse', 'Пульс'), ('systolic', 'Систолическое давление'), ('diastolic', 'Диастолическое давление'),
        # Опорно-двигательный
        ('skeleton', 'Скелет'), ('muscles', 'Мышцы'), ('spine', 'Позвоночник'),
        # Половая
        ('testicles', 'Тестикулы'), ('prostate', 'Простата'), ('hormonal', 'Гормональная система'),
        ('function', 'Функциональность'),
        # Пищеварительная
        ('esophagus', 'Пищевод'), ('liver', 'Печень'), ('stomach', 'Желудок'),
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


class Tests(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='tests', verbose_name="Профиль"
    )
    name = models.CharField(max_length=200, db_index=True)
    read = models.BooleanField(default=False)
    message = models.TextField(null=True, default=None)
    created_at = models.DateField(auto_now_add=True)
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
    drugs=models.ForeignKey(
        'Pet_Drugs', on_delete=models.CASCADE, related_name='pet_drugs_check', verbose_name="Drugs"
    )
    created_at=models.DateField(auto_now_add=True)

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

class Pet(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='pet', verbose_name="Профиль"
    )
    klichka=models.CharField(max_length=200)
    pet=models.CharField(max_length=200)
    photo = models.ImageField(blank=True, upload_to='pictures/')
    gender = models.CharField(max_length=200, null=True, blank=True, default=None)
    health_system = models.JSONField(null=True, default=None)


    def __str__(self):
        return self.profile.name


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
class Calories(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='cal', verbose_name="Профиль"
    )
    created_at=models.DateField(auto_now_add=True)
    detail=models.JSONField(null=True, default=None)
    total=models.JSONField(null=True, default=None)
    images = models.ImageField(upload_to='calories/', default=None,null=True)

    saved=models.BooleanField(default=False)


    def __str__(self):
        return self.profile.name

class PetCalories(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='pet_calories', verbose_name="Питомец"
    )
    created_at=models.DateField(auto_now_add=True)
    detail=models.JSONField(null=True, default=None)
    total=models.JSONField(null=True, default=None)
    images = models.ImageField(upload_to='calories/', default=None,null=True)
    saved = models.BooleanField(default=False)



    def __str__(self):
        return self.pet.klichka


class PetChat(models.Model):
    pet = models.ForeignKey(
        'Pet', on_delete=models.CASCADE, related_name='chat', verbose_name="Питомец"
    )
    question=models.TextField(null=True, default=None)
    answer=models.TextField(null=True, default=None)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pet.klichka


