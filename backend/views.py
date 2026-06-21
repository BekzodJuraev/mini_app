from rest_framework.permissions import IsAuthenticated
from django.db.models import ExpressionWrapper, F, DurationField, DateField
from datetime import date,timedelta
from rest_framework.parsers import MultiPartParser, FormParser
from collections import defaultdict
from django.contrib.auth import authenticate,login,logout
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import calendar
from .tranlater import translate_api_response,translate_health_keys_api
from django.db.models import Avg
from drf_yasg import openapi
from config import EMAIL_HOST_USER
import random
from django.core.mail import send_mail
from django.core.cache import cache
from .serializers import (
    SetResetPasswordSer,
    VerifyCodeSerializer,
    ResetPasswordRequestSerializer,
    RegistrationFirstSer,
    RegistrationSerializer,
    LoginSer,
    ProfileSer,
    ProfileUpdateSer,
    ProfileMainSystemSer,
    ChatSer,
    CrashTestSer,
    QuestSer,
    SymptomsTestSer,
    LifeStyleTestSer,
    HeartLestTestSer,
    HeartBreathTestSer,
    HeartGenchiTestSer,
    HeartRufeTestSer,
    HeartKotovaTestSer,
    HeartMartineTestSer,
    HeartKuperTestSer,
    NotificationSer,
    ChatGETSer,
    HabitSer,
    TrackingSer,
    GetHabitSer,
    CountHabitSer,
    RelationshipSer,
    RelationshipBabySer,
    GetRelationship,
    DrugsSer,
    GetDrugSer,
    DrugById,
    RefGet,
    DailyCheckSer,
    RentgenSer,
    RentgenSerGet,
    PetSerCreate,
    PetSerGet,
    PetstyleSer,
    PetEmotionSer,
    PetHabitSer,
    PetCatEmotSer,
    PetCatSleepSer,
    PetCatApetitSer,
    PetGrizunSer,
    CaloriesSer,
    GetCaloriesSer,
    CaloriesListSer,
    PetChatGet,
    PetDrugSer,
    GetPetDrugSer,
    CaloriesChatSer,
    PetGetCaloriesSer,
    PublicNotifcationSer,
    PublicNotificationDrugSer,
    PublicNotificationPetDrugSer,
    Notification_drugs_Ser,
    DrugUpdateSer,
    EditCaloriesSer,
    NutritionGoalSerializer,
    AdminTestsSer,
    AdminTestByIDSer,
    AIInputSer,
    NotificatonSer,
    NutritionGoalPetSerializer,
    EditCaloriesPetSer,
    Notification_drugs_pet_Ser,
    DrugUpdatePetSer,
    NotificationPEtSer,
    HearthTestSer,
    Add_familyrefSer



)
from threading import Thread
from datetime import date
from django.utils import timezone


from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Exists, OuterRef

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .models import Profile,Quest,Categories_Quest,Tests,Chat,Tracking_Habit,Habit,Drugs,Check_Drugs,Daily_check,Rentgen_Image,Rentgen,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,PetRentgen,PetRentgen_Image,PetDaily_check,PetCalories,Notification_drugs,NutritionGoal,Test,Notification,NutritionGoalPet,Notification_Pet_drugs,Tests_Pet,BloodPressure
from django.db.models.functions import ExtractYear,TruncDate
from django.utils.timezone import now
import time
from .prompt import chat_system,crash_test,lifestyle_test,symptoms_test,lestnica_test,breath_test,genchi_test,ruffier_test,kotova_test,martinet_test,cooper_test,chat_update,daily_check,rentgen,get_health_scale_pet,lifestyle_test_dog,habit_test_dog,emotion_test_dog,emotion_test_cat,sleep_test_cat,apetit_test_cat,povidenie_test_grizuna,apetit_test_grizuna,forma_test_grizuna,calories,petrentgen,petdaily_check,pet_calories,chat_update_pet,chat_system_pet,calories_edit,testadmin,calories_pet_edit,blood_pressure_test,life_expectancy,single_pressure_analysis

from django.utils.timezone import localtime, now
from django.shortcuts import get_object_or_404
import json
from django.db.models import Sum,Q,Count,F,Max,Prefetch,OuterRef, Subquery,Value
# def update_life_expectancy(f):
#
#     def wrapper(self, request, *args, **kwargs):
#         response = f(self, request, *args, **kwargs)
#
#         if response.status_code == 200:
#             profile = request.user.profile
#
#             def update():
#                 user_data = {
#                     "age": profile.age,
#                     "gender": profile.gender,
#                     "region": profile.region,
#                     "height": profile.height,
#                     "weight": profile.weight,
#                     "blood_pressure": profile.blood_pressure,
#                     "pulse": profile.pulse,
#                 }
#
#                 result = life_expectancy(user_data)
#
#                 profile.life_expectancy_json = result["message"]
#                 profile.save(update_fields=["life_expectancy"])
#
#             Thread(target=update, daemon=True).start()
#
#         return response
#
#     return wrapper


def get_chat_history(profile):
    """
    Вытаскивает последние 20 сообщений диалога и форматирует их для OpenAI.
    """
    chats = list(
        Chat.objects.filter(profile=profile).order_by('-created_at')[:20]
    )
    chats.reverse()  # Разворачиваем в хронологический порядок

    history = []
    for chat in chats:
        if chat.question:
            history.append({"role": "user", "content": chat.question})
        if chat.answer:
            history.append({"role": "assistant", "content": chat.answer})
    return history


def get_user_and_pet_context(profile):
    """
    Максимальный медицинский контекст:
    Профиль, Семья, Цели, Последние 15 чекапов, Тесты, Рентген/МРТ,
    Давление, Привычки (с историей выполнений), Калории за 30 дней для человека, его семьи и питомцев.
    """
    # ЛОКАЛЬНЫЕ ИМПОРТЫ МОДЕЛЕЙ (Защита от Circular Import)
    from .models import Calories, Rentgen, Tracking_Habit

    # Временной отрезок за последние 30 дней
    start_date = timezone.now().date() - timedelta(days=30)

    # 1. Последние 10 медицинских тестов человека
    human_tests = list(profile.tests.exclude(message=None).order_by('-created_at')[:10])
    human_tests_history = [f"{t.name}: {t.message}" for t in human_tests]

    # 2. Последние 5 заключений рентгена / МРТ (Rentgen)
    rentgen_records = list(profile.rentgen.exclude(answer=None).order_by('-created_at')[:5])
    rentgen_history = [f"{r.message}: {r.answer}" for r in rentgen_records]

    # 3. Последние 10 записей давления человека
    pressure_records = list(profile.pressure_history.order_by('-created_at')[:10])
    pressure_history = [f"{p.pressure_top}/{p.pressure_bottom}" for p in pressure_records]

    # 4. Привычки человека с подсчетом выполненных дней
    # Аннотируем каждую привычку количеством успешных отметок (check_is=True)
    habits_with_counts = profile.habit.all().annotate(
        completed_days_count=Count(
            'habit_tracking',
            filter=Q(habit_tracking__profile=profile, habit_tracking__check_is=True)
        )
    )
    habits_list = [
        f"{h.name_habit} ({h.lenght}) — выполнено дней: {h.completed_days_count}"
        for h in habits_with_counts
    ]

    # 5. Последние 15 ежедневных чекапов человека (Daily_check)
    daily_checks = list(
        profile.daily_check.exclude(message=None).order_by('-created_at', '-id')[:15]
    )
    daily_checks.reverse()
    daily_checks_history = [
        {"date": check.created_at.strftime('%Y-%m-%d') if check.created_at else "Неизвестно", "report": check.message}
        for check in daily_checks
    ]

    # 6. История питания человека за 30 дней (detail)
    calories_30_days = Calories.objects.filter(
        profile=profile,
        created_at__date__gte=start_date,
        saved=True
    ).order_by('-created_at')

    human_food_history = []
    total_water_30_days = 0.0

    for c in calories_30_days:
        if c.detail:
            human_food_history.append({
                "date": c.created_at.strftime('%Y-%m-%d'),
                "detail": c.detail
            })
        if c.water_intake:
            total_water_30_days += c.water_intake

    # 7. Цели пользователя (КБЖУ + Вода из Profile)
    user_nutrition_goals = {}
    if hasattr(profile, 'nutrition_goal') and profile.nutrition_goal:
        goal = profile.nutrition_goal
        user_nutrition_goals = {
            "target_calories": goal.calories,
            "target_proteins": goal.proteins,
            "target_fats": goal.fats,
            "target_carbs": goal.carbs,
            "target_fiber": goal.fiber,
        }
    user_nutrition_goals["target_water_liters"] = getattr(profile, 'water_goal', None)

    # 8. Данные обо всех питомцах хозяина
    pets_data = []
    for pet in profile.pet.all():
        pet_tests = list(pet.tests_pet.exclude(message=None).order_by('-created_at')[:5])
        pet_tests_history = [f"{pt.name}: {pt.message}" for pt in pet_tests]

        pet_calories_30_days = pet.pet_calories.filter(
            created_at__gte=start_date,
            saved=True
        ).order_by('-created_at')

        pet_food_history = []
        for pc in pet_calories_30_days:
            if pc.detail:
                pet_food_history.append({
                    "date": pc.created_at.strftime('%Y-%m-%d'),
                    "detail": pc.detail
                })

        pet_nutrition_goals = {}
        if hasattr(pet, 'nutrition_goal_pet') and pet.nutrition_goal_pet:
            p_goal = pet.nutrition_goal_pet
            pet_nutrition_goals = {
                "target_calories": p_goal.calories,
                "target_proteins": p_goal.proteins,
                "target_fats": p_goal.fats,
                "target_carbs": p_goal.carbs,
                "target_fiber": p_goal.fiber
            }

        pets_data.append({
            "name": pet.klichka,
            "type": pet.pet,
            "gender": pet.gender,
            "birth_date": pet.age.strftime('%Y-%m-%d') if pet.age else None,
            "health_system_metrics": pet.health_system or {},
            "environmental_risks_report": pet.risk_test,
            "last_medical_tests": pet_tests_history,
            "nutrition_history_30_days": pet_food_history,
            "nutrition_goals": pet_nutrition_goals
        })

    # 9. ПОДКЛЮЧАЕМ ДАННЫЕ О СЕМЬЕ (Profile.family)
    family_data = []

    family_members = set()
    if profile.family:
        family_members.add(profile.family)

    for member in profile.family_family.all():
        family_members.add(member)

    for member in family_members:
        m_tests = list(member.tests.exclude(message=None).order_by('-created_at')[:5])
        m_tests_history = [f"{t.name}: {t.message}" for t in m_tests]

        # Считаем привычки и для членов семьи, чтобы ИИ понимал их уровень дисциплины
        m_habits_with_counts = member.habit.all().annotate(
            completed_days_count=Count(
                'habit_tracking',
                filter=Q(habit_tracking__profile=member, habit_tracking__check_is=True)
            )
        )
        m_habits = [
            f"{h.name_habit} ({h.lenght}) — выполнено дней: {h.completed_days_count}"
            for h in m_habits_with_counts
        ]

        family_data.append({
            "name": member.name,
            "gender": member.gender,
            "birth_date": member.date_birth.strftime('%Y-%m-%d') if member.date_birth else None,
            "health_indicators_score": member.health_system or {},
            "environmental_risks": member.risk_test,
            "health_recommendations_summary": member.health_recommendations,
            "habits": m_habits,
            "recent_medical_tests": m_tests_history
        })

    # Итоговый JSON для OpenAI
    return {
        "user_info": {
            "name": profile.name,
            "gender": profile.gender,
            "birth_date": profile.date_birth.strftime('%Y-%m-%d') if profile.date_birth else None,
            "place_of_residence": profile.place_of_residence,
            "health_indicators_score": profile.health_system or {},
            "calculated_life_expectancy": profile.life_expectancy,
            "environmental_risks": profile.risk_test,
            "health_recommendations_summary": profile.health_recommendations
        },
        "user_nutrition_and_water_goals": user_nutrition_goals,
        "user_daily_checkups_last_15_days": daily_checks_history,
        "user_medical_tests": human_tests_history,
        "user_rentgen_and_mri_reports": rentgen_history,
        "user_blood_pressure_history": pressure_history,
        "user_habits": habits_list,  # Теперь содержит количество выполненных дней!
        "user_nutrition_history_30_days": {
            "food_records": human_food_history,
            "total_water_intake_liters_last_30_days": total_water_30_days
        },
        "user_pets": pets_data,
        "user_family_members": family_data
    }
def update_system(f):
    def wrapper(self,request,*args,**kwargs):
        message = f(self, request, *args, **kwargs)
        if message.status_code == 200 and 'message' in message.data:
            profile = request.user.profile
            #print(message.data['message'])




            def update():
                update_health = chat_update(profile.health_system, message.data['message'])
                profile.health_system = update_health


                profile.save(update_fields=['health_system'])

            # asd
            Thread(target=update).start()



        return message
    return wrapper

def pet_update_system(f):
    def wrapper(self,request, message_id,*args,**kwargs):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        message = f(self,request,message_id, *args, **kwargs)

        if message.status_code == 200 and 'message' in message.data:


            def update():
                health_system = chat_update_pet(pet.health_system,message.data['message'])
                pet.health_system = health_system
                pet.save(update_fields=['health_system'])

            # asd
            Thread(target=update).start()


        return message
    return wrapper
class AddRefamilyvView(APIView):
    serializer_class = Add_familyrefSer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            family_ref = serializer.validated_data['family_ref']
            family = Profile.objects.filter(family_ref=family_ref).first()
            profile.recommended_by_family=family
            profile.family=family
            profile.save(update_fields=['recommended_by_family','family'])
            # Создаем кастомный ответ с сообщением
            response_data = {
                "status": "Добавлен в семью",
                "data": serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DeleteFromFamilyView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        profile=request.user.profile


        # Remove them from the family without deleting the user row
        profile.family = None
        profile.save(update_fields=['family'])

        return Response(
            {"detail": "User's family association cleared. Account is safe."},
            status=status.HTTP_200_OK
        )

class AdminTestsView(APIView):
    serializer_class = AdminTestsSer

    permission_classes = [IsAuthenticated]


    @swagger_auto_schema(
        responses={status.HTTP_200_OK: AdminTestsSer()}
    )
    @translate_api_response(fields=['title','description','system_display'])
    def get(self, request):
        query=Test.objects.all()
        serializer = self.serializer_class(query,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationAPIViewSecond(APIView):
    serializer_class = NotificatonSer
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: NotificatonSer()}
    )

    def get(self, request):

        profile = request.user.profile
        today = localtime(now()).date()
        notifications = Notification.objects.filter(profile=profile,created_at=today)

        serializer = self.serializer_class(notifications, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: NotificatonSer()}
    )
    def post(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class AdminTestDetailAPIView(APIView):
    serializer_class = AdminTestByIDSer

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: AdminTestByIDSer()}
    )
    @translate_api_response(fields=['question.text', 'question.choices.text'])
    def get(self, request, pk):
        # Используем prefetch_related, чтобы за 1 запрос вытащить
        # сам тест, все вопросы к нему и все варианты ответов (choices)
        test = Test.objects.prefetch_related(
            'questions',           # Подгружаем вопросы (используй свой related_name)
            'questions__choices'   # Подгружаем варианты ответов для этих вопросов
        ).get(pk=pk) # Либо get_object_or_404(Test.objects.prefetch_related(...), pk=pk)

        serializer = self.serializer_class(test)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: AIInputSer()}
    )
    @update_system
    @translate_api_response(fields=['summary'])
    def post(self, request, pk, pet_id=None):
        test = get_object_or_404(Test, pk=pk)


        # Валидируем только наличие поля 'answers' как JSON
        input_serializer = AIInputSer(data=request.data)


        if input_serializer.is_valid():
            # Собираем контекст из модели
            # Добавляем which_animal только если роль — животное
            role_info = test.get_role_display()
            if test.role == 'animal' and hasattr(test, 'which_animal'):
                role_info = f"{role_info} ({test.get_which_animal_display()})"

            # 3. Формируем "Жирный" JSON для ИИ
            full_context_for_ai = {
                "metadata": {
                    "title": test.title,
                    "description": test.description,
                    "role": role_info,
                    "system": test.get_system_display(),
                    "subsection": test.get_subsection_display(),
                },
                "instructions": {
                    "expert_rule": test.example_answer  # Твой главный промпт-инструкция
                },
                "user_data": {
                    "answers": input_serializer.validated_data['answers']  # Весь JSONField от фронта
                }
            }
            test_ai=testadmin(full_context_for_ai)
            if test.role == "animal":
                pet=get_object_or_404(Pet,id=pet_id,profile=request.user.profile)
                Tests_Pet.objects.create(pet=pet, name=test.title, message=test_ai['summary'])
            else:
                Tests.objects.create(profile=request.user.profile, name=test.title, message=test_ai['summary'])



            # Отправляем этот "компот" в ИИ или возвращаем для проверки
            return Response(test_ai, status=status.HTTP_200_OK)

        return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class SetPasswordView(APIView):
    serializer_class = SetResetPasswordSer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=SetResetPasswordSer,
        responses={status.HTTP_200_OK: "Password updated successfully"}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            new_password = serializer.validated_data['password']


            user = request.user


            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Your password has been reset successfully."},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RegistrationSerializer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RegistrationSerializer()}
    )
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({'message': 'Profile Created'}, status=status.HTTP_201_CREATED)

class RegisterFirstAPIView(APIView):
    serializer_class = RegistrationFirstSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RegistrationFirstSer()}
    )
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        token, created = Token.objects.get_or_create(user=user)

        return Response({'message': 'Registration successful', 'token': token.key}, status=status.HTTP_201_CREATED)

class LoginAPIView(APIView):
    serializer_class = LoginSer
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LoginSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username=serializer.validated_data.get('login')
            password = serializer.validated_data.get('password')

            user = authenticate(username=username, password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                response_data = {'message': 'Login successful', 'token': token.key}

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'User not registered'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)



class RequestPasswordReset(APIView):
    serializer_class = ResetPasswordRequestSerializer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ResetPasswordRequestSerializer()}
    )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


        reset_code = str(random.randint(100000, 999999))


        cache.set(f"reset_code_{email}", reset_code, timeout=600)


        send_mail(
            'Password Reset Code',
            f'Your 6-digit verification code is: {reset_code}',
            EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Code sent to email'}, status=status.HTTP_200_OK)


class VerifyResetCode(APIView):
    serializer_class = VerifyCodeSerializer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: VerifyCodeSerializer()}
    )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        input_code = serializer.validated_data['code']


        cached_code = cache.get(f"reset_code_{email}")



        if cached_code and input_code == cached_code:
            cache.set(f"verified_email_{email}", True, timeout=300)
            user=User.objects.filter(email=email).first()
            if not user:
                return Response({"error": "User no longer exists."}, status=404)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Code verified. You can now change your password.",
                "email": email,
                "token":token.key
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Invalid or expired code."},
            status=status.HTTP_400_BAD_REQUEST
        )
class LogoutAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete the token to logout the user
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSer
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ProfileSer()}
    )
    @translate_api_response(fields=['pressure_test','life_expectancy_json','health_recommendations','risk_test','pressure_plus','diary_plus'])
    def get(self,request):
        def calculate_age(birth_date):
            today = date.today()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        profile = Profile.objects.filter(username=request.user).first()
        age = calculate_age(profile.date_birth)
        profile.age = age
        serializer = self.serializer_class(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=ProfileUpdateSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ProfileUpdateSer()}
    )
    def get(self,request):
        profile=request.user.profile
        serializer=self.serializer_class(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def patch(self,request):
        profile=request.user.profile
        serializer = self.serializer_class(profile,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully!",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Profile update failed!",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class ProfileMainSystemAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileMainSystemSer
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ProfileMainSystemSer()}
    )

    def get(self, request):
        profile = request.user.profile
        serializer = self.serializer_class(profile)

        try:
            health_system = serializer.data.get('health_system', {})

            # Convert dictionary into a list of {"name": key, "value": value} dictionaries
            transformed_health_system = [{"name": key, "value": value} for key, value in health_system.items()]

            return Response({
                "name": serializer.data["name"],
                "health_system": transformed_health_system
            }, status=status.HTTP_200_OK)
        except:
            return Response({"message": "waiting data"}, status=status.HTTP_200_OK)
    # def get(self, request):
    #     profile = request.user.profile
    #
    #     for _ in range(20):
    #         profile.refresh_from_db()
    #         serializer = self.serializer_class(profile)
    #         health_system = profile.health_system
    #
    #
    #
    #
    #         if health_system:
    #             transformed_health_system = [
    #                 {"name": key, "value": value}
    #                 for key, value in health_system.items()
    #             ]
    #
    #             return Response({
    #                 "name": serializer.data["name"],
    #                 "health_system": transformed_health_system
    #             }, status=status.HTTP_200_OK)
    #
    #         time.sleep(1)
    #
    #         # If still no data after retries, return pending
    #     return Response({"message": "pending"}, status=status.HTTP_200_OK)





class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatGETSer(many=True)}
    )
    def get(self,request):
        profile=request.user.profile
        query=Chat.objects.filter(profile=profile).order_by('created_at')
        serializer=ChatGETSer(query,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatSer()}
    )
    @update_system
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            message = serializer.validated_data.get('message')

            # 1. Быстро собираем историю диалога и медицинский контекст через функции
            history = get_chat_history(profile)
            context_data = get_user_and_pet_context(profile)

            # 2. Получаем ответ от ИИ
            response_data = chat_system(
                message=message,
                context_data=context_data,
                history=history
            )

            # 3. Сохраняем в базу
            Chat.objects.create(
                profile=profile,
                question=message,
                answer=response_data
            )

            return Response(
                {"message": response_data},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Invalid form data"},
            status=status.HTTP_400_BAD_REQUEST
        )

class CrashTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CrashTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CrashTestSer()}
    )
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=crash_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=1)
            Tests.objects.create(profile=profile, name="Краш тест", created_at=today, message=test['message'])
            profile.life_expectancy=test['life_expectancy']
            profile.IK=serializer.validated_data.get('ik',0)
            profile.save(update_fields=['life_expectancy','IK'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


#asd
class SymptomsTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SymptomsTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: SymptomsTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test = symptoms_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile,  tests_id=2)
            Tests.objects.create(profile=profile, name="Выбор симптомов", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class BloodPressureTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HearthTestSer  # Убедитесь, что в нем есть pressure_top и pressure_bottom

    def get(self, request):
        profile = request.user.profile

        # 1. Получаем средние значения по дням из модели BloodPressure
        # Используем trunc_date, чтобы группировать именно по календарным дням
        daily_stats = (
            BloodPressure.objects.filter(profile=profile)
            .values("created_at")  # Группировка по дате без учета времени
            .annotate(
                avg_top=Avg("pressure_top"),
                avg_bottom=Avg("pressure_bottom")
            )
            .order_by("-created_at")
        )

        # 2. Группируем данные по месяцам
        structured_data = defaultdict(list)
        for entry in daily_stats:
            day_date = entry["created_at"]
            month_key = day_date.strftime("%Y-%m")

            structured_data[month_key].append({
                "date": day_date,
                "pressure_top": round(entry["avg_top"]),
                "pressure_bottom": round(entry["avg_bottom"])
            })

        # 3. Формируем итоговый список
        result = []
        for month, days in structured_data.items():
            month_avg_top = sum(d["pressure_top"] for d in days) / len(days)
            month_avg_bottom = sum(d["pressure_bottom"] for d in days) / len(days)

            result.append({
                "month": month,
                "month_average": {
                    "pressure_top": round(month_avg_top),
                    "pressure_bottom": round(month_avg_bottom)
                },
                "days": days
            })

        return Response(result)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: HearthTestSer()}
    )
    @translate_api_response(fields=['result'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            profile = request.user.profile
            p_top = serializer.validated_data["pressure_top"]
            p_bottom = serializer.validated_data["pressure_bottom"]
            test=single_pressure_analysis(p_top,p_bottom)

            # 1. Сохраняем новое измерение
            BloodPressure.objects.create(
                profile=profile,
                pressure_top=p_top,
                pressure_bottom=p_bottom
            )

            # 2. Получаем начало ТЕКУЩЕГО месяца
            # Например, если сегодня 15 июня, возьмет 1 июня 00:00
            start_of_month = now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # 3. Берем все записи только за этот календарный месяц
            month_history = BloodPressure.objects.filter(
                profile=profile,
                created_at__gte=start_of_month
            )

            # 4. Отправляем список записей в функцию ИИ
            ai_analysis = blood_pressure_test(month_history)

            # 5. Логируем результат анализа в модель Tests
            profile.pressure_test=ai_analysis.get("message")
            profile.save(update_fields=['pressure_test'])

            return Response(
                {
                    "message": "Измерение сохранено, анализ за месяц обновлен",
                    "current": {"top": p_top, "bottom": p_bottom},
                    "result":test.get('message')
                },
                status=status.HTTP_201_CREATED
            )

class LifeStyleTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LifeStyleTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LifeStyleTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lifestyle_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=4)
            Tests.objects.create(profile=profile,name="Оценка образа жизни",created_at=today,message=test['message'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartLestTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartLestTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartLestTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lestnica_test(serializer.validated_data['pulse'])
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест на лестнице", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartRelaxTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartLestTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartLestTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lestnica_test(serializer.validated_data['pulse'])
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест в  состоянии покоя", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class HeartBreathTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartBreathTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartBreathTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=breath_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Штанге", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class HeartGenchiTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartGenchiTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartGenchiTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=genchi_test(serializer.data)
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Генчи", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartRufeTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartRufeTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartRufeTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=ruffier_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile,  tests_id=3)
            Tests.objects.create(profile=profile, name="Тест Руфье", created_at=today, message=test['message'])


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartKotovaTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartKotovaTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartKotovaTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test = kotova_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Котова", created_at=today, message=test['message'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)



class HeartMartineTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartMartineTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartMartineTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=martinet_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Мартинэ", created_at=today, message=test['message'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartKuperTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartKuperTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartKuperTestSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=cooper_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест Купера", created_at=today, message=test['message'])

            # def update():
            #     update_health = chat_update(profile.health_system, test['message'])
            #     profile.health_system = update_health
            #
            #     profile.save(update_fields=['health_system'])
            #
            #
            #
            # #asd
            # Thread(target=update).start()
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class QuestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: QuestSer(many=True)}
    )
    def get(self,request):
        profile = request.user.profile
        today = localtime(now()).date()

        # Annotate all categories with a status field (True if at least one related Quest exists today)
        categories = Categories_Quest.objects.annotate(
            status=Exists(
                Quest.objects.filter(
                    profile=profile,
                    tests=OuterRef('pk')  # Matches each category with its related Quests
                )
            )
        ).values('name', 'status')


        serializer = self.serializer_class(categories,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)






class NotificationPetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPEtSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: NotificationPEtSer(many=True)}
    )
    def get(self,request,message_id):
        profile = request.user.profile
        pet=get_object_or_404(Pet,profile=profile,id=message_id)
        cat = Tests_Pet.objects.filter(pet=pet).order_by('-id')
        filter = request.query_params.get('filter')

        if filter:
            cat=Tests_Pet.objects.filter(pet=pet,name__icontains=filter).order_by('-id')




        serializer = self.serializer_class(cat,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessagePetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id,test_id):
        profile=request.user.profile
        pet = get_object_or_404(Pet, profile=profile, id=message_id)
        message = get_object_or_404(Tests_Pet, id=test_id, pet=pet)
        if message.read == False:
            message.read=True
            message.save(update_fields=['read'])
        return Response({'message': message.message},status=status.HTTP_200_OK)
class NotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: NotificationSer(many=True)}
    )

    def get(self,request):
        profile = request.user.profile
        cat = Tests.objects.filter(profile=profile).order_by('-id')
        filter = request.query_params.get('filter')

        if filter:
            cat=Tests.objects.filter(profile=profile,name__icontains=filter).order_by('-id')




        serializer = self.serializer_class(cat,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    @translate_api_response(fields=['message'])
    def get(self, request, message_id):
        profile=request.user.profile
        message = get_object_or_404(Tests, id=message_id, profile=profile)
        if message.read == False:
            message.read=True
            message.save(update_fields=['read'])
        return Response({'message': message.message},status=status.HTTP_200_OK)


class HabitView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HabitSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HabitSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=request.user.profile)

            return Response({'message':'Saved a habit'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class Tracking_checkView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TrackingSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: TrackingSer()}
    )
    @update_system
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            target_date = serializer.validated_data.get('date')
            check_is_val = serializer.validated_data.get('check_is')

            profile = request.user.profile
            habit = Habit.objects.filter(name_habit=serializer.validated_data['habit']).first()

            if habit:
                # 1. Забираем или создаем объект трекера
                obj, created = Tracking_Habit.objects.get_or_create(
                    profile=profile,
                    habit=habit,
                    created_at=target_date,
                    defaults={'check_is': check_is_val}
                )

                # Если запись уже была, но юзер изменил статус (например, передумал и отметил) — обновляем
                if not created and obj.check_is != check_is_val:
                    obj.check_is = check_is_val
                    obj.save(update_fields=['check_is'])

                # 2. Считаем общее количество дней выполнения этой привычки
                total_completed_days = Tracking_Habit.objects.filter(
                    profile=profile,
                    habit=habit,
                    check_is=True
                ).count()
                total_missed_days = Tracking_Habit.objects.filter(
                    profile=profile,
                    habit=habit,
                    check_is=False
                ).count()

                # 3. Формируем единый, жирный message для твоего ИИ-декоратора
                status_text = "выполнена успешно" if obj.check_is else "не выполнена / пропущена"
                habit_type_ru = "Полезная" if habit.type == "good" else "Вредная"
                ai_message = (
                    f"Привычка '{habit.name_habit}' ({habit.lenght}). "
                    f"Тип привычки: {habit_type_ru} . "
                    f"Статус за дату {obj.created_at}: {status_text}. "
                    f"Статистика за всё время — выполнено дней: {total_completed_days}, пропущено дней: {total_missed_days}."
                )

                # 4. Отдаем полный фарш в Response
                response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
                return Response({
                    'success': obj.check_is,  # Поле успеха (True/False)
                    'message': ai_message,  # Полный текст для chat_update промпта
                }, status=response_status)

            return Response({'message': 'Habit not found', 'success': False}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetTrackingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetHabitSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetHabitSer(many=True)}
    )

    def get(self,request):
        profile=request.user.profile
        tracking=Tracking_Habit.objects.filter(habit__profile=profile)
        serializer = self.serializer_class(tracking,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetTrackingCount(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CountHabitSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CountHabitSer(many=True)}
    )
    def get(self,request):
        profile = request.user.profile
        tracking = Habit.objects.filter(profile=profile).annotate(day=Count('habit_tracking',filter=Q(habit_tracking__check_is=False))).values('id','type','name_habit','day','lenght')




        serializer = self.serializer_class(tracking, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class RelationshipView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=RelationshipSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RelationshipSer()}
    )

    def post(self,request):
        #print(request.user)
        serializer = self.serializer_class(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        #token, created = Token.objects.get_or_create(user=user)
        return Response({'message': "Created"}, status=status.HTTP_201_CREATED)


class RelationshipBabyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=RelationshipBabySer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RelationshipBabySer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        user=serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

class GetRelationshipListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=GetRelationship

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetRelationship(many=True)}
    )

    def get(self, request):
        profile = request.user.profile
        # Получаем QuerySet
        query = Profile.objects.filter(family=profile).annotate(tests_count=Count('tests')
        ).order_by('-id')

        # Передаем QuerySet в сериализатор (убедись, что self.serializer_class равен ProfileWithTokenSerializer)
        serializer = self.serializer_class(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)



class PetDrugsAPiView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetDrugSer()}
    )

    def post(self,request,message_id):
        serializer = self.serializer_class(data=request.data)
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        if serializer.is_valid():
            drug_instance=serializer.save(pet_id=message_id)

            return Response({
                'message': 'Saved drug',
                'id': drug_instance.id  # Фронтенд возьмет этот ID для создания уведомлений
            }, status=status.HTTP_201_CREATED)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class DeleteDrugsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(Drugs, pk=pk,profile=request.user.profile)
        item.delete()
        return Response({'message':'Drug deleted'}, status=status.HTTP_200_OK)


class DeleteHabitView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(Habit, pk=pk,profile=request.user.profile)
        item.delete()
        return Response({'message':'Habit deleted'}, status=status.HTTP_200_OK)



class DrugsAPiView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DrugsSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DrugsSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            drug_instance = serializer.save(profile=request.user.profile)

            return Response({
                'message': 'Saved drug',
                'id': drug_instance.id  # Фронтенд возьмет этот ID для создания уведомлений
            }, status=status.HTTP_201_CREATED)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetDrugsAPIListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetPetDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetPetDrugSer()}
    )

    def get(self,request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        today = localtime(now()).date()
        query = Pet_Drugs.objects.filter(pet=pet).prefetch_related(
            Prefetch(
                'notifications_pet_drugs',  # Убедись, что в модели Drugs это имя в related_name
                queryset=Notification_Pet_drugs.objects.prefetch_related(
                    Prefetch('checks', queryset=Pet_Check_Drugs.objects.filter(date=today))
                )
            )
        )
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class Notification_create(APIView):
    permission_classes = [IsAuthenticated]

    # Используем many=True в схеме, так как ожидаем список времен
    @swagger_auto_schema(
        request_body=Notification_drugs_Ser(many=True),
        responses={status.HTTP_201_CREATED: Notification_drugs_Ser(many=True)}
    )
    def post(self, request, drug_id):  # переименовал message_id в drug_id для ясности
        profile = request.user.profile

        # Проверяем, что лекарство принадлежит именно этому профилю
        drug = get_object_or_404(Drugs, id=drug_id, profile=profile)

        # Передаем данные в сериализатор. many=True позволяет принять список [{}, {}]
        serializer = Notification_drugs_Ser(data=request.data, many=True)

        if serializer.is_valid():
            # При сохранении передаем drug, чтобы связать уведомления с объектом
            serializer.save(drugs=drug)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class Notification_Pet_create(APIView):
    permission_classes = [IsAuthenticated]

    # Используем many=True в схеме, так как ожидаем список времен
    @swagger_auto_schema(
        request_body=Notification_drugs_Ser(many=True),
        responses={status.HTTP_201_CREATED: Notification_drugs_Ser(many=True)}
    )
    def post(self, request, message_id,drug_id):  # переименовал message_id в drug_id для ясности
        profile = request.user.profile
        pet=get_object_or_404(Pet,profile=profile,id=message_id)

        # Проверяем, что лекарство принадлежит именно этому профилю
        drug = get_object_or_404(Pet_Drugs, id=drug_id, pet=pet)

        # Передаем данные в сериализатор. many=True позволяет принять список [{}, {}]
        serializer = Notification_drugs_pet_Ser(data=request.data, many=True)

        if serializer.is_valid():
            # При сохранении передаем drug, чтобы связать уведомления с объектом
            serializer.save(drugs=drug)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MonthlyStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        today = localtime(now()).date()

        # 1. Параметры месяца (можно передавать через ?month=12&year=2025)
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        start_of_month = today.replace(year=year, month=month, day=1)
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = today.replace(year=year, month=month, day=last_day)

        # 2. Цели пользователя
        goal = getattr(profile, 'nutrition_goal', None)
        if not goal or goal.calories == 0:
            return Response({"error": "Цель не установлена"}, status=200)

        # 3. Выборка данных
        queryset = Calories.objects.filter(
            profile=profile,
            created_at__range=[start_of_month, end_of_month],
            saved=True
        ).values('created_at', 'total')

        # 4. Группировка всех нутриентов по дням
        # Используем лямбда-функцию, чтобы структура БЖУ создавалась для каждого нового дня
        daily_data = defaultdict(lambda: {
            "calories": 0.0, "belok": 0.0, "jir": 0.0, "uglevod": 0.0, "klechatka": 0.0
        })

        for entry in queryset:
            day = entry['created_at']
            t = entry['total'] or {}

            daily_data[day]["calories"] += float(t.get('ккал', 0))
            daily_data[day]["belok"] += float(t.get('белок', 0))
            daily_data[day]["jir"] += float(t.get('жир', 0))
            daily_data[day]["uglevod"] += float(t.get('углеводы', 0))
            daily_data[day]["klechatka"] += float(t.get('клетчатка', 0))

        # 5. Формируем детальный ответ по дням и считаем общий средний %
        total_monthly_percent = 0
        daily_details = {}

        for day, stats in daily_data.items():
            # Процент выполнения за конкретный день
            raw_percent = (stats["calories"] / goal.calories) * 100
            day_percent = min(round(raw_percent, 1), 100.0)

            # Сохраняем детали дня (для нижней части изображение_5.png)
            daily_details[day.strftime('%Y-%m-%d')] = {
                "fact": stats,
                "goal": {
                    "calories": goal.calories,
                    "belok": goal.proteins,
                    "jir": goal.fats,
                    "uglevod": goal.carbs,
                    "klechatka": goal.fiber
                },
                "percentage": day_percent
            }

            # Для общего итога месяца суммируем, ограничивая 100% (как в ТЗ)
            total_monthly_percent += min(day_percent, 100)

        # Средний процент за месяц
        days_tracked = len(daily_data)
        average_monthly_percent = round(total_monthly_percent / days_tracked, 1) if days_tracked > 0 else 0

        return Response({
            "average_monthly_percent": average_monthly_percent,  # Для топ-бара
            "monthly_label": start_of_month.strftime('%B %Y'),
            "daily_details": daily_details,  # Объект, где ключи - даты
            "marked_days": list(daily_details.keys())  # Список дат с данными
        }, status=status.HTTP_200_OK)
class MonthlyStatisticsPetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,message_id):
        profile = request.user.profile
        pet=get_object_or_404(Pet,profile=profile,id=message_id)
        today = localtime(now()).date()


        # 1. Параметры месяца (можно передавать через ?month=12&year=2025)
        year = int(request.query_params.get('year', today.year))
        month = int(request.query_params.get('month', today.month))

        start_of_month = today.replace(year=year, month=month, day=1)
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = today.replace(year=year, month=month, day=last_day)

        # 2. Цели пользователя
        goal = getattr(pet, 'nutrition_goal_pet', None)
        if not goal or goal.calories == 0:
            return Response({"error": "Цель не установлена"}, status=200)

        # 3. Выборка данных
        queryset = PetCalories.objects.filter(
            pet=pet,
            created_at__range=[start_of_month, end_of_month],
            saved=True
        ).values('created_at', 'total')

        # 4. Группировка всех нутриентов по дням
        # Используем лямбда-функцию, чтобы структура БЖУ создавалась для каждого нового дня
        daily_data = defaultdict(lambda: {
            "calories": 0.0, "belok": 0.0, "jir": 0.0, "uglevod": 0.0, "klechatka": 0.0,"vitamin":0.0,"mineral":0.0
        })

        for entry in queryset:
            day = entry['created_at']
            t = entry['total'] or {}

            daily_data[day]["calories"] += float(t.get('ккал', 0))
            daily_data[day]["belok"] += float(t.get('белок', 0))
            daily_data[day]["jir"] += float(t.get('жир', 0))
            daily_data[day]["uglevod"] += float(t.get('углеводы', 0))
            daily_data[day]["klechatka"] += float(t.get('клетчатка', 0))
            daily_data[day]["vitamin"] += float(t.get('витамины', 0))
            daily_data[day]["mineral"] += float(t.get('минералы', 0))

        # 5. Формируем детальный ответ по дням и считаем общий средний %
        total_monthly_percent = 0
        daily_details = {}

        for day, stats in daily_data.items():
            # Процент выполнения за конкретный день
            raw_percent = (stats["calories"] / goal.calories) * 100
            day_percent = min(round(raw_percent, 1), 100.0)

            # Сохраняем детали дня (для нижней части изображение_5.png)
            daily_details[day.strftime('%Y-%m-%d')] = {
                "fact": stats,
                "goal": {
                    "calories": goal.calories,
                    "belok": goal.proteins,
                    "jir": goal.fats,
                    "uglevod": goal.carbs,
                    "klechatka": goal.fiber,
                    "vitamin":goal.vitamin,
                    "mineral":goal.mineral

                },
                "percentage": day_percent
            }

            # Для общего итога месяца суммируем, ограничивая 100% (как в ТЗ)
            total_monthly_percent += min(day_percent, 100)

        # Средний процент за месяц
        days_tracked = len(daily_data)
        average_monthly_percent = round(total_monthly_percent / days_tracked, 1) if days_tracked > 0 else 0

        return Response({
            "average_monthly_percent": average_monthly_percent,  # Для топ-бара
            "monthly_label": start_of_month.strftime('%B %Y'),
            "daily_details": daily_details,  # Объект, где ключи - даты
            "marked_days": list(daily_details.keys())  # Список дат с данными
        }, status=status.HTTP_200_OK)


class Water_view(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        # Общая цель берется один раз из профиля
        goal = getattr(profile, 'water_goal', 2.0)

        # Агрегируем выпитое по дням
        stats = Calories.objects.filter(profile=profile, saved=True) \
            .annotate(date=TruncDate('created_at')) \
            .values('date') \
            .annotate(total_intake=Sum('water_intake')) \
            .order_by('-date')

        # Формируем список дней
        days_history = []
        for entry in stats:
            current = entry['total_intake'] or 0.0
            days_history.append({
                "date": entry['date'],
                "current_liters": round(current, 2),
                # Процент для конкретного дня
                "percentage": round((current / goal * 100), 1) if goal > 0 else 0
            })

        # Итоговая структура: цель отдельно, история отдельно
        return Response({
            "goal_liters": round(goal, 2),
            "history": days_history
        })
class Notification_Detail(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=Notification_drugs_Ser()
    )
    def patch(self, request, pk):
        """Изменение конкретного уведомления по его ID"""
        profile = request.user.profile

        # Ищем уведомление, проверяя через связь, что оно принадлежит лекарству этого юзера
        notification = get_object_or_404(
            Notification_drugs,
            id=pk,
            drugs__profile=profile
        )

        # Передаем объект в сериализатор для частичного обновления
        serializer = Notification_drugs_Ser(notification, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Ищем уведомление по его ID
        # Добавляем фильтр drugs__profile, чтобы юзер не мог удалить чужое уведомление
        notification = get_object_or_404(
            Notification_drugs,
            id=pk,
            drugs__profile=request.user.profile
        )

        notification.delete()

        return Response(
            {"message": f"Deleted {pk} "},
            status=status.HTTP_200_OK
        )
    
class Notification_Pet_Detail(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=Notification_drugs_pet_Ser()
    )
    def patch(self, request, message_id, pk):
        """Изменение конкретного уведомления по его ID"""
        profile = request.user.profile
        pet=get_object_or_404(Pet,profile=profile,id=message_id)

        notification = get_object_or_404(
            Notification_Pet_drugs,
            id=pk,
            drugs__pet=pet
        )

        # Передаем объект в сериализатор для частичного обновления
        serializer = Notification_drugs_pet_Ser(notification, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, message_id, pk):
        profile = request.user.profile
        pet = get_object_or_404(Pet, profile=profile, id=message_id)
        notification = get_object_or_404(
            Notification_Pet_drugs,
            id=pk,
            drugs__pet=pet
        )

        notification.delete()

        return Response(
            {"message": f"Deleted {pk} "},
            status=status.HTTP_200_OK
        )
# class DrugsAPIListView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = GetDrugSer
#
#     @swagger_auto_schema(
#         responses={status.HTTP_200_OK: GetDrugSer()}
#     )
#
#     def get(self,request):
#         profile = request.user.profile
#         today = localtime(now()).date()
#         query = Drugs.objects.filter(profile=profile).annotate(end_day=ExpressionWrapper(F('created_at') + F('interval'), output_field=DateField()), status=Exists(
#                 Check_Drugs.objects.filter(
#                     profile=profile,
#                     drugs=OuterRef('pk'),
#                     created_at=today
#                     # Matches each category with its related Quests
#                 )
#             ))
#         serializer = self.serializer_class(query, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

class DrugsAPIListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetDrugSer()})
    def get(self, request):


        profile = request.user.profile
        today = localtime(now()).date()
        query = Drugs.objects.filter(profile=profile).prefetch_related(
            Prefetch(
                'notifications_drugs',  # Убедись, что в модели Drugs это имя в related_name
                queryset=Notification_drugs.objects.prefetch_related(
                    Prefetch('checks', queryset=Check_Drugs.objects.filter(date=today))
                )
            )
        )
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DrugEditView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=DrugUpdateSer)
    def patch(self, request, drug_id):
        profile = request.user.profile
        # Ищем лекарство именно этого пользователя
        drug = get_object_or_404(Drugs, id=drug_id, profile=profile)

        # partial=True позволяет обновлять только часть полей
        serializer = DrugUpdateSer(drug, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Данные лекарства обновлены",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Если нужен полный апдейт (PUT)
    def put(self, request, drug_id):
        profile = request.user.profile
        drug = get_object_or_404(Drugs, id=drug_id, profile=profile)
        serializer = DrugUpdateSer(drug, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DrugEditPetView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=DrugUpdatePetSer)
    def patch(self, request, message_id, drug_id):
        profile = request.user.profile
        pet=get_object_or_404(Pet,profile=profile,id=message_id)
        # Ищем лекарство именно этого пользователя
        drug = get_object_or_404(Pet_Drugs, id=drug_id, pet=pet)

        # partial=True позволяет обновлять только часть полей
        serializer = DrugUpdatePetSer(drug, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Данные лекарства обновлены",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Если нужен полный апдейт (PUT)
    def put(self, request, message_id, drug_id):
        profile = request.user.profile
        pet = get_object_or_404(Pet, profile=profile, id=message_id)
        drug = get_object_or_404(Pet_Drugs, id=drug_id, pet=pet)
        serializer = DrugUpdateSer(drug, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DeletePetDrugsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request,pk):
        item = get_object_or_404(Pet_Drugs, pk=pk,pet__profile=request.user.profile)
        item.delete()
        return Response({'message':'Drug deleted'}, status=status.HTTP_200_OK)





class PetDrugCheckbyDayView(APIView):
    permission_classes = [IsAuthenticated]



    def post(self,request,message_id,notification_id):
        today = localtime(now()).date()
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        get_object_or_404(Notification_Pet_drugs,drugs__pet=pet)
        try:
            Pet_Check_Drugs.objects.get_or_create(
                notification_id=notification_id,
                date=today,
            )
            return Response({'message': 'Notification drug is checked'}, status=200)
        except:

            return Response({'message': 'Not Found'}, status=404)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class DrugCheckbyDayView(APIView):
    permission_classes = [IsAuthenticated]



    def post(self,request,notification_id):
        today = localtime(now()).date()
        profile = request.user.profile
        get_object_or_404(Notification_drugs,drugs__profile=profile)
        try:
            Check_Drugs.objects.get_or_create(
                notification_id=notification_id,
                date=today,
            )
            return Response({'message': 'Notification drug is checked'}, status=200)
        except:

            return Response({'message': 'Not Found'}, status=404)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)













class RefGetView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RefGet

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RefGet()}
    )

    def get(self,request):
        profile = request.user.profile

        counts = Profile.objects.aggregate(
            family_ref_count=Count('id', filter=Q(recommended_by_family=profile)),
            partner_ref_count=Count('id', filter=Q(recommended_by_partner=profile)),
        )

        total = counts['family_ref_count'] + counts['partner_ref_count']

        data = {
            "total": total,
            "ref": profile.ref,
            "family_ref": profile.family_ref
        }

        serializer = self.serializer_class(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DailyCheckView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DailyCheckSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DailyCheckSer()}
    )
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            daily=Daily_check.objects.filter(profile=profile).first()
            if daily:
                test = daily_check(serializer.validated_data, daily.message)
            else:
                test = daily_check(serializer.validated_data)


            Daily_check.objects.get_or_create(profile=profile, message=test['message'],created_at=today)

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetDailyCheckView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DailyCheckSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DailyCheckSer()}
    )
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            today = localtime(now()).date()
            daily=PetDaily_check.objects.filter(pet_id=message_id).first()
            if daily:
                test = petdaily_check(serializer.validated_data, daily.message)
            else:
                test = petdaily_check(serializer.validated_data)


            PetDaily_check.objects.get_or_create(pet_id=message_id, message=test['message'],created_at=today)

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class RentgenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentgenSer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSerGet(many=True)}
    )
    @translate_api_response(fields=['message','answer'])
    def get(self, request):
        profile = request.user.profile
        query = Rentgen.objects.filter(profile=profile).prefetch_related('rentgen_image').order_by('created_at')
        serializer = RentgenSerGet(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSer()}
    )
    @update_system
    @translate_api_response(fields=['message'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            current_message = serializer.validated_data.get('message')
            files = serializer.validated_data.get('file')

            # 1. Извлекаем чистые заключения (только answer)
            past_records = Rentgen.objects.filter(profile=profile).exclude(answer=None).order_by('-created_at')[:20]

            history_lines = [
                f"Дата: {r.created_at.strftime('%Y-%m-%d')} -> Заключение: {r.answer}"
                for r in reversed(past_records)
            ]
            records_context = "\n".join(history_lines)

            # 2. Соединяем с глобальным отчетом из профиля
            rentgen_history_context = ""
            if profile.analysis_risk:
                rentgen_history_context += f"ПОСЛЕДНИЙ СФОРМИРОВАННЫЙ АНАЛИЗ РИСКОВ ИЗ ПРОФИЛЯ:\n{profile.analysis_risk}\n\n"

            rentgen_history_context += f"ИСТОРИЯ ПРЕДЫДУЩИХ ЗАКЛЮЧЕНИЙ:\n{records_context}"

            # 3. Отправляем в OpenAI (функция деф rentgen остается прежней)
            test = rentgen(files, current_message, rentgen_history_context)

            # 4. Обновляем глобальный накопительный отчет в профиле
            new_analysis_risk = test.get('analysis_risk')
            if new_analysis_risk:
                profile.analysis_risk = new_analysis_risk
                profile.save(update_fields=['analysis_risk'])

            # 5. Сохраняем текущее исследование в базу
            r = Rentgen.objects.create(
                profile=profile,
                message=current_message,
                answer=test.get('message')
            )

            # 6. Сохраняем картинки/документы пачкой
            consumables = [
                Rentgen_Image(rentgen=r, images=image)
                for image in files
            ]
            Rentgen_Image.objects.bulk_create(consumables)

            return Response({'message': test['message']}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetRentgenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentgenSer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSerGet(many=True)}
    )
    @translate_api_response(fields=['message','answer'])
    def get(self, request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        query = PetRentgen.objects.filter(pet_id=message_id).prefetch_related('rentgen_image').order_by('created_at')
        serializer = RentgenSerGet(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSer()}
    )
    @translate_api_response(fields=['message'])
    @pet_update_system
    def post(self,request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():


            test=petrentgen(serializer.validated_data.get('file'),serializer.validated_data.get('message'))
            r=PetRentgen.objects.create(pet_id=message_id,message=serializer.validated_data.get('message'),answer=test['message'])



            consumables = [
                PetRentgen_Image(rentgen=r, images=image)
                for image in serializer.validated_data.get('file')
            ]
            PetRentgen_Image.objects.bulk_create(consumables)






            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetSerCreate

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetSerGet(many=True)}
    )
    @translate_api_response(fields=['risk_test'])
    def get(self, request):
        profile = request.user.profile
        query = Pet.objects.filter(profile=profile)
        serializer = PetSerGet(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetSerCreate()}
    )


    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            pet=Pet.objects.create(profile=profile,photo=serializer.validated_data.get('photo'),klichka=serializer.validated_data.get('klichka'),pet=serializer.validated_data.get('pet'),
                                   gender=serializer.validated_data.get('gender'),age=serializer.validated_data.get('age'))

            health_system = get_health_scale_pet(serializer.validated_data)
            pet.health_system = health_system
            pet.save(update_fields=['health_system'])

            # def update():
            #     health_system = get_health_scale_pet(serializer.validated_data)
            #     pet.health_system = health_system
            #     pet.save(update_fields=['health_system'])
            #
            #
            #
            # #asd
            # Thread(target=update).start()




            return Response({'message': 'Pet created'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class PetstyleView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetstyleSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetstyleSer()}
    )

    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=lifestyle_test_dog(serializer.validated_data)




            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetEmotionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetEmotionSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetEmotionSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=emotion_test_dog(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class PetHabitView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetHabitSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetHabitSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=habit_test_dog(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class PetCatEmotView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetCatEmotSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetCatEmotSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=emotion_test_cat(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class PetCatSleepView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetCatSleepSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetCatSleepSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=sleep_test_cat(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)



class PetCatApetitView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetCatApetitSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetCatApetitSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=apetit_test_cat(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class PetGrizunPovidenieView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetGrizunSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetGrizunSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,messsage_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=povidenie_test_grizuna(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetGrizunFormaView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetGrizunSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetGrizunSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=forma_test_grizuna(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class PetGrizunApetitView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetGrizunSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetGrizunSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=apetit_test_grizuna(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class CaroiesView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=CaloriesSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetCaloriesSer()}
    )
    def get(self, request):
        profile = request.user.profile
        today = localtime(now()).date()

        # 1. Собираем данные о потребленных калориях (Факт)
        # Получаем все JSON-поля 'total' за сегодня, которые были сохранены
        query = Calories.objects.filter(
            profile=profile,
            created_at__date=today,
            saved=True
        ).values_list('total', flat=True)

        calories = belok = jir = uglevod = klechatka = 0

        for item in query:
            if item:  # Проверка на случай, если JSON пустой
                calories += item.get('ккал', 0)
                belok += item.get('белок', 0)
                jir += item.get('жир', 0)
                uglevod += item.get('углеводы', 0)
                klechatka += item.get('клетчатка', 0)

        # 2. Получаем цели из NutritionGoal (Норма)
        # Используем select_related('nutrition_goal') в идеале,
        # но тут просто берем связанный объект
        goal = getattr(profile, 'nutrition_goal', None)

        # Если цель не установлена, везде будут нули
        g_cal = goal.calories if goal else 0
        g_belok = goal.proteins if goal else 0
        g_jir = goal.fats if goal else 0
        g_uglevod = goal.carbs if goal else 0
        g_fiber = goal.fiber if goal else 0

        # 3. Считаем процент выполнения для круга (81% на макете)
        percentage = 0
        if g_cal > 0:
            percentage = int((calories / g_cal) * 100)
            # Ограничиваем 100%, если нужно для красоты диаграммы,
            # либо оставляем как есть, если важен перебор
            if percentage > 100:
                percentage = 100

                # 4. Формируем ответ вручную
        response_data = {
            "calories": calories,
            "goal_calories": g_cal,

            "belok": round(belok, 1),
            "goal_belok": g_belok,

            "jir": round(jir, 1),
            "goal_jir": g_jir,

            "uglevod": round(uglevod, 1),
            "goal_uglevod": g_uglevod,

            "klechatka": round(klechatka, 1),
            "goal_klechatka": g_fiber,

            "percentage": percentage,
            "has_goal": goal is not None
        }

        return Response(response_data, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesSer()}
    )
    @update_system
    @translate_api_response(fields=['detail.еда'])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            test=calories(serializer.validated_data['photo'])
            if test.get('detail'):
                cal=Calories.objects.create(profile=profile, detail=test.get('detail', []), total=test.get('total', []),
                                        images=serializer.validated_data['photo'],water_intake=test.get('water_intake'))




            return Response(
                {   'id':cal.id,
                    'detail':test['detail'],
                    'total':test['total']}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

    @update_system
    def patch(self, request, id):
        """
        Метод для активации флага saved=True.
        Передай id в URL: /calories/<id>/
        """
        profile = request.user.profile
        # Ищем запись именно этого пользователя
        cal_record = get_object_or_404(Calories, id=id, profile=profile)

        cal_record.saved = True
        cal_record.save()

        return Response({'message': cal_record.detail}, status=status.HTTP_200_OK)


class CaroiesListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=CaloriesListSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesListSer(many=True)}
    )
    @translate_api_response(fields=['foods.meals.detail.еда'])
    def get(self, request):
        profile = request.user.profile
        query=Calories.objects.filter(profile=profile,saved=True).exclude(detail=[]).order_by('-id')

        dic = defaultdict(lambda: {
            'meals': [],
            'total_daily': {
                "вес": 0,
                "ккал": 0,
                "белок": 0,
                "жир": 0,
                "углеводы": 0,
                "клетчатка": 0
            }
        })

        for item in query:
            dic[item.created_at]['meals'].append({
                'detail': item.detail,
                'total': item.total
            })

            dic[item.created_at]['total_daily']['вес']+=item.total.get('вес',0)
            dic[item.created_at]['total_daily']['ккал'] += item.total.get('ккал', 0)
            dic[item.created_at]['total_daily']['белок'] += item.total.get('белок', 0)
            dic[item.created_at]['total_daily']['жир'] += item.total.get('жир', 0)
            dic[item.created_at]['total_daily']['углеводы'] += item.total.get('углеводы', 0)
            dic[item.created_at]['total_daily']['клетчатка'] += item.total.get('клетчатка', 0)


        result=[]
        for key,item in dic.items():
            result.append({
                'created_at':key,
                'foods':item

            })







        serializer = self.serializer_class(result,many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatPetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetChatGet(many=True)}
    )

    def get(self,request,message_id):
        profile=request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)
        query=PetChat.objects.filter(pet_id=message_id).order_by('created_at')
        serializer=PetChatGet(query,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatSer()}
    )
    @pet_update_system
    @translate_api_response(fields=['message'])
    def post(self, request, message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            message = serializer.validated_data.get('message')

            # 1. Достаем питомца (сразу проверяем владельца)
            pet = get_object_or_404(Pet, id=message_id, profile=profile)

            # 2. Собираем ЛЕГКИЙ контекст только для этого питомца
            start_date = timezone.now().date() - timedelta(days=30)

            # Тянем только его тесты (исключая пустые)
            pet_tests = pet.tests_pet.exclude(message=None).order_by('-created_at')[:5]
            pet_tests_history = [f"{pt.name}: {pt.message}" for pt in pet_tests]

            # Тянем только его историю питания за 30 дней
            pet_calories = pet.pet_calories.filter(created_at__gte=start_date, saved=True).order_by('-created_at')
            pet_food_history = [
                {"date": pc.created_at.strftime('%Y-%m-%d'), "detail": pc.detail}
                for pc in pet_calories if pc.detail
            ]

            # Цели по КБЖУ питомца
            pet_nutrition_goals = {}
            if hasattr(pet, 'nutrition_goal_pet') and pet.nutrition_goal_pet:
                p_goal = pet.nutrition_goal_pet
                pet_nutrition_goals = {
                    "target_calories": p_goal.calories,
                    "target_proteins": p_goal.proteins,
                    "target_fats": p_goal.fats,
                    "target_carbs": p_goal.carbs,
                    "target_fiber": p_goal.fiber
                }

            # Итоговый компактный JSON-контекст для ИИ
            pet_ai_context = {
                "name": pet.klichka,
                "type": pet.pet,
                "gender": pet.gender,
                "birth_date": pet.age.strftime('%Y-%m-%d') if pet.age else None,
                "place_of_residence": profile.place_of_residence,  # Локация важна для климата/рисков
                "health_system_metrics": pet.health_system or {},
                "environmental_risks_report": pet.risk_test,
                "last_medical_tests": pet_tests_history,
                "nutrition_history_30_days": pet_food_history,
                "nutrition_goals": pet_nutrition_goals
            }

            # 3. Передаем в чат сообщение и легкий контекст
            response_data = chat_system_pet(message, pet_ai_context)

            # 4. Сохраняем историю
            PetChat.objects.create(
                pet_id=message_id,
                question=message,
                answer=response_data
            )

            return Response({'message': response_data}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)



class CaloriesEdit(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EditCaloriesSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: EditCaloriesSer()}
    )


    def get(self,request):
        profile = request.user.profile
        cal = Calories.objects.filter(profile=profile,saved=True).last()
        serializer = self.serializer_class(cal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        # request_body определяет, что мы ЖДЕМ от пользователя (detail тут исчезнет)
        request_body=EditCaloriesSer(),
        # responses определяет, что мы ОТДАДИМ (тут detail будет виден)
        responses={status.HTTP_200_OK: EditCaloriesSer()}
    )

    def post(self, request):
        profile = request.user.profile
        # Берем последнюю запись (обычно ту, что сейчас на экране)
        cal = Calories.objects.filter(profile=profile).last()

        if not cal:
            return Response({'message': 'Record not found'}, status=404)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_input = serializer.validated_data.get('message', '')

            active_details = serializer.validated_data.get('current_details', cal.detail)

            # Вызываем AI, передавая ему и текст, и текущую структуру
            test = calories_edit(user_input, cal.detail,active_details)

            if test.get('detail'):
                cal.detail = test.get('detail', [])
                cal.total = test.get('total', {})


                cal.save(update_fields=['detail', 'total'])

                return Response({
                    'message': test['message'],
                    'detail': cal.detail,
                    'total': cal.total
                }, status=status.HTTP_200_OK)

            return Response({'message': test.get('message', 'Error analyzing data')}, status=200)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CaloriesPetEdit(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EditCaloriesPetSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: EditCaloriesPetSer()}
    )


    def get(self,request,message_id):
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)
        cal = PetCalories.objects.filter(pet=pet,saved=True).last()
        serializer = self.serializer_class(cal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        # request_body определяет, что мы ЖДЕМ от пользователя (detail тут исчезнет)
        request_body=EditCaloriesPetSer(),
        # responses определяет, что мы ОТДАДИМ (тут detail будет виден)
        responses={status.HTTP_200_OK: EditCaloriesPetSer()}
    )

    def post(self, request,message_id):
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)
        # Берем последнюю запись (обычно ту, что сейчас на экране)
        cal = PetCalories.objects.filter(pet=pet).last()

        if not cal:
            return Response({'message': 'Record not found'}, status=404)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_input = serializer.validated_data.get('message', '')

            active_details = serializer.validated_data.get('current_details', cal.detail)


            # Вызываем AI, передавая ему и текст, и текущую структуру
            test = calories_pet_edit(user_input, cal.detail,active_details)

            if test.get('detail'):
                cal.detail = test.get('detail', [])
                cal.total = test.get('total', {})


                cal.save(update_fields=['detail', 'total'])

                return Response({
                    'message': test['message'],
                    'detail': cal.detail,
                    'total': cal.total
                }, status=status.HTTP_200_OK)

            return Response({'message': test.get('message', 'Error analyzing data')}, status=200)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NutritionGoalView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NutritionGoalSerializer

    def get(self, request):
        profile = request.user.profile
        goal = NutritionGoal.objects.filter(profile=profile).first()
        if not goal:
            return Response({
                "calories": 0, "proteins": 0, "fats": 0, "carbs": 0, "fiber": 0
            }, status=status.HTTP_200_OK)

        serializer = self.serializer_class(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=NutritionGoalSerializer)
    def post(self, request):
        """
        Создание или полное обновление целей питания.
        Работает для кнопки 'Подтвердить цель'.
        """
        profile = request.user.profile

        # update_or_create ищет запись по profile,
        # если находит — обновляет поля из defaults, если нет — создает.
        goal, created = NutritionGoal.objects.update_or_create(
            profile=profile,
            defaults={
                'calories': request.data.get('calories', 0),
                'proteins': request.data.get('proteins', 0),
                'fats': request.data.get('fats', 0),
                'carbs': request.data.get('carbs', 0),
                'fiber': request.data.get('fiber', 0),
            }
        )

        serializer = self.serializer_class(goal)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def patch(self, request):
        """Для частичного обновления (например, только калории)"""
        profile = request.user.profile
        goal = get_object_or_404(NutritionGoal, profile=profile)
        serializer = self.serializer_class(goal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NutritionGoalPETView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NutritionGoalPetSerializer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: NutritionGoalPetSerializer()}
    )

    def get(self, request,message_id):
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)
        goal = NutritionGoalPet.objects.filter(pet=pet).first()
        if not goal:
            return Response({
                "calories": 0, "proteins": 0, "fats": 0, "carbs": 0, "fiber": 0,"vitamin":0,"mineral":0
            }, status=status.HTTP_200_OK)

        serializer = self.serializer_class(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=NutritionGoalPetSerializer)
    def post(self, request,message_id):
        """
        Создание или полное обновление целей питания.
        Работает для кнопки 'Подтвердить цель'.
        """
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)

        # update_or_create ищет запись по profile,
        # если находит — обновляет поля из defaults, если нет — создает.
        goal, created = NutritionGoalPet.objects.update_or_create(
            pet=pet,
            defaults={
                'calories': request.data.get('calories', 0),
                'proteins': request.data.get('proteins', 0),
                'fats': request.data.get('fats', 0),
                'carbs': request.data.get('carbs', 0),
                'fiber': request.data.get('fiber', 0),
                'vitamin': request.data.get('vitamin', 0),
                'mineral': request.data.get('mineral', 0),
            }
        )

        serializer = self.serializer_class(goal)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def patch(self, request,message_id):
        profile = request.user.profile
        pet = get_object_or_404(Pet, id=message_id, profile=profile)

        goal = get_object_or_404(NutritionGoalPet, pet=pet)
        serializer = self.serializer_class(goal, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CaloriesChatView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaloriesChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesChatSer(many=True)}
    )
    @translate_api_response(fields=['detail.еда'])
    def get(self,request):
        profile=request.user.profile
        today = localtime(now()).date()
        three_days_ago = today - timedelta(days=2)
        query=Calories.objects.filter(profile=profile,created_at__gte=three_days_ago).order_by('created_at')
        serializer=CaloriesChatSer(query,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)



class PetCaroiesView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=CaloriesSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetGetCaloriesSer()}
    )
    def get(self, request, message_id):
        profile = request.user.profile
        # Проверяем, что питомец принадлежит именно этому пользователю
        pet = get_object_or_404(Pet, id=message_id, profile=profile)
        today = localtime(now()).date()

        # 1. Собираем данные о потребленных нутриентах
        query = PetCalories.objects.filter(
            pet_id=message_id,
            created_at=today,
            saved=True
        ).values_list('total', flat=True)

        calories = belok = jir = uglevod = klechatka = vitamin = mineral = 0

        for item in query:
            if item:
                calories += item.get('ккал', 0)
                belok += item.get('белок', 0)
                jir += item.get('жир', 0)
                uglevod += item.get('углеводы', 0)
                klechatka += item.get('клетчатка', 0)
                vitamin += item.get('витамины', 0)
                mineral += item.get('минералы', 0)

        # 2. Получаем цели (нормы) для питомца
        # Предположим, у модели Pet есть связь с NutritionGoal или поля внутри модели
        # Если цели хранятся в связанной модели, например pet.nutrition_goal:
        goal = getattr(pet, 'nutrition_goal_pet', None)

        g_cal = goal.calories if goal else 0
        g_belok = goal.proteins if goal else 0
        g_jir = goal.fats if goal else 0
        g_uglevod = goal.carbs if goal else 0
        g_fiber = goal.fiber if goal else 0

        # 3. Считаем общий процент выполнения по калориям
        percentage = 0
        if g_cal > 0:
            percentage = min(int((calories / g_cal) * 100), 100)

        # 4. Формируем словарь для сериализатора
        data = {
            "calories": round(calories, 1),
            "goal_calories": g_cal,

            "belok": round(belok, 1),
            "goal_belok": g_belok,

            "jir": round(jir, 1),
            "goal_jir": g_jir,

            "uglevod": round(uglevod, 1),
            "goal_uglevod": g_uglevod,

            "klechatka": round(klechatka, 1),
            "goal_klechatka": g_fiber,

            "vitamin": round(vitamin, 1),
            "mineral": round(mineral, 1),

            "percentage": percentage,
            "has_goal": goal is not None
        }

        # Если вы используете сериализатор, передайте данные в него
        # Убедитесь, что в PetGetCaloriesSer описаны все эти поля

        return Response(data, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesSer()}
    )
    @translate_api_response(fields=['detail.еда'])
    def post(self, request,message_id):
        serializer = self.serializer_class(data=request.data)
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        if serializer.is_valid():

            test=pet_calories(serializer.validated_data['photo'])

            if test.get('detail'):

                pet_cal=PetCalories.objects.create(pet_id=message_id, detail=test.get('detail', []), total=test.get('total', []),
                                        images=serializer.validated_data['photo'])
                return Response(
                    {'id': pet_cal.id,
                     'detail': test['detail'],
                     'total': test['total']}, status=status.HTTP_200_OK)



        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, message_id,id):
        """
        Метод для активации флага saved=True.
        Передай id в URL: <id>/
        """
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        # Ищем запись именно этого пользователя
        cal_record = get_object_or_404(PetCalories, id=id, pet=pet)

        cal_record.saved = True
        cal_record.save()

        return Response({'message': 'Calories saved successfully'}, status=status.HTTP_200_OK)
class PetCaroiesListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=CaloriesListSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesListSer(many=True)}
    )
    @translate_api_response(fields=['foods.meals.detail.еда'])
    def get(self, request,message_id):

        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        query=PetCalories.objects.filter(pet_id=message_id).exclude(detail=[]).order_by('-id')

        dic = defaultdict(lambda: {
            'meals': [],
            'total_daily': {
                "вес": 0,
                "ккал": 0,
                "белок": 0,
                "жир": 0,
                "углеводы": 0,
                "клетчатка": 0,
                "витамны":0,
                "минералы":0
            }
        })

        for item in query:
            dic[item.created_at]['meals'].append({
                'detail': item.detail,
                'total': item.total
            })

            dic[item.created_at]['total_daily']['вес']+=item.total.get('вес',0)
            dic[item.created_at]['total_daily']['ккал'] += item.total.get('ккал', 0)
            dic[item.created_at]['total_daily']['белок'] += item.total.get('белок', 0)
            dic[item.created_at]['total_daily']['жир'] += item.total.get('жир', 0)
            dic[item.created_at]['total_daily']['углеводы'] += item.total.get('углеводы', 0)
            dic[item.created_at]['total_daily']['клетчатка'] += item.total.get('клетчатка', 0)
            dic[item.created_at]['total_daily']['витамны'] += item.total.get('витамны', 0)
            dic[item.created_at]['total_daily']['минералы'] += item.total.get('минералы', 0)


        result=[]
        for key,item in dic.items():
            result.append({
                'created_at':key,
                'foods':item

            })







        serializer = self.serializer_class(result,many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PetCaloriesChatView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CaloriesChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesChatSer(many=True)}
    )
    @translate_api_response(fields=['detail.еда'])
    def get(self, request,message_id):
        #today = localtime(now()).date()
        #three_days_ago = today - timedelta(days=2)
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        query = PetCalories.objects.filter(
            pet_id=message_id
        ).order_by('created_at')
        serializer = CaloriesChatSer(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
class PublicNotifcationView(APIView):

    serializer_class = PublicNotifcationSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PublicNotifcationSer(many=True)}
    )
    def get(self, request):
        query=Habit.objects.filter(profile__who_is=None).select_related('profile').values('profile__username__username','profile__place_of_residence').distinct()

        serializer = PublicNotifcationSer(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)




class PublicNotificationDrugView(APIView):

    serializer_class = PublicNotificationDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PublicNotificationDrugSer(many=True)}
    )
    def get(self, request):
        query=Drugs.objects.filter(profile__who_is=None).select_related('profile','profile__username').prefetch_related('notifications_drugs')

        serializer = PublicNotificationDrugSer(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicNotificationPetDrugView(APIView):

    serializer_class = PublicNotificationPetDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PublicNotificationPetDrugSer(many=True)}
    )
    def get(self, request):
        query=Pet_Drugs.objects.filter(pet__profile__who_is=None).select_related('pet','pet__profile','pet__profile__username')

        serializer = PublicNotificationPetDrugSer(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
