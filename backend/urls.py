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
 path('api/tests/crashtest',views.CrashTestAPIView.as_view(),name='crashtest'),
 path('api/tests/symptomstest',views.SymptomsTestAPIView.as_view(),name='symptomstests'),
 path('api/tests/lifestyletest',views.LifeStyleTestAPIView.as_view(),name='lifestyletest'),
 path('api/hearthtest/lest',views.HeartLestTestAPIView.as_view(),name='hearttest'),
 path('api/hearthtest/breath', views.HeartBreathTestAPIView.as_view(),name='breathtest'),
 path('api/hearthtest/genchi', views.HeartGenchiTestAPIView.as_view(), name='genchi'),

 path('api/tests',views.QuestAPIView.as_view(),name='list'),
]