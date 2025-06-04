from rest_framework import serializers
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Tracking_Habit,Habit,Relationship,Drugs
    #,DigestiveSystem,DentalJawSystem,EndocrineSystem,CardiovascularSystem,MentalHealthSystem,ImmuneSystem,RespiratorySystem,HematopoieticMetabolicSystem,SkeletalMuscleSystem,SensorySystem,ExcretorySystem
from django.contrib.auth.models import User
import openai
from concurrent.futures import ThreadPoolExecutor
import json
import time
from threading import Thread
from .prompt import get_health_scale,get_health_scale_baby








class RegistrationSerializer(serializers.ModelSerializer):
    name=serializers.CharField()
    lastname=serializers.CharField()
    middle_name=serializers.CharField()
    gender=serializers.CharField()
    place_of_residence=serializers.CharField()
    date_birth=serializers.DateField()
    photo=serializers.CharField(required=False)
    height=serializers.IntegerField()
    weight=serializers.IntegerField()
    recent_smoke=serializers.CharField()
    now_smoke=serializers.CharField()
    exp_smoke=serializers.IntegerField(required=False)
    smoke_what=serializers.CharField()
    smoke_day=serializers.IntegerField(required=False)



    class Meta:
        model=User
        fields=['username','name','lastname','middle_name','gender','place_of_residence','date_birth','photo','recent_smoke','now_smoke','exp_smoke','height','weight','smoke_what','smoke_day']



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
        smoke_what=validated_data.pop('smoke_what')
        smoke_day=validated_data.pop('smoke_day')


        def fetch_and_save_health(user):
            health_system = get_health_scale(
                height, weight, smoking_now=now_smoke, smoking_past=recent_smoke,
                location=place_of_residence, gender=gender, date_birth=date_birth, exp_smoke=exp_smoke,smoke_what=smoke_what,smoke_day=smoke_day
            )
            #print(health_system)
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


class RelationshipSer(serializers.ModelSerializer):
    who_is=serializers.CharField()
    name = serializers.CharField()
    lastname = serializers.CharField()
    middle_name = serializers.CharField()
    gender = serializers.CharField()
    place_of_residence = serializers.CharField()
    date_birth = serializers.DateField()
    photo = serializers.CharField(required=False)
    height = serializers.IntegerField()
    weight = serializers.IntegerField()
    recent_smoke = serializers.CharField()
    now_smoke = serializers.CharField()
    exp_smoke = serializers.IntegerField(required=False)
    smoke_what = serializers.CharField()
    smoke_day = serializers.IntegerField(required=False)


    class Meta:
        model=Relationship
        fields=['who_is','name','lastname','middle_name','gender','place_of_residence','date_birth','photo','recent_smoke','now_smoke','exp_smoke','height','weight','smoke_what','smoke_day']



    def create(self, validated_data):
        profile = self.context['request'].user.profile
        recent_smoke=validated_data.pop('recent_smoke')
        who_is=validated_data.get('who_is')
        now_smoke=validated_data.pop('now_smoke')
        exp_smoke=validated_data.pop('exp_smoke',"")
        height=validated_data.pop('height')
        weight=validated_data.pop('weight')
        place_of_residence=validated_data.get('place_of_residence')
        gender=validated_data.get('gender')
        date_birth=validated_data.get('date_birth')
        smoke_what=validated_data.pop('smoke_what')
        smoke_day=validated_data.pop('smoke_day')


        def fetch_and_save_health(rel):
            health_system = get_health_scale(
                height, weight, smoking_now=now_smoke, smoking_past=recent_smoke,
                location=place_of_residence, gender=gender, date_birth=date_birth, exp_smoke=exp_smoke,smoke_what=smoke_what,smoke_day=smoke_day
            )
            #print(health_system)
            if isinstance(health_system, str):
                try:
                    health_system = json.loads(health_system)  # Convert JSON string to dictionary
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format returned from OpenAI API")
            rel.health_system = health_system
            rel.save(update_fields=['health_system'])

        rel=Relationship.objects.create(profile=profile,**validated_data)

        Thread(target=fetch_and_save_health, args=(rel,)).start()


        return rel
class RelationshipBabySer(serializers.ModelSerializer):
    who_is=serializers.CharField()
    name = serializers.CharField()
    gender = serializers.CharField()
    place_of_residence = serializers.CharField()
    date_birth = serializers.DateField()
    photo = serializers.CharField(required=False)
    height = serializers.IntegerField()
    weight = serializers.IntegerField()






    class Meta:
        model=Relationship
        fields=['who_is','name','gender','place_of_residence','date_birth','photo','height','weight']



    def create(self, validated_data):
        profile = self.context['request'].user.profile
        who_is=validated_data.get('who_is')
        height=validated_data.pop('height')
        weight=validated_data.pop('weight')
        place_of_residence=validated_data.get('place_of_residence')
        gender=validated_data.get('gender')
        date_birth=validated_data.get('date_birth')



        def fetch_and_save_health(rel):
            health_system = get_health_scale_baby(
                height=height, weight=weight,location=place_of_residence, gender=gender, date_birth=date_birth)

            if isinstance(health_system, str):
                try:
                    health_system = json.loads(health_system)  # Convert JSON string to dictionary
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format returned from OpenAI API")
            rel.health_system = health_system
            rel.save(update_fields=['health_system'])

        rel=Relationship.objects.create(profile=profile,**validated_data)

        Thread(target=fetch_and_save_health, args=(rel,)).start()


        return rel
class LoginSer(serializers.Serializer):
    telegram_id=serializers.CharField(required=True,write_only=True)

class ProfileSer(serializers.ModelSerializer):
    age=serializers.IntegerField()
    class Meta:
        model=Profile
        fields=['name','lastname','middle_name','gender','age','photo','life_expectancy','balance']



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



class ChatSer(serializers.Serializer):
    message=serializers.CharField()



class CrashTestSer(serializers.Serializer):
    smoke_day=serializers.IntegerField()
    exp_smoke=serializers.IntegerField()
    drop_smoke=serializers.CharField()
    alcohol_week=serializers.IntegerField()
    alcohol_litr=serializers.FloatField()
    drug_day=serializers.IntegerField()
    day_sleep=serializers.IntegerField()
    work=serializers.CharField()
    level_stress=serializers.CharField()
    habit=serializers.CharField()
    sex=serializers.CharField()
    environment=serializers.ListField(
        child=serializers.CharField()
    )
    food=serializers.CharField()

class SymptomsTestSer(serializers.Serializer):
    symptoms=serializers.ListField(
        child=serializers.CharField()
    )
    temp=serializers.IntegerField()
    covid=serializers.CharField()
    breath=serializers.IntegerField()
    cough=serializers.IntegerField()
    congestion=serializers.IntegerField()
    muscle=serializers.IntegerField()
    chest=serializers.IntegerField()
    headache=serializers.IntegerField()
    vomit=serializers.IntegerField()

class LifeStyleTestSer(serializers.Serializer):
    sleep=serializers.IntegerField()
    food=serializers.IntegerField()
    training=serializers.IntegerField()
    couple=serializers.CharField()
class HeartLestTestSer(serializers.Serializer):
    pulse=serializers.IntegerField()


class HeartBreathTestSer(serializers.Serializer):
    breathing=serializers.IntegerField()
    breathing_time=serializers.CharField()
class HeartGenchiTestSer(serializers.Serializer):
    breathing_time = serializers.CharField()
    sportsmen=serializers.CharField()


class HeartRufeTestSer(serializers.Serializer):
    pulse_main=serializers.IntegerField()
    pulse_first=serializers.IntegerField()
    pulse_second=serializers.IntegerField()

class HeartKotovaTestSer(serializers.Serializer):
    pulse_main=serializers.IntegerField()
    pressure_top=serializers.CharField()
    pressure_bottom=serializers.CharField()
    pulse_first = serializers.IntegerField()
    pulse_second = serializers.IntegerField()


class HeartMartineTestSer(serializers.Serializer):
    pulse_main=serializers.IntegerField()
    pressure_top = serializers.CharField()
    pressure_bottom = serializers.CharField()
    pulse_first = serializers.IntegerField()
    pulse_second = serializers.IntegerField()

class HeartKuperTestSer(serializers.Serializer):
    distance=serializers.FloatField()
class NotificationSer(serializers.ModelSerializer):
    class Meta:
        model=Tests
        fields=['id','name','created_at','read',]

class QuestSer(serializers.ModelSerializer):
    status=serializers.BooleanField(default=0)

    class Meta:
        model=Categories_Quest
        fields=['name','status']


class ChatGETSer(serializers.ModelSerializer):
    class Meta:
        model=Chat
        fields=['question','answer','created_at']


class HabitSer(serializers.ModelSerializer):
    class Meta:
        model=Habit
        fields=['name_habit','lenght']

class TrackingSer(serializers.Serializer):
    habit=serializers.CharField()
    check_is=serializers.BooleanField()


class GetHabitSer(serializers.ModelSerializer):
    habit=serializers.CharField(source='habit.name_habit')


    class Meta:
        model=Tracking_Habit
        fields=['habit','check_is','created_at']
class CountHabitSer(serializers.Serializer):
    habit=serializers.CharField(source='name_habit')
    day=serializers.IntegerField()


class GetRelationship(serializers.ModelSerializer):
    class Meta:
        model=Relationship
        fields=['name','id']

class GetRelationshipID(serializers.ModelSerializer):
    class Meta:
        model=Relationship
        fields=['who_is','name','health_system']

class DrugsSer(serializers.ModelSerializer):
    class Meta:
        model=Drugs
        fields=['catigories','name','time_day','day','intake','notification']

class GetDrugSer(serializers.ModelSerializer):
    end_day=serializers.DateField()
    status=serializers.BooleanField()
    class Meta:
        model=Drugs
        fields=['id','name','time_day','day','intake','notification','created_at','end_day','status']

class DrugById(serializers.Serializer):
    id=serializers.IntegerField()


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