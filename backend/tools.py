import json
from django.utils import timezone
from .models import Calories  # Подставь верный импорт твоей модели Calories
import openai

from config import KEY, MODEL
openai.api_key = KEY

# ==============================================================
# 1. СИСТЕМНЫЙ ПРОМПТ
# ==============================================================
NUTRITION_SYSTEM_PROMPT = """Ты — умный ассистент дневника питания.
Твоя задача — принимать запросы пользователя (добавление еды/воды, удаление или изменение позиций) и вызывать инструмент update_nutrition_log.

СТРОГИЕ ЕДИНИЦЫ ИЗМЕРЕНИЯ (ВСЁ В ГРАММАХ И МИЛЛИЛИТРАХ):
1. Вес и объем продуктов/напитков ВСЕГДА указываются в абсолютных единицех: граммы (г) и миллилитры (мл).
   - 250 мл = 250
   - 0.5 литра / 500 мл = 500
   - 1 литр / 1000 мл = 1000
   - 1 кг = 1000
2. `added_water_ml` — количество чистой питьевой воды СТРОГО в миллилитрах (например, 250 для 250мл или 500 для 0.5л).
3. При ДОБАВЛЕНИИ: добавляй позицию в `detail` и пересчитывай `total`.
4. При УДАЛЕНИИ: убирай позицию из `detail` и пересчитывай `total`.
5. При ИЗМЕНЕНИИ: обновляй позицию в `detail` и пересчитывай `total`.
6. Если пользователь не указал вес/объем — НЕ вызывай функцию, а попроси уточнить текстом."""


# ==============================================================
# 2. ОПИСАНИЕ TOOLS ДЛЯ OPENAI
# ==============================================================
NUTRITION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_nutrition_log",
            "description": "Обновить дневник питания (добавить, изменить или удалить еду/воду) с пересчетом detail и total.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["add", "update", "delete"],
                        "description": "Тип действия."
                    },
                    "message": {
                        "type": "string",
                        "description": "Краткое текстовое сообщение для пользователя (например: 'Добавил 250мл воды в дневник!')."
                    },
                    "added_water_ml": {
                        "type": "number",
                        "description": "Количество чистой питьевой воды в миллилитрах (например, 250, 500, 1000). Если вода не добавлялась — 0."
                    },
                    "detail": {
                        "type": "array",
                        "description": "ПОЛНЫЙ список всех продуктов/напитков за сегодня. Вес/объем указывается в г/мл.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "еда": {"type": "string"},
                                "вес": {"type": "number"},
                                "ккал": {"type": "number"},
                                "белок": {"type": "number"},
                                "жир": {"type": "number"},
                                "углеводы": {"type": "number"},
                                "клетчатка": {"type": "number"}
                            },
                            "required": ["еда", "вес", "ккал", "белок", "жир", "углеводы", "клетчатка"]
                        }
                    },
                    "total": {
                        "type": "object",
                        "description": "ПОЛНЫЕ суммарные показатели КБЖУ всех элементов из detail.",
                        "properties": {
                            "вес": {"type": "number"},
                            "ккал": {"type": "number"},
                            "белок": {"type": "number"},
                            "жир": {"type": "number"},
                            "углеводы": {"type": "number"},
                            "клетчатка": {"type": "number"}
                        },
                        "required": ["вес", "ккал", "белок", "жир", "углеводы", "клетчатка"]
                    }
                },
                "required": ["action_type", "message", "added_water_ml", "detail", "total"]
            }
        }
    }
]


# ==============================================================
# 3. ИСПОЛНИТЕЛЬ ДЕЙСТВИЙ И СОХРАНЕНИЕ В DJANGO ORM
# ==============================================================
def execute_nutrition_action(tool_call, profile_obj) -> str:
    """
    Принимает аргументы от OpenAI, сохраняет detail/total (в г/мл),
    а в water_intake переводит прибавку миллилитров в литры (250мл -> +0.25л).
    """
    args = json.loads(tool_call.function.arguments)
    today = timezone.now().date()

    message = args.get("message", "Дневник успешно обновлен.")
    added_water_ml = float(args.get("added_water_ml", 0))
    updated_detail = args.get("detail", [])
    updated_total = args.get("total", {})

    entry, _ = Calories.objects.get_or_create(
        profile=profile_obj,
        created_at__date=today,
        defaults={'saved': True, 'detail': [], 'total': {}, 'water_intake': 0.0}
    )

    # Меняем ТОЛЬКО water_intake: переводим миллилитры в литры при сохранении
    if added_water_ml > 0:
        added_liters = added_water_ml / 1000.0  # 250 мл -> 0.25 л
        current_water_liters = float(entry.water_intake or 0.0)
        entry.water_intake = round(current_water_liters + added_liters, 3)

    # detail и total сохраняются как раньше (в г/мл)
    entry.detail = updated_detail
    entry.total = updated_total
    entry.saved = True
    entry.save()

    return message


# ==============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ ЧАТА ПИТАНИЯ
# ==============================================================
def nutrition_chat_system(message, profile_obj, history=None) -> str:
    today = timezone.now().date()

    # 1. Загружаем текущие данные из БД Django
    entry = Calories.objects.filter(profile=profile_obj, created_at__date=today,saved=True).last()

    current_detail = entry.detail if (entry and entry.detail) else []
    current_total = entry.total if (entry and entry.total) else {
        "вес": 0, "ккал": 0, "белок": 0, "жир": 0, "углеводы": 0, "клетчатка": 0
    }
    current_water_liters = entry.water_intake if entry else 0.0

    today_context = {
        "date": str(today),
        "detail": current_detail,
        "total": current_total,
        "water_intake_liters": current_water_liters
    }

    # 2. Формируем контекст сообщений
    messages = [
        {"role": "system", "content": NUTRITION_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"ТЕКУЩЕЕ СОСТОЯНИЕ ДНЕВНИКА ЗА СЕГОДНЯ ({today}):\n{json.dumps(today_context, ensure_ascii=False)}"
        }
    ]

    if history:
        messages.extend(history[-10:])

    messages.append({"role": "user", "content": message})

    # 3. Вызов OpenAI API
    response = openai.ChatCompletion.create(
        model=MODEL if 'MODEL' in globals() else "gpt-4o-mini",
        messages=messages,
        tools=NUTRITION_TOOLS,
        tool_choice="auto"
    )

    response_msg = response.choices[0].message

    # 4. Если ИИ вызвал функцию обновления
    if response_msg.get("tool_calls"):
        for tool_call in response_msg.tool_calls:
            return execute_nutrition_action(tool_call, profile_obj)

    # 5. Ответ простым текстом (если требуется уточнение)
    return response_msg.content.strip()