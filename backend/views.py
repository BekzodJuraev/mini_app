from rest_framework.permissions import IsAuthenticated
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
    ChatGETSer
)

from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Exists, OuterRef

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .models import Profile,Quest,Categories_Quest,Tests,Chat
from django.db.models.functions import ExtractYear
from django.utils.timezone import now
import time
from .prompt import chat_system,crash_test,lifestyle_test,symptoms_test,lestnica_test,breath_test,genchi_test,ruffier_test,kotova_test,martinet_test,cooper_test
from django.utils.timezone import localtime, now
from django.shortcuts import get_object_or_404
import json
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
        profile= Profile.objects.annotate(age=now().year - ExtractYear('date_birth')).filter(username=request.user).first()
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

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile=request.user.profile
            message = serializer.validated_data.get('message')
            response_data=chat_system(message)
            Chat.objects.create(profile=profile,question=message,answer=response_data)

            return Response({'message': response_data}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)


class CrashTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CrashTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: CrashTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=crash_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=1)
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
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test = symptoms_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=2)
            Tests.objects.create(profile=profile, name="Выбор симптомов", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class LifeStyleTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LifeStyleTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: LifeStyleTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lifestyle_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=4)
            Tests.objects.create(profile=profile,name="Оценка образа жизни",created_at=today,message=test['message'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartLestTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartLestTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartLestTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lestnica_test(serializer.validated_data['pulse'])
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест на лестнице", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartRelaxTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartLestTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartLestTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=lestnica_test(serializer.validated_data['pulse'])
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест в  состоянии покоя", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class HeartBreathTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartBreathTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartBreathTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=breath_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Штанге", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)

class HeartGenchiTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartGenchiTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartGenchiTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=genchi_test(serializer.data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Генчи", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartRufeTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartRufeTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartRufeTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=ruffier_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест Руфье", created_at=today, message=test['message'])


            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartKotovaTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartKotovaTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartKotovaTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test = kotova_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Котова", created_at=today, message=test['message'])

            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartMartineTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartMartineTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartMartineTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=martinet_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Проба Мартинэ", created_at=today, message=test['message'])
            return Response(test, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid form data'}, status=status.HTTP_400_BAD_REQUEST)
class HeartKuperTestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HeartKuperTestSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: HeartKuperTestSer()}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            profile = request.user.profile
            today = localtime(now()).date()
            test=cooper_test(serializer.validated_data)
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)
            Tests.objects.create(profile=profile, name="Тест Купера", created_at=today, message=test['message'])
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
                    created_at=today,
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
        cat = Tests.objects.filter(profile=profile).order_by('-created_at')
        filter = request.query_params.get('filter')

        if filter:
            cat=Tests.objects.filter(profile=profile,name__icontains=filter).order_by('-created_at')




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