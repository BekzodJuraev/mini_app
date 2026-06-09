from threading import Thread
from .prompt import life_expectancy,health_recommendations,environmental_risk_analysis,monthly_pressure_analysis,pulse_diary_analysis,environmental_and_data_risk_analysis_pet
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date
from datetime import timedelta
from django.utils import timezone
from django.db import models


def pet_risk_analysis_decorator(fields_to_track=None):
    """
    Универсальный декоратор для моделей Pet, Tests_Pet и PetChat.
    Следит за изменениями полей и запускает ИИ-анализ рисков в фоне.
    """
    if isinstance(fields_to_track, type) and issubclass(fields_to_track, models.Model):
        model_class = fields_to_track
        return make_decorated_model(model_class, fields_to_track=None)

    def decorator(model_class):
        return make_decorated_model(model_class, fields_to_track)

    return decorator


def make_decorated_model(model_class, fields_to_track):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        trigger_analysis = False

        # 1. Проверяем, изменились ли отслеживаемые поля
        if fields_to_track and self.pk:
            try:
                old_instance = model_class.objects.get(pk=self.pk)
                for field in fields_to_track:
                    if getattr(old_instance, field) != getattr(self, field):
                        trigger_analysis = True
                        break
            except model_class.DoesNotExist:
                trigger_analysis = True
        else:
            # Если поля не переданы или запись новая — триггерим железно
            trigger_analysis = True

        # 2. Сохраняем объект (база присваивает pk)
        original_save(self, *args, **kwargs)

        # 3. Если нужно делать анализ — вычисляем, кто вызвал save() и ищем инстанс Pet
        if trigger_analysis:
            pet_instance = None

            # Если декоратор висит на самой модели Pet
            if hasattr(self, 'tests_pet') and hasattr(self, 'chat'):
                pet_instance = self

            # Если декоратор висит на Tests_Pet или PetChat — прыгаем в связанного питомца через ForeignKey
            elif hasattr(self, 'pet') and isinstance(self.pet, models.Model):
                pet_instance = self.pet

            # Если нашли питомца — погнали в фон
            if pet_instance and pet_instance.pk:

                def run_pet_analysis():
                    try:
                        # А) Вытаскиваем последние 30 сообщений из Tests_Pet
                        recent_tests = list(
                            pet_instance.tests_pet.exclude(message=None).order_by('-created_at', '-id')[:30]
                        )
                        recent_tests.reverse()
                        messages_history = [t.message for t in recent_tests if t.message]

                        # Б) ВЫТАСКИВАЕМ ПОСЛЕДНИЕ 10 ВОПРОСОВ ИЗ ЧАТА (PetChat)
                        # Исключаем пустые вопросы, если юзер отправил только картинку
                        recent_chats = list(
                            pet_instance.chat.exclude(question=None).order_by('-created_at', '-id')[:20]
                        )
                        recent_chats.reverse()  # В хронологическом порядке
                        chat_questions_history = [c.question for c in recent_chats if c.question]

                        # Собираем полный фарш данных для ИИ
                        pet_payload = {
                            "user_timezone": pet_instance.profile.timezone if (
                                        pet_instance.profile and hasattr(pet_instance.profile, 'timezone')) else None,
                            "pet_name": pet_instance.klichka,
                            "pet_type": pet_instance.pet,
                            "pet_birth_date": pet_instance.age.strftime('%Y-%m-%d') if pet_instance.age else None,
                            "pet_gender": pet_instance.gender,
                            "health_metrics": pet_instance.health_system or {},
                            "messages_history_last_30": messages_history,  # История анализов/сообщений
                            "recent_user_questions_from_chat": chat_questions_history,  # Твои вопросы из чата!
                            "current_symptoms": pet_instance.risk_test  # Что ввели вручную в профиле
                        }

                        # Стучимся в твою функцию OpenAI
                        ai_result = environmental_and_data_risk_analysis_pet(pet_payload)

                        # Обновляем поле risk_test у питомца чистым текстом отчета
                        pet_instance.__class__.objects.filter(pk=pet_instance.pk).update(
                            risk_test=ai_result.get("message", "Ошибка генерации отчета.")
                        )

                    except Exception as e:
                        print(f"Ошибка фонового анализа (универсальный декоратор + чат): {e}")

                Thread(target=run_pet_analysis, daemon=True).start()

    model_class.save = new_save
    return model_class
def pulse_diary_decorator(model_class):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Сначала стандартно сохраняем текущий тест/запись дневника в базу
        original_save(self, *args, **kwargs)

        # 2. Уходим в фоновый поток для работы с ИИ
        def run_pulse_analysis():
            try:
                p = self.profile
                if p:
                    # Вычисляем точку отсчета — 30 дней назад
                    start_date = timezone.now() - timedelta(days=30)

                    # Вытаскиваем максимум 7 последних непустых сообщений за месяц
                    test_answers = list(
                        p.tests.filter(
                            message__isnull=False,
                            created_at__gte=start_date
                        )
                        .exclude(message="")
                        .order_by('-created_at')
                        .values_list('message', flat=True)[:20]
                    )

                    # Если история за этот месяц есть, скармливаем её ИИ
                    if test_answers:
                        # Запускаем новый промпт для дневника пульса
                        result = pulse_diary_analysis(test_answers)
                        ai_message = result.get("message", "")

                        if ai_message:
                            # Обновляем именно поле diary_plus в профиле напрямую через SQL
                            p.__class__.objects.filter(pk=p.pk).update(
                                diary_plus=ai_message
                            )
            except Exception as e:
                print(f"Ошибка при работе ИИ в декораторе дневника пульса: {e}")

        # Запускаем асинхронно, чтобы не тормозить фронтенд при сохранении
        Thread(target=run_pulse_analysis, daemon=True).start()

    model_class.save = new_save
    return model_class
def monthly_report_only_tests_decorator(model_class):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Сначала стандартно сохраняем текущий тест в базу
        original_save(self, *args, **kwargs)

        # 2. Уходим в фон собирать историю за последние 30 дней и отправлять в ИИ
        def run_analysis():
            try:
                p = self.profile
                if p:
                    # Вычисляем точку отсчета — 30 дней назад
                    start_date = timezone.now() - timedelta(days=30)

                    # Вытаскиваем максимум 7 ответов ИИ строго за последние 30 дней
                    test_answers = list(
                        p.tests.filter(
                            message__isnull=False,
                            created_at__gte=start_date  # Фильтр за последние 30 дней
                        )
                        .exclude(message="")
                        .order_by('-created_at')
                        .values_list('message', flat=True)[:20]
                    )

                    if test_answers:
                        result = monthly_pressure_analysis(test_answers)
                        ai_message = result.get("message", "")

                        if ai_message:
                            p.__class__.objects.filter(pk=p.pk).update(
                                pressure_plus=ai_message
                            )
            except Exception as e:
                print(f"Ошибка при работе ИИ в декораторе тестов: {e}")

        Thread(target=run_analysis, daemon=True).start()

    model_class.save = new_save
    return model_class
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