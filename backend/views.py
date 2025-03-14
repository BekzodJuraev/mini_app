from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from .serializers import RegistrationSerializer,LoginSer,ProfileSer
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .models import Profile
from django.db.models.functions import ExtractYear
from django.utils.timezone import now
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

