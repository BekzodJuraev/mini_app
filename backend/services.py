import zoneinfo
from datetime import datetime, timedelta
from django_q.tasks import schedule, async_task
from django_q.models import Schedule
from .models import Profile


import zoneinfo
from datetime import datetime, timedelta
from django_q.tasks import schedule
from django_q.models import Schedule
from .models import Profile

def schedule_all_morning_reminders():
    profiles = Profile.objects.filter(timezone__isnull=False)

    for profile in profiles:
        user_tz_str = profile.timezone
        try:
            user_tz = zoneinfo.ZoneInfo(user_tz_str)
        except:
            user_tz = zoneinfo.ZoneInfo("Europe/Moscow")

        now_user = datetime.now(user_tz)

        # Вспомогательная функция для расчета времени отправки
        def get_utc_run_time(hour, minute):
            target_time = now_user.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time < now_user:
                target_time += timedelta(days=1)
            return target_time.astimezone(zoneinfo.ZoneInfo("UTC"))

        # 1. Твое старое уведомление (Еда 11:30)
        task_food = f"morning_food_{profile.telegram_id}"
        Schedule.objects.filter(name=task_food).delete() # Удаляем старое, чтобы не было ошибки IntegrityError
        schedule(
            'backend.tasks.send_morning_food_reminder',
            profile.telegram_id,
            name=task_food,
            schedule_type=Schedule.ONCE,
            next_run=get_utc_run_time(12, 10)
        )

        # 2. ПОДТВЕРЖДЕНИЕ ПРИВЫЧКИ (12:00) — из изображение_6.png
        task_habit_remind = f"habit_remind_{profile.telegram_id}"
        Schedule.objects.filter(name=task_habit_remind).delete()
        schedule(
            'backend.tasks.send_habit_confirmation', # Не забудь создать эту функцию в tasks.py
            profile.telegram_id,
            name=task_habit_remind,
            schedule_type=Schedule.ONCE,
            next_run=get_utc_run_time(12, 5)
        )

        # 3. ПРОВЕРКА ВЫПОЛНЕНИЯ (20:00) — из изображение_6.png
        task_habit_check = f"habit_check_{profile.telegram_id}"
        Schedule.objects.filter(name=task_habit_check).delete()
        schedule(
            'backend.tasks.send_habit_not_finished_warning', # Не забудь создать эту функцию в tasks.py
            profile.telegram_id,
            name=task_habit_check,
            schedule_type=Schedule.ONCE,
            next_run=get_utc_run_time(20, 0)
        )


