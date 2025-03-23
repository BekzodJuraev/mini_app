from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from .serializers import RegistrationSerializer,LoginSer,ProfileSer,ProfileUpdateSer,ProfileMainSystemSer,ChatSer,CrashTestSer,QuestSer,SymptomsTestSer,LifeStyleTestSer,HeartLestTestSer
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Exists, OuterRef

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .models import Profile,Quest,Categories_Quest
from django.db.models.functions import ExtractYear
from django.utils.timezone import now
import time
from .prompt import chat_system,crash_test
from django.utils.timezone import localtime, now

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
    def get(self,request):
        profile= request.user.profile
        serializer = self.serializer_class(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSer

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ChatSer()}
    )

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data.get('message')
            response_data=chat_system(message)
            return Response(response_data, status=status.HTTP_200_OK)

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
            Quest.objects.get_or_create(profile=profile,created_at=today,tests_id=1)
            test=crash_test(serializer.validated_data)
            # if isinstance(test, str):
            #     try:
            #         test = json.loads(test)  # Convert JSON string to dictionary
            #     except json.JSONDecodeError:
            #         raise ValueError("Invalid JSON format returned from OpenAI API")
            # print(test)


            #print(test['life_expectancy'])
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
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=2)

            return Response(serializer.data, status=status.HTTP_200_OK)

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
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=4)

            return Response(serializer.data, status=status.HTTP_200_OK)

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
            Quest.objects.get_or_create(profile=profile, created_at=today, tests_id=3)

            return Response(serializer.data, status=status.HTTP_200_OK)

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

