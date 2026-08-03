import json
import openai
from django.utils import timezone
from .models import Calories  # Убедись, что путь к модели Calories верный

from config import KEY, MODEL
openai.api_key = KEY

# ==============================================================
# 1. СИСТЕМНЫЙ ПРОМПТ
# ==============================================================
NUTRITION_SYSTEM_PROMPT = """Ты — умный ассистент дневника питания.
Твоя задача — принимать запросы пользователя (добавление, изменение или удаление еды/воды) и вызывать инструмент update_nutrition_log.

КРИТИЧЕСКИЕ ПРАВИЛА ИЗМЕНЕНИЯ И УДАЛЕНИЯ:
1. Твой ЕДИНСТВЕННЫЙ источник правды — системный блок "ПОСЛЕДНЯЯ ЗАПИСЬ ДНЕВНИКА В БД".
2. При РЕДАКТИРОВАНИИ (например, "поменяй 1 кг на 500 г"):
   - Найди продукт в `detail`, измени его вес и пропорционально пересчитай КБЖУ (ккал, белок, жир, углеводы).
   - Обнови итоговые данные в `total`.
3. При УДАЛЕНИИ ВОДЫ/ЖИДКОСТИ (например, "убери воду", "обнули воду"):
   - Установи `water_action` в значение "reset".
   - Установи `added_water_ml` в 0.
   - Убери упоминания воды из `detail` (если она там была) и пересчитай `total`.

УТОЧНЕНИЕ ПРИ ДОБАВЛЕНИИ:
1. Если пользователь просит ДОБАВИТЬ еду/воду, И В ПОСЛЕДНЕЙ ЗАПИСИ УЖЕ ЕСТЬ ПРОДУКТЫ (`detail` НЕ пустой):
   - Сначала СПРОСИ текстом: "Добавить [название продукта] в текущую запись или создать новую?"
   - ИСКЛЮЧЕНИЕ: Если пользователь сам сразу указал контекст ("добавь в новую запись", "измени в текущей", "убери из последней"), сразу вызывай инструмент.
2. Если последняя запись ПУСТАЯ — сразу вызывай инструмент без вопросов.

ФЛАГИ В ИНСТРУМЕНТЕ:
- `target_entry`: "current" (текущая запись) или "new" (создать новую).
- `water_action`:
    * "add" — прибавить `added_water_ml` к текущей воде в БД.
    * "reset" — полностью сбросить/удалить воду (установить water_intake = 0).
    * "set" — установить точный объем воды равным `added_water_ml`.

ЕДИНИЦЫ ИЗМЕРЕНИЯ (СТРОГО В ГРАММАХ И МИЛЛИЛИТРАХ):
- Вес и объем всегда в абсолютных числах (г/мл): 500 г -> 500, 1 кг -> 1000, 1 л -> 1000."""


# ==============================================================
# 2. ОПИСАНИЕ TOOLS ДЛЯ OPENAI
# ==============================================================
NUTRITION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_nutrition_log",
            "description": "Обновить или создать запись в дневнике питания (добавить, изменить или удалить еду/воду).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {
                        "type": "string",
                        "enum": ["add", "update", "delete"],
                        "description": "Тип действия."
                    },
                    "target_entry": {
                        "type": "string",
                        "enum": ["current", "new"],
                        "description": "'current' — обновить последнюю запись, 'new' — создать новую."
                    },
                    "water_action": {
                        "type": "string",
                        "enum": ["add", "reset", "set"],
                        "description": "'add' — прибавить воду, 'reset' — сбросить воду в 0, 'set' — установить конкретное значение."
                    },
                    "message": {
                        "type": "string",
                        "description": "Краткий ответ пользователю."
                    },
                    "added_water_ml": {
                        "type": "number",
                        "description": "Количество воды/жидкости в мл."
                    },
                    "detail": {
                        "type": "array",
                        "description": "Актуальный полный список продуктов записи.",
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
                        "description": "Пересчитанные суммарные показатели КБЖУ всех элементов из detail.",
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
                "required": ["action_type", "target_entry", "water_action", "message", "added_water_ml", "detail", "total"]
            }
        }
    }
]


# ==============================================================
# 3. ИСПОЛНИТЕЛЬ ДЕЙСТВИЙ (ОБРАБОТКА ВОДЫ И ГРАММОВОК)
# ==============================================================
def execute_nutrition_action(tool_call, profile_obj) -> str:
    args = json.loads(tool_call.function.arguments)

    message = args.get("message", "Дневник успешно обновлен.")
    target_entry = args.get("target_entry", "current")
    water_action = args.get("water_action", "add")
    added_water_ml = float(args.get("added_water_ml", 0))
    updated_detail = args.get("detail", [])
    updated_total = args.get("total", {})

    last_entry = Calories.objects.filter(profile=profile_obj).order_by('-created_at').first()

    # Создание новой записи или получение текущей
    if target_entry == "new" or last_entry is None:
        entry = Calories(profile=profile_obj, saved=True, water_intake=0.0)
    else:
        entry = last_entry

    # ОБРАБОТКА ВОДЫ (water_intake)
    if water_action == "reset":
        entry.water_intake = 0.0
    elif water_action == "set":
        entry.water_intake = round(added_water_ml / 1000.0, 3)
    elif water_action == "add" and added_water_ml > 0:
        added_liters = added_water_ml / 1000.0
        current_water = float(entry.water_intake or 0.0)
        entry.water_intake = round(current_water + added_liters, 3)

    entry.detail = updated_detail
    entry.total = updated_total
    entry.saved = True
    entry.save()

    return message


# ==============================================================
# 4. ОСНОВНАЯ ФУНКЦИЯ ЧАТА ПИТАНИЯ
# ==============================================================
def nutrition_chat_system(message, profile_obj, history=None) -> str:
    entry = Calories.objects.filter(profile=profile_obj).order_by('-created_at').first()

    current_detail = entry.detail if (entry and entry.detail) else []
    current_total = entry.total if (entry and entry.total) else {
        "вес": 0, "ккал": 0, "белок": 0, "жир": 0, "углеводы": 0, "клетчатка": 0
    }
    current_water_liters = entry.water_intake if entry else 0.0

    last_record_context = {
        "record_id": entry.id if entry else None,
        "detail": current_detail,
        "total": current_total,
        "water_intake_liters": current_water_liters
    }

    messages = [
        {"role": "system", "content": NUTRITION_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"ПОСЛЕДНЯЯ ЗАПИСЬ ДНЕВНИКА В БД:\n"
                f"{json.dumps(last_record_context, ensure_ascii=False)}\n\n"
                f"При удалении воды всегда передавай water_action='reset'."
            )
        }
    ]

    if history:
        messages.extend(history[-4:])

    messages.append({"role": "user", "content": message})

    response = openai.ChatCompletion.create(
        model=MODEL if 'MODEL' in globals() else "gpt-4o-mini",
        messages=messages,
        tools=NUTRITION_TOOLS,
        tool_choice="auto"
    )

    response_msg = response.choices[0].message

    if response_msg.get("tool_calls"):
        for tool_call in response_msg.tool_calls:
            return execute_nutrition_action(tool_call, profile_obj)

    return response_msg.content.strip()