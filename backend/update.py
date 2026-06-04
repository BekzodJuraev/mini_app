from threading import Thread
from .prompt import life_expectancy,health_recommendations,environmental_risk_analysis
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date


def environmental_risk_decorator(model_class):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Проверяем, изменился ли именно timezone
        is_timezone_changed = False
        if self.pk:
            try:
                # Берем старое значение из БД
                old_instance = self.__class__.objects.get(pk=self.pk)
                if old_instance.timezone != self.timezone:
                    is_timezone_changed = True
            except self.__class__.DoesNotExist:
                # Если это создание нового объекта, тоже триггерим
                is_timezone_changed = True
        else:
            # Новый объект (без PK)
            is_timezone_changed = True

        # 2. Сохраняем объект
        original_save(self, *args, **kwargs)

        # 3. Если timezone изменился — запускаем ИИ в фоне
        if is_timezone_changed and self.timezone:
            def run_analysis():
                try:
                    # Вызываем промпт, передавая только timezone
                    result = environmental_risk_analysis(self.timezone)

                    # Сохраняем результат в поле (например, env_risks_json)
                    # Используем .update() чтобы не вызвать save() повторно
                    self.__class__.objects.filter(pk=self.pk).update(
                        risk_test=result.get("message", "")
                        # Если у тебя есть поле для штрафа к легким:
                    )
                except Exception as e:
                    print(f"Error in environmental analysis: {e}")

            Thread(target=run_analysis, daemon=True).start()

    model_class.save = new_save
    return model_class
def update_life_expectancy_decorator(model_class):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Сохраняем модель (Profile, Habit, BloodPressure и т.д.)
        original_save(self, *args, **kwargs)

        def run_update():
            try:

                p = self if hasattr(self, 'life_expectancy_json') else self.profile

                # 1. Последнее давление и пульс из BloodPressure (если есть)
                last_bp = p.pressure_history.order_by('-created_at').first()

                # 2. Список привычек из Habit
                habits_list = list(p.habit.values_list('name_habit', flat=True))

                # 3. Результаты тестов (из модели Tests)
                # Берем последние 7 записей, где есть осмысленный текст (анализы, ответы)
                test_answers = list(
                    p.tests.filter(message__isnull=False)
                    .exclude(message="")
                    .order_by('-created_at')
                    .values_list('message', flat=True)[:7]
                )

                # Формируем структуру данных строго по делу
                raw_data = {
                    "date_birth": p.date_birth,
                    "gender": p.gender,
                    "region": p.place_of_residence,
                    "habits": habits_list,
                    "blood_pressure": {
                        "systolic": last_bp.pressure_top if last_bp else None,
                        "diastolic": last_bp.pressure_bottom if last_bp else None,
                    },
                    "medical_context": {
                        "recent_test_results": test_answers  # Текстовые ответы из Tests
                    }
                }

                # Очистка данных для JSON (убираем ошибки сериализации дат)
                user_data = json.loads(json.dumps(raw_data, cls=DjangoJSONEncoder))

                # 4. Вызываем твой промпт life_expectancy
                result = life_expectancy(user_data)

                # 5. Сохраняем результат в Profile через .update()
                p.__class__.objects.filter(pk=p.pk).update(
                    life_expectancy_json=result.get("message", "")
                )

            except Exception as e:
                print(f"Ошибка в работе ИИ (Life Expectancy Update): {e}")

        # Запускаем в фоне
        Thread(target=run_update, daemon=True).start()

    model_class.save = new_save
    return model_class


def health_recommendations_decorator(model_class):
    """
    Декоратор: передает date_birth, детализацию питания (detail),
    данные Rentgen и историю Tests. Без агрегированных средних значений.
    """
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Сохраняем модель в базу
        original_save(self, *args, **kwargs)

        def run_update():
            try:
                # Определяем профиль
                p = self if hasattr(self, 'life_expectancy_json') else self.profile

                # --- CALORIES: Только текстовые подробности (detail) последних записей ---
                # Берем последние 5 записей о питании
                food_details = list(
                    p.cal.order_by('-created_at')[:5].values_list('detail', flat=True)
                )

                # --- RENTGEN: Последние заключения ---
                rentgen_data = list(
                    p.rentgen.all().order_by('-created_at')
                    .values_list('answer')[:5]
                )

                # --- TESTS: История расшифровок ИИ ---
                test_history = list(
                    p.tests.filter(message__isnull=False)
                    .exclude(message="")
                    .order_by('-created_at')
                    .values_list('message', flat=True)[:7]
                )

                # --- ФОРМИРУЕМ ОБЪЕКТ user_data ---
                raw_data = {
                    "profile": {
                        "date_birth": p.date_birth,
                        "gender": p.gender,
                        "region": p.place_of_residence
                    },
                    "nutrition_context": {
                        "recent_food_details": food_details  # Только текстовые детали
                    },
                    "medical_imaging": rentgen_data,  # Данные из Rentgen
                    "recent_test_results": test_history  # Данные из Tests
                }

                # Сериализация (даты в строки)
                user_data = json.loads(json.dumps(raw_data, cls=DjangoJSONEncoder))

                # 2. Вызываем функцию ИИ
                result = health_recommendations(user_data)

                # 3. Обновляем текстовое поле в Profile
                p.__class__.objects.filter(pk=p.pk).update(
                    health_recommendations=result.get("message", "")
                )

            except Exception as e:
                print(f"Ошибка в обновлении рекомендаций: {e}")

        # Фоновый запуск
        Thread(target=run_update, daemon=True).start()

    model_class.save = new_save
    return model_class