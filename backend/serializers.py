from rest_framework import serializers
from .models import Profile\
    #,DigestiveSystem,DentalJawSystem,EndocrineSystem,CardiovascularSystem,MentalHealthSystem,ImmuneSystem,RespiratorySystem,HematopoieticMetabolicSystem,SkeletalMuscleSystem,SensorySystem,ExcretorySystem
from django.contrib.auth.models import User
import openai
from concurrent.futures import ThreadPoolExecutor
import json
import time
from threading import Thread








openai.api_key = "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"
def get_health_scale(height, weight, smoking_now, smoking_past, location, gender, date_birth, exp_smoke):
    user_input = f"""
    Рост: {height}
    Вес: {weight}
    Пол: {gender}
    Дата рождения: {date_birth}
    Курите ли вы сейчас: {smoking_now}
    Курили ли вы раньше: {smoking_past}
    Стаж курения: {exp_smoke}
    Место проживания: {location}

    Оцени состояние по шкале от 1 до 10 для следующих категорий:

    - Общий тонус (Overall tone)
    - Дыхательная система (Respiratory System)
      - Легкие (Lungs)
      - Трахея (Trachea)
      - Носоглотка (Nasopharynx)
      - Бронхи (Bronchi)
      - Рёбра (Ribs)
      - Диафрагма (Diaphragm)
    - Сердечно-сосудистая система (Cardiovascular System)
      - Пульс (Pulse)
      - Систолическое давление (Systolic Pressure)
      - Диастолическое давление (Diastolic Pressure)
    - Опорно-двигательная система (Skeletal Muscle System)
      - Скелет (Skeleton)
      - Мышцы (Muscles)
      - Защита (Protection)
      - Гибкость суставов (Joint Flexibility)
      - Амортизация (Shock Absorption)
      - Позвоночник (Spine)
    - Эндокринная система (Endocrine System)
      - Щитовидная железа (Thyroid Gland)
      - Шишковидная железа (Pineal Gland)
      - Надпочечники (Adrenal Glands)
      - Поджелудочная железа (Pancreas)
      - Вилочковая железа (Thymus)
      - Половые железы (Sex Glands)
    - Иммунная система (Immune System)
    - Пищеварительная система (Digestive System)
      - Пищевод (Esophagus)
      - Печень (Liver)
      - Желудок (Stomach)
      - Толстый кишечник (Large Intestine)
      - Тонкий кишечник (Small Intestine)
      - Ротовая полость (Oral Cavity)
    - Выделительная система (Excretory System)
    - Зубочелюстная система (Dental Jaw System)
    - Сенсорная система (Sensory System)
    - Кроветворение и обмен (Hematopoietic Metabolic System)
    - Психическое здоровье (Mental Health System)

    Ответ должен быть ТОЛЬКО в формате JSON, например:
    {{
        "Общий тонус": 1,
        "Дыхательная система": {{
            "Легкие": 1,
            "Трахея": 1,
            "Носоглотка": 1,
            "Бронхи": 1,
            "Рёбра": 1,
            "Диафрагма": 1
        }},
        "Сердечно-сосудистая система": {{
            "Пульс": 1,
            "Систолическое давление": 1,
            "Диастолическое давление": 1
        }},
        "Опорно-двигательная система": {{
            "Скелет": 1,
            "Мышцы": 1,
            "Защита": 1,
            "Гибкость суставов": 1,
            "Амортизация": 1,
            "Позвоночник": 1
        }},
        "Эндокринная система": {{
            "Щитовидная железа": 1,
            "Шишковидная железа": 1,
            "Надпочечники": 1,
            "Поджелудочная железа": 1,
            "Вилочковая железа": 1,
            "Половые железы": 1
        }},
        "Иммунная система": 1,
        "Пищеварительная система": {{
            "Пищевод": 1,
            "Печень": 1,
            "Желудок": 1,
            "Толстый кишечник": 1,
            "Тонкий кишечник": 1,
            "Ротовая полость": 1
        }},
        "Выделительная система": 1,
        "Зубочелюстная система": 1,
        "Сенсорная система": 1,
        "Кроветворение и обмен": 1,
        "Психическое здоровье": 1
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты медицинский анализатор. Оцени состояние организма по шкале от 1 до 10."},
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

        def fetch_and_save_health(user):
            health_system = get_health_scale(
                height, weight, smoking_now=now_smoke, smoking_past=recent_smoke,
                location=place_of_residence, gender=gender, date_birth=date_birth, exp_smoke=exp_smoke
            )
            if isinstance(health_system, str):
                try:
                    health_system = json.loads(health_system)  # Convert JSON string to dictionary
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format returned from OpenAI API")
            user.profile.health_system = health_system
            user.profile.save()




        user = User.objects.create_user(username=username)
        profile = Profile.objects.create(username=user, **validated_data)
        Thread(target=fetch_and_save_health, args=(user,)).start()


        return user

class LoginSer(serializers.Serializer):
    telegram_id=serializers.CharField(required=True,write_only=True)

class ProfileSer(serializers.ModelSerializer):
    age=serializers.IntegerField()
    class Meta:
        model=Profile
        fields=['name','lastname','middle_name','gender','age','photo']



class ProfileUpdateSer(serializers.ModelSerializer):

    class Meta:
        model=Profile
        fields=['name','lastname','middle_name','gender','date_birth','photo','place_of_residence','email','nickname']
class ProfileMainSystemSer(serializers.ModelSerializer):
    # RespiratorySystem=RespiratorySystemSer(source='res')
    # CardiovascularSystem=CardiovascularSystemSer(source='cardi')
    # SkeletalMuscleSystem=SkeletalMuscleSystemSer(source='skelet')
    # EndocrineSystem=EndocrineSystemSer(source='endoc')
    # ImmuneSystem=ImmuneSystemSer(source='immune')
    # DigestiveSystem=DigestiveSystemSer(source='digestive')
    # ExcretorySystem=ExcretorySystemSer(source='excretor')
    # DentalJawSystem=DentalJawSystemSer(source='dental')
    # SensorySystem=SensorySystemSer(source='sensor')
    # HematopoieticMetabolicSystem=HematopoieticMetabolicSystemSer(source='hemato')
    # MentalHealthSystem=MentalHealthSystemSer(source='mental')

    class Meta:
        model=Profile
        #fields=['name','Overall_tone','RespiratorySystem','CardiovascularSystem','SkeletalMuscleSystem','EndocrineSystem','ImmuneSystem','DigestiveSystem','ExcretorySystem','DentalJawSystem','SensorySystem','HematopoieticMetabolicSystem','MentalHealthSystem']
        fields=['name','health_system']

# class ProfileHealthSystemSer(serializers.Serializer):
#     name=serializers.CharField()
#     Overall_tone=serializers.IntegerField()
#     RespiratorySystem_total=serializers.IntegerField()
#     CardiovascularSystem_total=serializers.IntegerField()
#     SkeletalMuscleSystem_total=serializers.IntegerField()
#     EndocrineSystem_total=serializers.IntegerField()
#     ImmuneSystem_total=serializers.IntegerField()
#     DigestiveSystem_total=serializers.IntegerField()
#     ExcretorySystem_total=serializers.IntegerField()
#     DentalJawSystem_total=serializers.IntegerField()
#     SensorySystem_total=serializers.IntegerField()
#     HematopoieticMetabolicSystem_total=serializers.IntegerField()
#     MentalHealthSystem_total=serializers.IntegerField()


# class RespiratorySystemSer(serializers.ModelSerializer):
#
#     class Meta:
#         model=RespiratorySystem
#         fields=['lungs','trachea','nasopharynx','bronchi','ribs','diaphragm','total_rank']
#
# class CardiovascularSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=CardiovascularSystem
#         fields=['pulse','systolic_pressure','diastolic_pressure','total_rank']
#
# class SkeletalMuscleSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=SkeletalMuscleSystem
#         fields=['skeleton','muscles','protection','joint_flexibility','shock_absorption','spine','total_rank']
#
# class EndocrineSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=EndocrineSystem
#         fields=['thyroid_gland','pineal_gland','adrenal_glands','pancreas','thymus','sex_gland','total_rank']
#
#
# class ImmuneSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=ImmuneSystem
#         fields=['total_rank']
# #
# class DigestiveSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=DigestiveSystem
#         fields=['esophagus','liver','stomach','large_intestine','small_intestine','oral_cavity','total_rank']
#
#
# class ExcretorySystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=ExcretorySystem
#         fields=['total_rank']
#
# class DentalJawSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=DentalJawSystem
#         fields=['total_rank']
#
# class SensorySystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=SensorySystem
#         fields=['total_rank']
#
# class HematopoieticMetabolicSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=HematopoieticMetabolicSystem
#         fields=['total_rank']
# class MentalHealthSystemSer(serializers.ModelSerializer):
#     class Meta:
#         model=MentalHealthSystem
#         fields=['total_rank']

