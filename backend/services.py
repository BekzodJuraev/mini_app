import zoneinfo
from datetime import datetime, timedelta
from django_q.tasks import schedule, async_task
from django_q.models import Schedule
from .models import Profile


import zoneinfo
from datetime import datetime, timedelta
from django_q.tasks import schedule
from django_q.models import Schedule
from .models import Profile,Drugs


def schedule_all_morning_reminders():
    profiles = Profile.objects.filter(timezone__isnull=False)

    for profile in profiles:
        user_tz_str = profile.timezone
        try:
            user_tz = zoneinfo.ZoneInfo(user_tz_str)
        except:
            user_tz = zoneinfo.ZoneInfo("Europe/Moscow")

        now_user = datetime.now(user_tz)
        today = now_user.date()

        # Вспомогательная функция для расчета времени отправки
        def get_utc_run_time(hour, minute):
            target_time = now_user.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time < now_user:
                target_time += timedelta(days=1)
            return target_time.astimezone(zoneinfo.ZoneInfo("UTC"))

        # --- ТВОИ ПРЕДЫДУЩИЕ БЛОКИ (Еда, Привычки, Калории) ---


        # 2. Привычки - напоминание (12:05)
        task_habit_remind = f"habit_remind_{profile.telegram_id}"
        Schedule.objects.filter(name=task_habit_remind).delete()
        schedule('backend.tasks.send_habit_confirmation', profile.telegram_id, name=task_habit_remind,
                 schedule_type=Schedule.ONCE, next_run=get_utc_run_time(12, 0))

        # 3. Привычки - проверка (20:00)
        task_habit_check = f"habit_check_{profile.telegram_id}"
        Schedule.objects.filter(name=task_habit_check).delete()
        schedule('backend.tasks.send_habit_not_finished_warning', profile.telegram_id, name=task_habit_check,
                 schedule_type=Schedule.ONCE, next_run=get_utc_run_time(20, 0))

        # 4. Калории (08:00)
        task_calories = f"calories_morning_{profile.telegram_id}"
        Schedule.objects.filter(name=task_calories).delete()
        schedule('backend.tasks.send_morning_food_reminder', profile.telegram_id, name=task_calories,
                 schedule_type=Schedule.ONCE, next_run=get_utc_run_time(8, 0))

        # --- НОВЫЙ БЛОК: ЛЕКАРСТВА ---
        # Просто берем все уведомления по всем лекарствам профиля
        user_drugs = Drugs.objects.filter(profile=profile)
        for drug in user_drugs:
            notifications = drug.notifications_drugs.all()
            cat = str(drug.catigories)
            d_name = str(drug.name)
            day = str(drug.day)
            time_day=str(drug.time_day)
            method = str(drug.intake)

            for notif in notifications:
                try:
                    # Парсим время "08:00" -> 8, 0
                    h, m = map(int, notif.time.split(':'))
                    drug_utc_time = get_utc_run_time(h, m)

                    # А) Основное напоминание
                    task_d = f"drug_{notif.id}_{today}"
                    Schedule.objects.filter(name=task_d).delete()
                    schedule(
                        'backend.tasks.send_medication_reminder',
                        profile.telegram_id,
                        cat,
                        d_name,
                        day,
                        time_day,
                        method,# Передаем ID времени приема в задачу
                        name=task_d,
                        schedule_type=Schedule.ONCE,
                        next_run=drug_utc_time
                    )

                    # Б) Проверка пропуска (через 1 час после приема)
                    task_c = f"check_drug_{notif.id}_{today}"
                    Schedule.objects.filter(name=task_c).delete()
                    schedule(
                        'backend.tasks.send_missed_medication_warning',
                        profile.telegram_id,
                        notif.id,
                        name=task_c,
                        schedule_type=Schedule.ONCE,
                        next_run=get_utc_run_time(23,0)
                    )
                except Exception as e:
                    print(f"Ошибка времени для уведомления {notif.id}: {e}")


