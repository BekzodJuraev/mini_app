from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from datetime import date,timedelta
import uuid

class Profile(models.Model):
    username = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name=models.CharField(max_length=200,null=True,blank=True,default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True,default=None)
    middle_name=models.CharField(max_length=200, null=True, blank=True,default=None)
    nickname=models.CharField(max_length=200, null=True, blank=True,default=None)
    email=models.EmailField(null=True, blank=True,default=None)
    gender=models.CharField(max_length=200, null=True, blank=True,default=None)
    place_of_residence=models.CharField(max_length=200, null=True, blank=True,default=None)
    date_birth=models.DateField(null=True,blank=True,default=None)
    photo = models.CharField(max_length=200,blank=True)
    balance=models.IntegerField(default=0)
    health_system=models.JSONField(null=True,default=None)
    life_expectancy=models.IntegerField(null=True,default=None)
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

    #Overall_tone=models.IntegerField(default=0)


    def __str__(self):
        return self.name

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


    def __str__(self):
        return self.name_habit


class Tracking_Habit(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='tracking', verbose_name="Профиль"
    )
    habit=models.ForeignKey('Habit',on_delete=models.CASCADE, related_name='habit_tracking')
    created_at=models.DateField(auto_now_add=True)
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
class Drugs(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='drugs', verbose_name="Профиль"
    )
    catigories=models.CharField(max_length=200)
    name=models.CharField(max_length=200)
    time_day=models.IntegerField()
    day=models.IntegerField()
    intake=models.CharField(max_length=200)
    interval=models.DurationField(null=True,blank=True)
    notification=models.JSONField()
    created_at=models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.interval=timedelta(days=self.time_day)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.profile.name


class Check_Drugs(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='drugs_check', verbose_name="Профиль"
    )
    drugs=models.ForeignKey(
        'Drugs', on_delete=models.CASCADE, related_name='drugs_check', verbose_name="Drugs"
    )
    created_at=models.DateField(auto_now_add=True)

    def __str__(self):
        return self.profile.name


class Daily_check(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='daily_check', verbose_name="Профиль"
    )
    message=models.TextField(null=True, default=None)
    created_at = models.DateField(auto_now_add=True,null=True)


    def __str__(self):
        return self.profile.name

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
    images=models.ImageField(upload_to='rentgen/',default=None)


    def __str__(self):
        return self.rentgen.profile.name

class Pet(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='pet', verbose_name="Профиль"
    )
    klichka=models.CharField(max_length=200)
    pet=models.CharField(max_length=200)
    gender = models.CharField(max_length=200, null=True, blank=True, default=None)
    health_system = models.JSONField(null=True, default=None)


    def __str__(self):
        return self.profile.name


    # class RespiratorySystem(models.Model):
#     profile = models.OneToOneField(
#         'Profile', on_delete=models.CASCADE, related_name='res', verbose_name="Профиль"
#     )
#     lungs = models.IntegerField(default=0, verbose_name="Легкие")
#     trachea = models.IntegerField(default=0, verbose_name="Трахея")
#     nasopharynx = models.IntegerField(default=0, verbose_name="Носоглотка")
#     bronchi = models.IntegerField(default=0, verbose_name="Бронхи")
#     ribs = models.IntegerField(default=0, verbose_name="Рёбра")
#     diaphragm = models.IntegerField(default=0, verbose_name="Диафрагма")
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Дыхательная система"
#         verbose_name_plural = "Дыхательная система"
#
#     def __str__(self):
#         return self.profile.name
#
# class CardiovascularSystem(models.Model):
#     profile = models.OneToOneField('Profile', on_delete=models.CASCADE, related_name='cardi', verbose_name="Профиль")
#     pulse = models.IntegerField(default=0, verbose_name="Пульс")
#     systolic_pressure = models.IntegerField(default=0, verbose_name="Систолическое давление")
#     diastolic_pressure = models.IntegerField(default=0, verbose_name="Диастолическое давление")
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Сердечно-сосудистая система"
#         verbose_name_plural = "Сердечно-сосудистая система"
#
#     def __str__(self):
#         return self.profile.name
#
# class SkeletalMuscleSystem(models.Model):
#     profile = models.OneToOneField('Profile', on_delete=models.CASCADE, related_name='skelet', verbose_name="Профиль")
#     skeleton = models.IntegerField(default=0, verbose_name="Скелет")
#     muscles = models.IntegerField(default=0, verbose_name="Мышцы")
#     protection = models.IntegerField(default=0, verbose_name="Защита")
#     joint_flexibility = models.IntegerField(default=0, verbose_name="Гибкость суставов")
#     shock_absorption = models.IntegerField(default=0, verbose_name="Амортизация")
#     spine = models.IntegerField(default=0, verbose_name="Позвоночник")
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Опорно-двигательная система"
#         verbose_name_plural = "Опорно-двигательная система"
#
#     def __str__(self):
#         return self.profile.name
#
# class EndocrineSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='endoc',
#         verbose_name="Профиль"
#     )
#     thyroid_gland = models.IntegerField(default=0, verbose_name="Щитовидная железа")
#     pineal_gland = models.IntegerField(default=0, verbose_name="Шишковидная железа")
#     adrenal_glands = models.IntegerField(default=0, verbose_name="Надпочечники")
#     pancreas = models.IntegerField(default=0, verbose_name="Поджелудочная железа")
#     thymus = models.IntegerField(default=0, verbose_name="Вилочковая железа")
#     sex_gland = models.IntegerField(default=0, verbose_name="Половые железы")
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Эндокринная система"
#         verbose_name_plural = "Эндокринные системы"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class ImmuneSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='immune',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Иммунная система"
#         verbose_name_plural = "Иммунные системы"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class DigestiveSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='digestive',
#         verbose_name="Профиль"
#     )
#     esophagus = models.IntegerField(default=0, verbose_name="Пищевод")
#     liver = models.IntegerField(default=0, verbose_name="Печень")
#     stomach = models.IntegerField(default=0, verbose_name="Желудок")
#     large_intestine = models.IntegerField(default=0, verbose_name="Толстый кишечник")
#     small_intestine = models.IntegerField(default=0, verbose_name="Тонкий кишечник")
#     oral_cavity = models.IntegerField(default=0, verbose_name="Ротовая полость")
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Пищеварительная система"
#         verbose_name_plural = "Пищеварительные системы"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class ExcretorySystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='excretor',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Выделительная система"
#         verbose_name_plural = "Выделительные системы"
#
#     def __str__(self):
#         return self.profile.name
#
# class DentalJawSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='dental',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Зубочелюстная система"
#         verbose_name_plural = "Зубочелюстные системы"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class SensorySystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='sensor',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Сенсорная система"
#         verbose_name_plural = "Сенсорные системы"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class HematopoieticMetabolicSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='hemato',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Кроветворение и обмен"
#         verbose_name_plural = "Кроветворение и обмен"
#
#     def __str__(self):
#         return self.profile.name
#
#
# class MentalHealthSystem(models.Model):
#     profile = models.OneToOneField(
#         Profile,
#         on_delete=models.CASCADE,
#         related_name='mental',
#         verbose_name="Профиль"
#     )
#     total_rank = models.IntegerField(default=0, verbose_name="Общий рейтинг")
#
#     class Meta:
#         verbose_name = "Психическое здоровье"
#         verbose_name_plural = "Психическое здоровье"
#
#     def __str__(self):
#         return self.profile.name
