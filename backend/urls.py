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
 path('api/hearthtest/relax', views.HeartRelaxTestAPIView.as_view(), name='heartrelaxtest'),
 path('api/hearthtest/lest',views.HeartLestTestAPIView.as_view(),name='hearttest'),
 path('api/hearthtest/breath', views.HeartBreathTestAPIView.as_view(),name='breathtest'),
 path('api/hearthtest/genchi', views.HeartGenchiTestAPIView.as_view(), name='genchi'),
 path('api/hearthtest/rufe', views.HeartRufeTestAPIView.as_view(), name='rufe'),
 path('api/hearthtest/kotova', views.HeartKotovaTestAPIView.as_view(), name='kotova'),
 path('api/hearthtest/martine', views.HeartMartineTestAPIView.as_view(), name='martine'),
 path('api/hearthtest/kuper', views.HeartKuperTestAPIView.as_view(), name='kuper'),
 path('api/notification',views.NotificationAPIView.as_view(),name='notification'),
 path('api/notification/message/<int:message_id>',views.MessageView.as_view(),name='message'),
 path('api/tests',views.QuestAPIView.as_view(),name='list'),
 path('api/habit/add',views.HabitView.as_view(), name='habit_add'),
 path('api/habit/tracking',views.Tracking_checkView.as_view(),name='tracking'),
 path('api/habit/list',views.GetTrackingView.as_view(),name='habit_get')
]