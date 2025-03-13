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

    def __str__(self):
        return self.name

