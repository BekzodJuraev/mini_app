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

class Calories(models.Model):
    profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='cal', verbose_name="Профиль"
    )
    created_at=models.DateField(auto_now_add=True)
    detail=models.JSONField(null=True, default=None)
    total=models.JSONField(null=True, default=None)


    def __str__(self):
        return self.profile.name

