from threading import Thread
from .prompt import life_expectancy
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date

def update_life_expectancy_decorator(model_class):
    original_save = model_class.save

    def new_save(self, *args, **kwargs):
        # 1. Сохраняем текущую модель (Habit, Tests и т.д.)
        original_save(self, *args, **kwargs)

        def run_update():
            try:
                # Получаем профиль (у твоих моделей это self.profile)
                p = self.profile

                # Собираем данные из связанных таблиц согласно скриншоту
                last_test = p.tests.order_by('-created_at').first()
                habits_list = list(p.habit.values_list('name_habit', flat=True))
                # Квесты/опросы (Quest)
                completed_quests = p.quest.count()

                # Формируем структуру строго по списку на картинке
                user_data = {
                    "age": (date.today() - p.date_birth).days // 365 if p.date_birth else None,
                    "gender": p.gender,
                    "region": p.place_of_residence,
                    "habits": habits_list,
                    "blood_pressure": {
                        "systolic": last_test.pressure_top if last_test else None,
                        "diastolic": last_test.pressure_bottom if last_test else None
                    },
                    #"pulse": last_test.pulse if last_test and hasattr(last_test, 'pulse') else None,
                    "lifestyle": {
                        "completed_quests": completed_quests,
                    }
                }

                # Вызываем твой промпт
                result = life_expectancy(user_data)

                # Сохраняем ТОЛЬКО в текстовое поле JSON-результат
                p.__class__.objects.filter(pk=p.pk).update(
                    life_expectancy_json=result.get("message", "")
                )
            except Exception as e:
                print(f"Ошибка в работе ИИ: {e}")

        # Запускаем в фоне
        Thread(target=run_update, daemon=True).start()

    model_class.save = new_save
    return model_class