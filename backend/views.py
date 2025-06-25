from rest_framework.permissions import IsAuthenticated
from django.db.models import ExpressionWrapper, F, DurationField, DateField
from datetime import date,timedelta
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
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
    GetPetDrugSer


)
from threading import Thread
from datetime import date


from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Exists, OuterRef

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .models import Profile,Quest,Categories_Quest,Tests,Chat,Tracking_Habit,Habit,Drugs,Check_Drugs,Daily_check,Rentgen_Image,Rentgen,Pet,Calories,PetChat,Pet_Drugs,Pet_Check_Drugs,PetRentgen,PetRentgen_Image,PetDaily_check
from django.db.models.functions import ExtractYear
from django.utils.timezone import now
import time
from .prompt import chat_system,crash_test,lifestyle_test,symptoms_test,lestnica_test,breath_test,genchi_test,ruffier_test,kotova_test,martinet_test,cooper_test,chat_update,daily_check,rentgen,get_health_scale_pet,lifestyle_test_dog,habit_test_dog,emotion_test_dog,emotion_test_cat,sleep_test_cat,apetit_test_cat,povidenie_test_grizuna,apetit_test_grizuna,forma_test_grizuna,calories,petrentgen,petdaily_check
from django.utils.timezone import localtime, now
from django.shortcuts import get_object_or_404
import json
from django.db.models import Sum,Q,Count,F,Max,Prefetch,OuterRef, Subquery,Value

def update_system(f):
    def wrapper(self,request,*args,**kwargs):
        message = f(self, request, *args, **kwargs)
        if message.status_code == 200 and 'message' in message.data:
            profile = request.user.profile



            def update():
                update_health = chat_update(profile.health_system, message.data['message'])
                profile.health_system = update_health

                profile.save(update_fields=['health_system'])

            # asd
            Thread(target=update).start()


        return message
    return wrapper
class RegisterAPIView(APIView):
    serializer_class = RegistrationSerializer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RegistrationSerializer()}
    )
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)



class LoginAPIView(APIView):
    serializer_class = LoginSer
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LoginSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username=serializer.validated_data.get('telegram_id')
            user=User.objects.filter(username=username).first()
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                response_data = {'message': 'Login successful', 'token': token.key}

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'User not registered'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


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
            return Response({"message":"waiting data"}, status=status.HTTP_200_OK)





class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatGETSer(many=True)}
    )
    def get(self,request):
        profile=request.user.profile
        query=Chat.objects.filter(profile=profile).order_by('-created_at')
        serializer=ChatGETSer(query,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatSer()}
    )
    @update_system
    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile=request.user.profile
            message = serializer.validated_data.get('message')




            response_data = chat_system(message)

            Chat.objects.create(profile=profile,question=message,answer=response_data)

            return Response({'message': response_data}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class CrashTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CrashTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CrashTestSer()}
    )
    @update_system
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=crash_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, tests_id=1)
            Tests.objects.create(profile=profile, name="Краш тест", created_at=today, message=test['message'])
            profile.life_expectancy=test['life_expectancy']

            profile.save(update_fields=['life_expectancy'])

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

class LifeStyleTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LifeStyleTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LifeStyleTestSer()}
    )
    @update_system
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
    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            today = localtime(now()).date()

            profile = request.user.profile
            habit = Habit.objects.filter(name_habit=serializer.validated_data['habit']).first()
            if habit:
                Tracking_Habit.objects.get_or_create(
                    profile=profile,
                    habit=habit,
                    created_at=today,
                    defaults={'check_is': serializer.validated_data['check_is']}
                )
                return Response({'message': 'Tracking habit created or already exists'}, status=200)
            else:
                return Response({'message': 'Habit not found'}, status=404)
        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


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
        tracking = Habit.objects.filter(profile=profile).annotate(day=Count('habit_tracking',filter=Q(habit_tracking__check_is=False))).values('name_habit','day')




        serializer = self.serializer_class(tracking, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class RelationshipView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=RelationshipSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RelationshipSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Saved successful'}, status=status.HTTP_201_CREATED)


class RelationshipBabyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=RelationshipBabySer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RelationshipBabySer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Saved successful'}, status=status.HTTP_201_CREATED)

class GetRelationshipListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=GetRelationship

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetRelationship(many=True)}
    )
    def get(self,request):
        profile=request.user.profile
        profiles = Profile.objects.filter(family=profile).order_by('-id').only('name', 'who_is', 'username')

        response_data = []

        for prof in profiles:
            token, _ = Token.objects.get_or_create(user=prof.username)

            response_data.append({
                "name": prof.name,
                "who_is": prof.who_is,
                "token": token.key,
            })
        serializer = self.serializer_class(response_data, many=True)
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
            serializer.save(pet_id=message_id)

            return Response({'message':'Saved drug'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class DrugsAPiView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DrugsSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DrugsSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=request.user.profile)

            return Response({'message':'Saved drug'}, status=status.HTTP_200_OK)

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
        query = Pet_Drugs.objects.filter(pet_id=message_id).annotate(end_day=ExpressionWrapper(F('created_at') + F('interval'), output_field=DateField()), status=Exists(
                Pet_Check_Drugs.objects.filter(
                    drugs=OuterRef('pk'),
                    created_at=today
                    # Matches each category with its related Quests
                )
            ))
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class DrugsAPIListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetDrugSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GetDrugSer()}
    )

    def get(self,request):
        profile = request.user.profile
        today = localtime(now()).date()
        query = Drugs.objects.filter(profile=profile).annotate(end_day=ExpressionWrapper(F('created_at') + F('interval'), output_field=DateField()), status=Exists(
                Check_Drugs.objects.filter(
                    profile=profile,
                    drugs=OuterRef('pk'),
                    created_at=today
                    # Matches each category with its related Quests
                )
            ))
        serializer = self.serializer_class(query, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PetDrugCheckbyDayView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DrugById

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DrugById()}
    )
    def post(self,request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            today = localtime(now()).date()
            profile = request.user.profile
            try:
                Pet_Check_Drugs.objects.get_or_create(
                    drugs_id=serializer.validated_data['id'],
                    created_at=today,
                )
                return Response({'message': 'Daily check saved'}, status=200)
            except:

                return Response({'message': 'Not Found'}, status=404)



        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class DrugCheckbyDayView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DrugById

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: DrugById()}
    )
    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            today = localtime(now()).date()
            profile = request.user.profile
            try:
                Check_Drugs.objects.get_or_create(
                    profile=profile,
                    drugs_id=serializer.validated_data['id'],
                    created_at=today,
                )
                return Response({'message': 'Daily check saved'}, status=200)
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
    def get(self, request):
        profile = request.user.profile
        query = Rentgen.objects.filter(profile=profile).prefetch_related('rentgen_image').order_by('-created_at')
        serializer = RentgenSerGet(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSer()}
    )
    @update_system
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile

            test=rentgen(serializer.validated_data.get('photo'),serializer.validated_data.get('message'))
            r=Rentgen.objects.create(profile=profile,message=serializer.validated_data.get('message'),answer=test['message'])


            consumables = [
                Rentgen_Image(rentgen=r, images=image)
                for image in serializer.validated_data.get('photo')
            ]
            Rentgen_Image.objects.bulk_create(consumables)






            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetRentgenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RentgenSer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSerGet(many=True)}
    )
    def get(self, request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        query = PetRentgen.objects.filter(pet_id=message_id).prefetch_related('rentgen_image').order_by('-created_at')
        serializer = RentgenSerGet(query, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: RentgenSer()}
    )

    def post(self,request,message_id):
        pet = get_object_or_404(Pet, id=message_id, profile=request.user.profile)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():


            test=petrentgen(serializer.validated_data.get('photo'),serializer.validated_data.get('message'))
            r=PetRentgen.objects.create(pet_id=message_id,message=serializer.validated_data.get('message'),answer=test['message'])


            consumables = [
                PetRentgen_Image(rentgen=r, images=image)
                for image in serializer.validated_data.get('photo')
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
            pet=Pet.objects.create(profile=profile,klichka=serializer.validated_data.get('klichka'),pet=serializer.validated_data.get('pet'),
                                   gender=serializer.validated_data.get('gender'))
            def update():
                health_system = get_health_scale_pet(serializer.validated_data)
                pet.health_system = health_system
                pet.save(update_fields=['health_system'])



            #asd
            Thread(target=update).start()




            return Response({'message': 'Pet created'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class PetstyleView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetEmotionSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetEmotionSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #profile = request.user.profile
            test=emotion_test_dog(serializer.validated_data)


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class PetEmotionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PetEmotionSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: PetEmotionSer()}
    )
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
    def post(self, request):
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
        query = Calories.objects.filter(profile=profile,created_at=today).values_list('total',flat=True)
        calories = belok = jir = uglevod = klechatka = 0
        if query:
            for item in query:
                calories+=item['ккал']
                belok+=item['белок']
                jir += item['жир']
                uglevod+=item['углеводы']
                klechatka+=item['клечатка']




        dic={
        "calories":calories,
        "belok":belok,
        "jir":jir,
        "uglevod":uglevod,
        "klechatka":klechatka

        }

        serializer = GetCaloriesSer(dic)

        return Response(serializer.data, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesSer()}
    )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            test=calories(serializer.validated_data['photo'])
            Calories.objects.create(profile=profile,detail=test['detail'],total=test['total'])


            return Response({'message':test['message']}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class CaroiesListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=CaloriesListSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CaloriesListSer(many=True)}
    )
    def get(self, request):
        profile = request.user.profile
        query=Calories.objects.filter(profile=profile)



        serializer = self.serializer_class(query,many=True)

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
        query=PetChat.objects.filter(pet_id=message_id).order_by('-created_at')
        serializer=PetChatGet(query,many=True)

        return Response(serializer.data,status=status.HTTP_200_OK)
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatSer()}
    )

    def post(self,request,message_id):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile=request.user.profile
            message = serializer.validated_data.get('message')

            pet = get_object_or_404(Pet, id=message_id, profile=profile)


            response_data = chat_system(message)

            PetChat.objects.create(pet_id=message_id,question=message,answer=response_data)

            return Response({'message': response_data}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


