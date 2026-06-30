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

        # --- БЛОК 2 И 3: ПРИВЫЧКИ ---
        task_habit_remind = f"habit_remind_{profile.telegram_id}"
        task_habit_check = f"habit_check_{profile.telegram_id}"

        # Сначала всегда чистим старые таски на сегодня, чтобы не дублировать
        Schedule.objects.filter(name=task_habit_remind).delete()
        Schedule.objects.filter(name=task_habit_check).delete()

        # Делаем schedule ТОЛЬКО если уведомления включены
        if profile.notification_habit:
            schedule('backend.tasks.send_habit_confirmation', profile.telegram_id, name=task_habit_remind,
                     schedule_type=Schedule.ONCE, next_run=get_utc_run_time(12, 5))

            schedule('backend.tasks.send_habit_not_finished_warning', profile.telegram_id, name=task_habit_check,
                     schedule_type=Schedule.ONCE, next_run=get_utc_run_time(20, 0))

        # --- БЛОК 4: КАЛОРИИ И ПИТАНИЕ ---
        task_calories = f"calories_morning_{profile.telegram_id}"
        Schedule.objects.filter(name=task_calories).delete()

        if profile.notification_calories:
            schedule('backend.tasks.send_morning_food_reminder', profile.telegram_id, name=task_calories,
                     schedule_type=Schedule.ONCE, next_run=get_utc_run_time(8, 0))

        # --- НОВЫЙ БЛОК: НАПОМИНАНИЯ О ЗДОРОВЬЕ (ДАВЛЕНИЕ В 18:02) ---
        task_health = f"health_morning_{profile.telegram_id}"
        Schedule.objects.filter(name=task_health).delete()

        if profile.notification_health:
            schedule('backend.tasks.send_health_reminder', profile.telegram_id, name=task_health,
                     schedule_type=Schedule.ONCE, next_run=get_utc_run_time(8, 0))

        # --- БЛОК: ЛЕКАРСТВА ---
        # Если лекарства вообще выключены в профиле, сразу переходим к следующему пользователю
        if not profile.notification_drugs:
            # Нам всё равно нужно почистить старые задачи по лекарствам, если они были в базе
            user_drugs = Drugs.objects.filter(profile=profile)
            for drug in user_drugs:
                for notif in drug.notifications_drugs.all():
                    Schedule.objects.filter(name=f"drug_{notif.id}_{today}").delete()
                    Schedule.objects.filter(name=f"check_drug_{notif.id}_{today}").delete()
            continue  # Пропускаем и идем к следующему профилю

        # Если notification_drugs == True, то спокойно крутим цикл и планируем
        user_drugs = Drugs.objects.filter(profile=profile)
        for drug in user_drugs:
            notifications = drug.notifications_drugs.all()
            cat = str(drug.catigories)
            d_name = str(drug.name)
            day = str(drug.day)
            time_day = str(drug.time_day)
            method = str(drug.intake)

            for notif in notifications:
                task_d = f"drug_{notif.id}_{today}"
                task_c = f"check_drug_{notif.id}_{today}"

                Schedule.objects.filter(name=task_d).delete()
                Schedule.objects.filter(name=task_c).delete()

                try:
                    h, m = map(int, notif.time.split(':'))
                    drug_utc_time = get_utc_run_time(h, m)

                    # А) Основное напоминание
                    schedule(
                        'backend.tasks.send_medication_reminder',
                        profile.telegram_id,
                        cat,
                        d_name,
                        day,
                        time_day,
                        method,
                        name=task_d,
                        schedule_type=Schedule.ONCE,
                        next_run=drug_utc_time
                    )

                    # Б) Проверка пропуска (23:00)
                    schedule(
                        'backend.tasks.send_missed_medication_warning',
                        profile.telegram_id,
                        notif.id,
                        name=task_c,
                        schedule_type=Schedule.ONCE,
                        next_run=get_utc_run_time(23, 0)
                    )
                except Exception as e:
                    print(f"Ошибка времени для уведомления {notif.id}: {e}")


