from rest_framework import serializers
from .models import Profile,Categories_Quest,Quest,Tests,Chat,Tracking_Habit,Habit,Drugs,Rentgen,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,Notification_drugs,NutritionGoal,Test,Question
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

class AIInputSer(serializers.Serializer):
    answers = serializers.JSONField()
class AdminTestByIDSer(serializers.ModelSerializer):
    # Твои поля
    question = serializers.SerializerMethodField()





    class Meta:
        model = Test
        fields = ['id', 'title','question']

    def get_question(self, obj):
        # Получаем вопросы, которые уже подгружены через prefetch_related
        return [
            {
                "text": q.text,
                "type": q.question_type,
                "type_display": q.get_question_type_display(),
                # Вкладываем choices прямо сюда
                "choices": [
                    {
                        "text": c.text,
                    } for c in q.choices.all() # choices подгружены заранее, запроса в БД не будет
                ]
            } for q in obj.questions.all()
        ]

class AdminTestsSer(serializers.ModelSerializer):

    role_display = serializers.ReadOnlyField(source='get_role_display')
    system_display = serializers.ReadOnlyField(source='get_system_display')
    subsection_display = serializers.ReadOnlyField(source='get_subsection_display')

    class Meta:
        model = Test
        fields = [
            'id',
            'role', 'role_display',
            'system', 'system_display',
            'subsection', 'subsection_display',
            'title', 'description'
        ]



class PublicNotificationPetDrugSer(serializers.ModelSerializer):
    telegram_id = serializers.CharField(source='pet.profile.username.username')
    city = serializers.CharField(source='pet.profile.place_of_residence')
    class Meta:
        model=Pet_Drugs
        fields=['telegram_id','catigories','name','time_day','day','intake','notification','city']
class PublicNotificationDrugSer(serializers.ModelSerializer):
    telegram_id = serializers.CharField(source='profile.username.username')
    city = serializers.CharField(source='profile.place_of_residence')
    notification=serializers.SerializerMethodField()

    class Meta:
        model=Drugs
        fields=['telegram_id','catigories','name','time_day','day','intake','city','notification']

    def get_notification(self, obj):
        # Достаем все уведомления, которые мы получили через prefetch_related
        # Используем .all(), чтобы Django не шел снова в базу
        notifications = obj.notifications_drugs.all()

        return [
            {

                "time": n.time
            }
            for n in notifications
        ]


class PublicNotifcationSer(serializers.ModelSerializer):
    telegram_id=serializers.CharField(source='profile__username__username')
    city=serializers.CharField(source='profile__place_of_residence')
    class Meta:
        model=Habit
        fields=['telegram_id','city']
class CaloriesChatSer(serializers.ModelSerializer):

    class Meta:
        model=Calories
        fields=['id','images','detail','total','created_at']

class SetResetPasswordSer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("The two password fields didn't match.")
        return data





class RegistrationFirstSer(serializers.ModelSerializer):
    login = serializers.CharField(source='username', required=True)
    password2 = serializers.CharField(write_only=True,required=True)
    email = serializers.EmailField(required=True)


    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Этот адрес электронной почты уже зарегистрирован. Пожалуйста, используйте другой."
            )
        return value

    def validate_login(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Это имя пользователя уже занято. Пожалуйста, выберите другое."
            )
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("The two password fields didn't match.")
        return data

    class Meta:
        model = User
        fields = ['login','email', 'password', 'password2']

    def create(self, validated_data):

        validated_data.pop('password2')

        user = User.objects.create_user(**validated_data)
        return user




class RegistrationSerializer(serializers.ModelSerializer):
    name=serializers.CharField()
    lastname=serializers.CharField()
    middle_name=serializers.CharField()
    gender=serializers.CharField()
    place_of_residence=serializers.CharField()
    date_birth=serializers.DateField()
    photo=serializers.ImageField(required=False)
    height=serializers.IntegerField()
    weight=serializers.IntegerField()
    recent_smoke=serializers.CharField()
    now_smoke=serializers.CharField()
    exp_smoke = serializers.IntegerField(required=False)
    smoke_what = serializers.CharField(required=False)
    smoke_day = serializers.IntegerField(required=False)
    ref=serializers.UUIDField(required=False)
    ref_family=serializers.UUIDField(required=False)
    telegram_id=serializers.IntegerField(required=True)




    class Meta:
        model=Profile
        fields=['telegram_id','name','lastname','middle_name','gender','place_of_residence','date_birth','photo','recent_smoke','now_smoke','exp_smoke','height','weight','smoke_what','smoke_day','ref','ref_family']



    def create(self, validated_data):
        user=validated_data.pop('user')
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




       # user = User.objects.create_user(username=username)
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
    who_is = serializers.CharField()
    name = serializers.CharField()
    date_birth = serializers.DateField()
    gender = serializers.CharField()
    # Поля с изображения 7
    blood_group = serializers.CharField(required=False, allow_blank=True)  # Группа крови
    rh_factor = serializers.CharField(required=False, allow_blank=True)  # Резус-фактор
    weight = serializers.FloatField()  # Укажите вес при рождении (кг)
    height = serializers.IntegerField()  # Укажите рост при рождении (см)
    gestation_period = serializers.IntegerField()  # Срок гестации (недели)
    birth_features = serializers.CharField(required=False, allow_blank=True)  # Особенности родов
    chronic_diseases = serializers.CharField(required=False, allow_blank=True)  # Хронические заболевания
    allergies = serializers.CharField(required=False, allow_blank=True)  # Аллергии
    operations = serializers.CharField(required=False, allow_blank=True)  # Перенесённые операции
    hereditary_diseases = serializers.CharField(required=False, allow_blank=True)  # Наследственные заболевания

    photo = serializers.ImageField(required=False)
    place_of_residence = serializers.CharField(required=False)






    class Meta:
        model=Profile
        fields=['who_is','name','gender','place_of_residence','date_birth','photo','height','weight','blood_group','rh_factor','gestation_period','birth_features'
                ,'chronic_diseases','allergies','operations','hereditary_diseases']



    def create(self, validated_data):
        profile = self.context['request'].user.profile
        who_is=validated_data.get('who_is')
        height=validated_data.pop('height')
        weight=validated_data.pop('weight')
        place_of_residence=validated_data.get('place_of_residence')
        gender=validated_data.get('gender')
        date_birth=validated_data.get('date_birth')

        gestation_period = validated_data.pop('gestation_period')# Срок гестации (недели)
        birth_features = validated_data.pop('birth_features') # Особенности родов
        chronic_diseases = validated_data.pop('chronic_diseases') # Хронические заболевания
        allergies = validated_data.pop('allergies')  # Аллергии
        operations = validated_data.pop('operations')  # Перенесённые операции
        hereditary_diseases = validated_data.pop('hereditary_diseases')
        blood_group = validated_data.pop('blood_group')
        rh_factor = validated_data.pop('rh_factor')




        def fetch_and_save_health(rel):
            health_system = get_health_scale_baby(
                height_birth=height, weight_birth=weight, gender=gender, date_birth=date_birth,

            gestation_period=gestation_period,birth_features=birth_features,chronic_diseases=chronic_diseases,allergies=allergies,operations=operations,
                hereditary_diseases=hereditary_diseases,blood_group=blood_group,rh_factor=rh_factor)

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
    #telegram_id=serializers.CharField(required=True,write_only=True)
    login=serializers.CharField(required=True)
    password=serializers.CharField(required=True)

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
class ProfileSer(serializers.ModelSerializer):
    age=serializers.IntegerField()


    class Meta:
        model=Profile
        fields=['name','lastname','middle_name','gender','age','photo','life_expectancy','balance','IK','place_of_residence','date_birth']



class ProfileUpdateSer(serializers.ModelSerializer):
    email=serializers.EmailField(source="username.email")
    login=serializers.CharField(source="username.username")

    class Meta:
        model=Profile
        fields=['login','name','lastname','middle_name','gender','date_birth','photo','place_of_residence','email','nickname']

    def update(self, instance, validated_data):

        # 1. Handle the nested user data
        # Use .pop() to separate user data from profile data
        user_data = validated_data.pop('username', None)

        if user_data:
            user_instance = instance.username  # This is the User object

            # Use getattr/setattr or dict.get() to avoid KeyErrors
            email = user_data.get('email', user_instance.email)
            login = user_data.get('username', user_instance.username)

            user_instance.email = email
            user_instance.username = login

            # If your business logic dictates that email must match username:
            # user_instance.username = email

            user_instance.save()

        # 2. Update the Profile instance with the remaining data
        # validated_data now only contains Profile fields (e.g., bio, avatar)
        return super().update(instance, validated_data)
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


class NutritionGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionGoal

        fields = ['calories', 'proteins', 'fats', 'carbs', 'fiber']



class ChatSer(serializers.Serializer):
    message=serializers.CharField()

class EditCaloriesSer(serializers.ModelSerializer):
    # Текстовая правка от пользователя (например: "добавь хлеб")
    message = serializers.CharField(required=False, allow_blank=True)
    # Текущий список блюд после ручных правок (удаление/изменение граммовки)
    current_details = serializers.ListField(child=serializers.JSONField(), required=False)

    class Meta:
        model = Calories
        # Оставляем только те поля, которые мы реально принимаем и отдаем
        fields = ['detail',  'message', 'current_details']
        read_only_fields = ['detail'] # Эти


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
    lenght=serializers.CharField(required=False)
    class Meta:
        model=Habit
        fields=['name_habit','lenght','type']

class TrackingSer(serializers.Serializer):
    habit=serializers.CharField()
    check_is=serializers.BooleanField()


class GetHabitSer(serializers.ModelSerializer):
    habit=serializers.CharField(source='habit.name_habit')
    type=serializers.CharField(source='habit.type')



    class Meta:
        model=Tracking_Habit
        fields=['habit','check_is','created_at','type']
class CountHabitSer(serializers.Serializer):
    habit=serializers.CharField(source='name_habit')
    day=serializers.IntegerField()
    id=serializers.IntegerField()
    lenght=serializers.CharField()
    type=serializers.CharField()


class GetRelationship(serializers.ModelSerializer):
    token=serializers.UUIDField()
    class Meta:
        model=Profile
        fields=['name','token','who_is']





class DrugsSer(serializers.ModelSerializer):


    class Meta:
        model = Drugs
        fields = ['id', 'catigories', 'name', 'time_day', 'day', 'intake']


class Notification_drugs_Ser(serializers.ModelSerializer):
    class Meta:
        model=Notification_drugs
        fields=['time']


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
    #end_day=serializers.DateField()
    #status=serializers.BooleanField()
    notification=serializers.SerializerMethodField()
    class Meta:
        model=Drugs
        fields=['id','name','time_day','day','intake','created_at','notification']

    def get_notification(self, obj):
        # Достаем все уведомления, которые мы получили через prefetch_related
        # Используем .all(), чтобы Django не шел снова в базу
        notifications = obj.notifications_drugs.all()

        return [
            {
                "id": n.id,
                "time": n.time,
                # Проверяем, есть ли чек на сегодня (он уже в памяти благодаря Prefetch)
                "is_taken": n.checks.exists()
            }
            for n in notifications
        ]


class DrugUpdateSer(serializers.ModelSerializer):
    class Meta:
        model = Drugs
        # Перечисляем поля, которые можно менять
        fields = ['catigories', 'name', 'time_day', 'day', 'intake']

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
    file=serializers.ListField(
        child=serializers.FileField(),
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
    photo = serializers.ImageField(required=False)

class PetSerGet(serializers.ModelSerializer):
    health = serializers.SerializerMethodField()


    class Meta:
        model=Pet
        fields=['id','klichka','pet','gender','health','photo']

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