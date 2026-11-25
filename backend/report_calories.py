from datetime import timedelta
from django.utils import timezone
from .prompt import get_nutrition_ai_analysis
from .models import Calories, NutritionGoal, CaloriesReportProfile


def calculate_monthly_nutrition_stats(profile):
    """
    Считает статистику питания за последние 30 дней только по подтвержденным записям (saved=True):
    - проценты выполнения нормы калорий по дням БЕЗ обрезки на 100%
    - среднюю частоту приёмов пищи в день (за дни, когда велись записи)
    - средние КБЖУ, клетчатку и воду за активные дни
    """
    today = timezone.localtime(timezone.now()).date()
    start_date = today - timedelta(days=29)
    dates_list = [start_date + timedelta(days=i) for i in range(30)]

    records = Calories.objects.filter(
        profile=profile,
        created_at__date__range=(start_date, today),
        saved=True
    )

    if not records.exists():
        return None

    goal = NutritionGoal.objects.filter(profile=profile).first()
    goal_calories = goal.calories if (goal and goal.calories and goal.calories > 0) else 0

    daily_totals = {}
    for r in records:
        dt = timezone.localtime(r.created_at) if timezone.is_aware(r.created_at) else r.created_at
        d = dt.date()
        if d not in daily_totals:
            daily_totals[d] = {
                'meals_count': 0,
                'kcal': 0.0,
                'protein': 0.0,
                'fat': 0.0,
                'carbs': 0.0,
                'fiber': 0.0,
                'water': 0.0,
            }

        daily_totals[d]['meals_count'] += 1

        if isinstance(r.total, dict):
            daily_totals[d]['kcal'] += float(r.total.get('ккал', 0) or 0)
            daily_totals[d]['protein'] += float(r.total.get('белок', 0) or 0)
            daily_totals[d]['fat'] += float(r.total.get('жир', 0) or 0)
            daily_totals[d]['carbs'] += float(r.total.get('углеводы', 0) or 0)
            daily_totals[d]['fiber'] += float(r.total.get('клетчатка', 0) or 0)

        # Вода за приём: чистая вода (water_intake) + вода внутри продуктов из detail
        water_from_food = 0.0
        if isinstance(r.detail, list):
            for item in r.detail:
                if isinstance(item, dict):
                    water_from_food += float(item.get('вода', 0) or 0)

        daily_totals[d]['water'] += float(r.water_intake or 0) + water_from_food

    active_days_count = len(daily_totals)
    avg_meals = round(sum(x['meals_count'] for x in daily_totals.values()) / active_days_count, 1)
    avg_kcal = round(sum(x['kcal'] for x in daily_totals.values()) / active_days_count)
    avg_protein = round(sum(x['protein'] for x in daily_totals.values()) / active_days_count)
    avg_fat = round(sum(x['fat'] for x in daily_totals.values()) / active_days_count)
    avg_carbs = round(sum(x['carbs'] for x in daily_totals.values()) / active_days_count)
    avg_fiber = round(sum(x['fiber'] for x in daily_totals.values()) / active_days_count)
    avg_water = round(sum(x['water'] for x in daily_totals.values()) / active_days_count, 2)

    # Проценты выполнения дневной нормы калорий за каждый из 30 дней (без обрезки на 100%)
    percentages_list = []
    if goal_calories > 0:
        for d in dates_list:
            day_kcal = daily_totals.get(d, {}).get('kcal', 0.0)
            pct = round((day_kcal / goal_calories) * 100, 1)
            percentages_list.append(pct)

    return {
        "dates_list": dates_list,
        "percentages_list": percentages_list,
        "has_goal": goal_calories > 0,
        "goal": (
            {
                "calories": goal.calories,
                "proteins": goal.proteins,
                "fats": goal.fats,
                "carbs": goal.carbs,
                "fiber": goal.fiber,
            }
            if goal_calories > 0
            else None
        ),
        "averages": {
            "meals_per_day": avg_meals,
            "calories": avg_kcal,
            "water_liters": avg_water,
            "carbs": avg_carbs,
            "proteins": avg_protein,
            "fiber": avg_fiber,
            "fats": avg_fat,
            "active_days": active_days_count,
        }
    }


def update_nutrition_ai_report_for_profile(profile):
    """
    Пересчитывает статистику за 30 дней и сохраняет актуальный ответ ИИ в CaloriesReportProfile.
    """
    stats = calculate_monthly_nutrition_stats(profile)
    if not stats:
        return

    payload_for_ai = {
        "has_goal": stats["has_goal"],
        "user_goal": stats["goal"],  # None, если цель удалена
        "monthly_averages": stats["averages"],
        "instruction": (
            "Цель по калориям НЕ задана. СТРОГО ЗАПРЕЩЕНО сравнивать питание с какой-либо целью или упоминать прежние цели."
            if not stats["has_goal"]
            else f"Актуальная цель по калориям: {stats['goal']['calories']} ккал. Используй строго эти актуальные цифры."
        ),
    }

    try:
        ai_res = get_nutrition_ai_analysis(payload_for_ai)
        CaloriesReportProfile.objects.update_or_create(
            profile=profile,
            defaults={
                "diet_report": ai_res.get("diet_report", ""),
                "general_recommendations": ai_res.get("general_recommendations", ""),
            }
        )
    except Exception as e:
        print(f"Error generating nutrition AI report: {e}")