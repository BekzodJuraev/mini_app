from rest_framework import serializers
from .models import Profile
from django.contrib.auth.models import User
import openai
openai.api_key = "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"
def get_health_scale(height, weight, smoking_now, smoking_past, location,gender,date_birth,exp_smoke):
    user_input = f"""
    Рост: {height}
    Вес: {weight}
    Пол:{gender}
    Дата рождения:{date_birth}
    Курите ли вы сейчас: {smoking_now}
    Курили вы раньше: {smoking_past}
    Укажите стаж курения:{exp_smoke}
    Место проживания: {location}

    Оцени состояние по шкале от 1 до 10 для следующих категорий:
    - Общий тонус
    - Система дыхания
    - Сердце и сосуды
    - Скелет и мышцы
    - Психика
    - Эндокринная система
    - Пищеварение

    Ответ должен быть только в JSON формате, например:
    {{
        "Общий тонус":1,
        "Система дыхания": 1,
        "Сердце и сосуды": 1,
        "Скелет и мышцы": 10,
        "Психика": 10,
        "Эндокринная система": 10,
        "Пищеварение": 10
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты медицинский анализатор. Оцени состояние по шкале от 1 до 10."},
            {"role": "user", "content": user_input}
        ]
    )

    return response["choices"][0]["message"]["content"]
class RegistrationSerializer(serializers.ModelSerializer):
    name=serializers.CharField()
    lastname=serializers.CharField()
    middle_name=serializers.CharField()
    gender=serializers.CharField()
    place_of_residence=serializers.CharField()
    date_birth=serializers.DateField()
    photo=serializers.ImageField()
    height=serializers.IntegerField()
    weight=serializers.IntegerField()
    recent_smoke=serializers.CharField()
    now_smoke=serializers.CharField()
    exp_smoke=serializers.IntegerField(required=False)



    class Meta:
        model=User
        fields=['username','name','lastname','middle_name','gender','place_of_residence','date_birth','photo','recent_smoke','now_smoke','exp_smoke','height','weight']

    def create(self, validated_data):
        username=validated_data.pop('username')
        recent_smoke=validated_data.pop('recent_smoke')
        now_smoke=validated_data.pop('now_smoke')
        exp_smoke=validated_data.pop('exp_smoke',"")
        height=validated_data.pop('height')
        weight=validated_data.pop('weight')
        place_of_residence=validated_data.get('place_of_residence')
        gender=validated_data.get('gender')
        date_birth=validated_data.get('date_birth')
        result=get_health_scale(height, weight, smoking_now=now_smoke, smoking_past=recent_smoke,location=place_of_residence,gender=gender,date_birth=date_birth,exp_smoke=exp_smoke)



        user = User.objects.create_user(username=username)
        profile = Profile.objects.create(username=user, **validated_data)

        return user

class LoginSer(serializers.Serializer):
    telegram_id=serializers.CharField(required=True,write_only=True)

