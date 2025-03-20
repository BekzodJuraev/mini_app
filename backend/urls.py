from django.urls import path,include
from . import views
urlpatterns=[
 path('api/register',views.RegisterAPIView.as_view(),name='register'),
 path('api/login',views.LoginAPIView.as_view(),name='login'),
 path('api/logout',views.LogoutAPIView.as_view(),name='logout'),
 path('api/profile/main',views.ProfileAPIView.as_view(),name='profile_main'),
 path('api/profile/update',views.ProfileUpdateAPIView.as_view(),name='profile_update'),
 path('api/profile/healthsystem', views.ProfileMainSystemAPIView.as_view(),name='healthsystem'),
 path('api/profile/chat',views.ChatAPIView.as_view(),name='chat'),
 path('api/profile/crashtest',views.CrashTestAPIView.as_view(),name='crashtest')
]