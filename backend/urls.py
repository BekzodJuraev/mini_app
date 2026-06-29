from django.urls import path,include
from . import views
urlpatterns=[
 path('api/register/first',views.RegisterFirstAPIView.as_view(),name='register1'),
 path('api/register/second',views.RegisterAPIView.as_view(),name='register'),



 path('api/login',views.LoginAPIView.as_view(),name='login'),
 path('api/reset/email',views.RequestPasswordReset.as_view(),name='reset_email'),
 path('api/reset/set_password',views.SetPasswordView.as_view(),name='set_passowrd'),
 path('api/reset/code',views.VerifyResetCode.as_view(),name='reset_code'),
 path('api/logout',views.LogoutAPIView.as_view(),name='logout'),
 path('api/profile/main',views.ProfileAPIView.as_view(),name='profile_main'),
 path('api/profile/update',views.ProfileUpdateAPIView.as_view(),name='profile_update'),
 path('api/profile/healthsystem', views.ProfileMainSystemAPIView.as_view(),name='healthsystem'),
 path('api/profile/chat',views.ChatAPIView.as_view(),name='chat'),
 path('api/tests/crashtest',views.CrashTestAPIView.as_view(),name='crashtest'),
 path('api/tests/symptomstest',views.SymptomsTestAPIView.as_view(),name='symptomstests'),
 path('api/tests/lifestyletest',views.LifeStyleTestAPIView.as_view(),name='lifestyletest'),
 path('api/tests/bloodpressure',views.BloodPressureTestAPIView.as_view(),name='bloodpressure'),

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

 path('api/pet/notification/<int:message_id>', views.NotificationPetAPIView.as_view(), name='notification'),
 path('api/pet/notification/message/<int:message_id>/<int:test_id>', views.MessagePetView.as_view(), name='message'),

 path('api/notification/second',views.NotificationAPIViewSecond.as_view()),
 path('api/tests',views.QuestAPIView.as_view(),name='list'),

 path('api/habit/add',views.HabitView.as_view(), name='habit_add'),
 path('api/habit/tracking',views.Tracking_checkView.as_view(),name='tracking'),
 path('api/habit/list',views.GetTrackingView.as_view(),name='habit_get'),
 path('api/habit/get',views.GetTrackingCount.as_view(),name='habit_count'),
 path('api/habit/delete/<int:pk>', views.DeleteHabitView.as_view(), name='habit_delete'),



 path('api/relationship/notbaby',views.RelationshipView.as_view(),name='relationship'),
 path('api/relationship/baby', views.RelationshipBabyView.as_view(), name='relationship_baby'),
 path('api/relationship/list', views.GetRelationshipListView.as_view(),name='list_relat'),
 path('api/relationship/add_by_ref',views.AddRefamilyvView.as_view()),
 path('api/relationship/delete_from_family',views.DeleteFromFamilyView.as_view()),

 path('api/drugs/create',views.DrugsAPiView.as_view(),name='drugs_create'),
 path('api/drugs/list',views.DrugsAPIListView.as_view(),name='drugs_list'),
 path('api/drugs/edit/<int:drug_id>', views.DrugEditView.as_view()),
 path('api/drugs/check/<int:notification_id>',views.DrugCheckbyDayView.as_view(),name='drugs_check'),
 path('api/drugs/notification_create/<int:drug_id>',views.Notification_create.as_view(),name='drugs_notificaton_create'),
 path('api/drugs/notifications/<int:pk>', views.Notification_Detail.as_view()),

 path('api/pet/drugs/create/<int:message_id>', views.PetDrugsAPiView.as_view(), name='create_drugs'), #done
 path('api/pet/drugs/list/<int:message_id>', views.PetDrugsAPIListView.as_view(), name='list_drugs'), #done
 path('api/pet/drugs/edit/<int:message_id>/<int:drug_id>', views.DrugEditPetView.as_view()),#done
 path('api/pet/drugs/check/<int:message_id>/<int:notification_id>', views.PetDrugCheckbyDayView.as_view(), name='check'), #done
 path('api/pet/drugs/notification_create/<int:message_id>/<int:drug_id>', views.Notification_Pet_create.as_view(),
      name='drugs_notificaton_create'), #done
 path('api/pet/drugs/notifications/<int:message_id>/<int:pk>', views.Notification_Pet_Detail.as_view()),
 path('api/ref/list',views.RefGetView.as_view(),name='ref_list'),
 path('api/profile/daily_check',views.DailyCheckView.as_view(),name='daily_check'),
 path('api/rentgen',views.RentgenView.as_view(),name='rentgen'),
 path('api/pet',views.PetView.as_view(),name='pet'),

 path('api/pet/dog/lifestyletest/<int:message_id>',views.PetstyleView.as_view(),name='lifestyletest'),
 path('api/pet/dog/emotion/<int:message_id>',views.PetEmotionView.as_view(),name='emotion'),
 path('api/pet/dog/habit/<int:message_id>', views.PetHabitView.as_view(), name='habit'),

 path('api/pet/cat/emotion/<int:message_id>',views.PetCatEmotView.as_view(),name='cat_emotion'),
 path('api/pet/cat/sleep/<int:message_id>',views.PetCatSleepView.as_view(),name='cat_sleep'),
 path('api/pet/cat/apetit/<int:message_id>',views.PetCatApetitView.as_view(),name='cat_apetit'),

 path('api/pet/grizun/pov/<int:message_id>',views.PetGrizunPovidenieView.as_view(),name='pov'),
 path('api/pet/grizun/forma/<int:message_id>',views.PetGrizunFormaView.as_view(),name='forma'),
 path('api/pet/grizun/apetit/<int:message_id>',views.PetGrizunApetitView.as_view(),name='apetit'),


 path('api/pet/chat/<int:message_id>',views.ChatPetAPIView.as_view(),name='chat_pet'),


 path('api/pet/join', views.JoinPetFamilyView.as_view(), name='join_pet_family'),


 path('api/calories',views.CaroiesView.as_view(),name='calories'),
 path('api/calories/<int:id>', views.CaroiesView.as_view()),
 path('api/calories/list',views.CaroiesListView.as_view(),name='calories_list'),
 path('api/calories/chat',views.CaloriesChatView.as_view(),name='calories_chat'),
 path('api/calories/statistics/monthly', views.MonthlyStatisticsView.as_view(), name='monthly-stats'),
 path('api/pet/rentgen/<int:message_id>',views.PetRentgenView.as_view(),name='pet_rentgen'),
 path('api/pet/daily_check/<int:message_id>',views.PetDailyCheckView.as_view(),name='pet_daily'),
 path('api/pet/calories/<int:message_id>',views.PetCaroiesView.as_view(),name='calories_pet'),
 path('api/pet/calories/<int:message_id>/<int:id>',views.PetCaroiesView.as_view(),name='calories_pet'),
 path('api/pet/calories/list/<int:message_id>',views.PetCaroiesListView.as_view(),name='calories_list_pet'),
 path('api/pet/calories/chat/<int:message_id>',views.PetCaloriesChatView.as_view(),name='calories_chat_pet'),
 path('api/public/',views.PublicNotifcationView.as_view(),name='public_notification'),

 path('api/public/drugs',views.PublicNotificationDrugView.as_view(),name='drug_notication'),
 path('api/public/pet/drugs',views.PublicNotificationPetDrugView.as_view(),name='drug_notication'),

 path('api/drugs/delete/<int:pk>',views.DeleteDrugsView.as_view(),name='delete_drugs'),
 path('api/pet/drugs/delete/<int:pk>', views.DeletePetDrugsView.as_view(), name='delete_pet_drugs'),

 path('api/calories/edit',views.CaloriesEdit.as_view(),name='edit_caloires'),
 path('api/nutrition', views.NutritionGoalView.as_view(), name='nutrition-goal'),
 path('api/admin/list',views.AdminTestsView.as_view(),name="admin_test"),
 path('api/admin/<int:pk>',views.AdminTestDetailAPIView.as_view(),name="admin_detail"),
 path('api/pet/admin/<int:pk>/<int:pet_id>',views.AdminTestDetailAPIView.as_view(),name="admin_detail"),
 path('api/pet/nutrition/<int:message_id>', views.NutritionGoalPETView.as_view()),
 path('api/pet/calories/edit/<int:message_id>',views.CaloriesPetEdit.as_view()),
 path('api/pet/calories/statistics/monthly/<int:message_id>', views.MonthlyStatisticsPetView.as_view()),




 path('api/water_intake',views.Water_view.as_view())
]
