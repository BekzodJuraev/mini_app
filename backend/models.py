from django.db import models
from django.contrib.auth.models import User


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
    photo = models.ImageField(blank=True,upload_to='pictures/')
    balance=models.IntegerField(default=0)
    health_system=models.JSONField(null=True,default=None)
    #Overall_tone=models.IntegerField(default=0)

    def __str__(self):
        return self.name


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
