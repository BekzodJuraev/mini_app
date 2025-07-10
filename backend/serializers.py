from rest_framework import serializers
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Tracking_Habit,Habit,Drugs,Rentgen,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs
    #,DigestiveSystem,DentalJawSystem,EndocrineSystem,CardiovascularSystem,MentalHealthSystem,ImmuneSystem,RespiratorySystem,HematopoieticMetabolicSystem,SkeletalMuscleSystem,SensorySystem,ExcretorySystem
from django.contrib.auth.models import User
import openai
from concurrent.futures import ThreadPoolExecutor
import json
import time
from threading import Thread
from .prompt import get_health_scale,get_health_scale_baby
import uuid

from rest_framework.authtoken.models import Token
class PublicNotifcationSer(serializers.ModelSerializer):
    telegram_id=serializers.CharField(source='profile__username__username')
    class Meta:
        model=Habit
        fields=['telegram_id']
class CaloriesChatSer(serializers.ModelSerializer):
    class Meta:
        model=Calories
        fields=['images','answer','created_at']




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
    exp_smoke = serializers.IntegerField(required=False)
    smoke_what = serializers.CharField(required=False)
    smoke_day = serializers.IntegerField(required=False)
    ref=serializers.UUIDField(required=False)
    ref_family=serializers.UUIDField(required=False)



    class Meta:
        model=User
        fields=['username','name','lastname','middle_name','gender','place_of_residence','date_birth','photo','recent_smoke','now_smoke','exp_smoke','height','weight','smoke_what','smoke_day','ref','ref_family']



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
        smoke_what=validated_data.pop('smoke_what',"")
        smoke_day=validated_data.pop('smoke_day',0)
        ref = validated_data.pop('ref', None)
        ref_family=validated_data.pop('ref_family',None)

        ik=0
        if now_smoke and exp_smoke and smoke_day:
            ik=(smoke_day * exp_smoke / 20)


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
        if ref:
            ref=Profile.objects.filter(ref=ref).first()
            profile = Profile.objects.create(username=user, recommended_by_partner=ref, **validated_data,IK=ik)
        elif ref_family:
            ref_family = Profile.objects.filter(family_ref=ref_family).first()
            profile = Profile.objects.create(username=user, recommended_by_family=ref_family,family=ref_family, **validated_data,IK=ik)
        else:
            profile = Profile.objects.create(username=user, **validated_data,IK=ik)

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
    smoke_what = serializers.CharField(required=False)
    smoke_day = serializers.IntegerField(required=False)




    class Meta:
        model=User
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
        smoke_what = validated_data.pop('smoke_what', "")
        smoke_day = validated_data.pop('smoke_day', 0)

        ik = 0
        if now_smoke and exp_smoke and smoke_day:
            ik = (smoke_day * exp_smoke / 20)


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
            user.profile.health_system = health_system
            user.profile.save(update_fields=['health_system'])


        user = User.objects.create_user(username=str(uuid.uuid4()))
        profile = Profile.objects.create(username=user, family=profile, **validated_data,IK=ik)

        Thread(target=fetch_and_save_health, args=(user,)).start()


        return user
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
        model=Profile
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
            user.profile.health_system = health_system
            user.profile.save(update_fields=['health_system'])

        user = User.objects.create_user(username=str(uuid.uuid4()))
        profile = Profile.objects.create(username=user, family=profile, **validated_data)

        Thread(target=fetch_and_save_health, args=(user,)).start()

        return user
class LoginSer(serializers.Serializer):
    telegram_id=serializers.CharField(required=True,write_only=True)

class ProfileSer(serializers.ModelSerializer):
    age=serializers.IntegerField()
    class Meta:
        model=Profile
        fields=['name','lastname','middle_name','gender','age','photo','life_expectancy','balance','IK']



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
    ik=serializers.FloatField(required=False)

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
    token=serializers.UUIDField()
    class Meta:
        model=Profile
        fields=['name','token','who_is']



class DrugsSer(serializers.ModelSerializer):
    class Meta:
        model=Drugs
        fields=['catigories','name','time_day','day','intake','notification']

class PetDrugSer(serializers.ModelSerializer):
    class Meta:
        model=Pet_Drugs
        fields=['catigories','name','time_day','day','intake','notification']


class GetPetDrugSer(serializers.ModelSerializer):
    end_day=serializers.DateField()
    status=serializers.BooleanField()
    class Meta:
        model=Pet_Drugs
        fields=['id','name','time_day','day','intake','notification','created_at','end_day','status']
class GetDrugSer(serializers.ModelSerializer):
    end_day=serializers.DateField()
    status=serializers.BooleanField()
    class Meta:
        model=Drugs
        fields=['id','name','time_day','day','intake','notification','created_at','end_day','status']

class DrugById(serializers.Serializer):
    id=serializers.IntegerField()

class RefGet(serializers.Serializer):
    total=serializers.IntegerField()
    ref = serializers.UUIDField()
    family_ref = serializers.UUIDField()


class DailyCheckSer(serializers.Serializer):
    feel_today=serializers.CharField()
    mood=serializers.CharField()
    appetite=serializers.CharField()
    physical=serializers.CharField()
    sleep=serializers.CharField()

class RentgenSer(serializers.Serializer):
    photo=serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        default=[]
    )
    message=serializers.CharField(default="")


class RentgenSerGet(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()



    class Meta:
        model=Rentgen
        fields=['message','answer','created_at','photo']

    def get_photo(self, obj):
        return [img.images.url for img in obj.rentgen_image.all()]
class PetSerCreate(serializers.Serializer):
    klichka=serializers.CharField()
    pet=serializers.CharField()
    poroda=serializers.CharField()
    age=serializers.CharField()
    disease=serializers.CharField()
    body=serializers.CharField()
    gender=serializers.CharField()

class PetSerGet(serializers.ModelSerializer):
    health = serializers.SerializerMethodField()


    class Meta:
        model=Pet
        fields=['id','klichka','pet','gender','health']

    def get_health(self, obj):
        return [obj.health_system]



class PetstyleSer(serializers.Serializer):
    dog_street=serializers.CharField()
    walk=serializers.CharField()
    time_walk=serializers.CharField()
    play_home=serializers.CharField()
    new_pet=serializers.CharField()
    jump=serializers.CharField()
    commands=serializers.CharField()
    fat=serializers.CharField()
    injury=serializers.CharField()
    l=serializers.CharField()


class PetEmotionSer(serializers.Serializer):
    avoid=serializers.CharField()
    run=serializers.CharField()
    cat_one=serializers.CharField()
    change=serializers.CharField()
    agressive=serializers.CharField()
    tremor=serializers.CharField()
    place=serializers.CharField()
    sleep=serializers.CharField()
    contact=serializers.CharField()
    fear=serializers.CharField()

class PetHabitSer(serializers.Serializer):
    apetit = serializers.CharField()
    vomit = serializers.CharField()
    change=serializers.CharField()
    smell = serializers.CharField()
    mochi = serializers.CharField()
    pee_problem = serializers.CharField()
    metorizm = serializers.CharField()
    predmet = serializers.CharField()
    vitamin = serializers.CharField()
    eat = serializers.CharField()

class PetCatEmotSer(serializers.Serializer):
    avoid = serializers.CharField()
    agressive = serializers.CharField()
    change = serializers.CharField()
    apatiya = serializers.CharField()
    sound = serializers.CharField()
    behaviour = serializers.CharField()
    place = serializers.CharField()
    fear = serializers.CharField()
    contact = serializers.CharField()
    adaption = serializers.CharField()
class PetCatSleepSer(serializers.Serializer):
    sleep_place = serializers.CharField()
    time_sleep = serializers.CharField()
    run = serializers.CharField()
    change_place = serializers.CharField()
    panic = serializers.CharField()
    tired = serializers.CharField()
    wake_up = serializers.CharField()
    dish = serializers.CharField()
    alone = serializers.CharField()
    behaviour = serializers.CharField()

class PetCatApetitSer(serializers.Serializer):
    apetit = serializers.CharField()
    vomit = serializers.CharField()
    color = serializers.CharField()
    allergy = serializers.CharField()
    dish = serializers.CharField()
    metorizm = serializers.CharField()
    ration = serializers.CharField()
    smell = serializers.CharField()
    interest = serializers.CharField()
    active = serializers.CharField()

class PetGrizunSer(serializers.Serializer):
    one = serializers.CharField()
    two = serializers.CharField()
    three = serializers.CharField()
    four = serializers.CharField()
    five = serializers.CharField()
    six = serializers.CharField()
    seven = serializers.CharField()
    eight = serializers.CharField()
    nine = serializers.CharField()
    ten = serializers.CharField()

class CaloriesSer(serializers.Serializer):
    photo=serializers.ImageField()
class GetCaloriesSer(serializers.Serializer):
    calories=serializers.IntegerField()
    belok=serializers.IntegerField()
    jir=serializers.IntegerField()
    uglevod=serializers.IntegerField()
    klechatka=serializers.IntegerField()

class PetGetCaloriesSer(serializers.Serializer):
    calories=serializers.IntegerField()
    belok=serializers.IntegerField()
    jir=serializers.IntegerField()
    uglevod=serializers.IntegerField()
    klechatka=serializers.IntegerField()
    vitamin = serializers.IntegerField()
    mineral = serializers.IntegerField()

class CaloriesListSer(serializers.ModelSerializer):

    #total = serializers.SerializerMethodField()
    foods=serializers.JSONField()

    class Meta:
        model=Calories
        fields=['created_at','foods']


    # def get_total(self, obj):
    #     return [obj.total]




class PetChatGet(serializers.ModelSerializer):

    class Meta:
        model=PetChat
        fields=['question','answer','created_at']