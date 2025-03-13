from rest_framework import serializers
from .models import Profile
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    name=serializers.CharField()

    class Meta:
        model=User
        fields=['username','name']

    def create(self, validated_data):
        username=validated_data.pop('username')
        user = User.objects.create_user(username=username)
        profile = Profile.objects.create(username=user, **validated_data)

        return user

class LoginSer(serializers.Serializer):
    telegram_id=serializers.CharField(required=True,write_only=True)

