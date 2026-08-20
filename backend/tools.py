import json
import openai
from django.utils import timezone
from .models import Calories  # Убедись, что путь к модели Calories верный

from config import KEY, MODEL
openai.api_key = KEY

# ==============================================================
# 1. СИСТЕМНЫЙ ПРОМПТ (ОБНОВЛЕННЫЕ ПРАВИЛА)
# ==============================================================
NUTRITION_SYSTEM_PROMPT = """Ты — умный ассистент дневника питания.
Твоя задача — принимать запросы пользователя (добавление, изменение или удаление еды/воды) и вызывать инструмент update_nutrition_log, либо задавать уточняющие вопросы.

КРИТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ):

1. ЧАЙ, КОФЕ, СОКИ И НАПИТКИ — ЭТО ЕДА, А НЕ ВОДА:
   - В счетчик воды (параметры `water_action` и `added_water_ml`) идет ТОЛЬКО чистая вода.
   - Чай, кофе, соки, лимонады и любые другие жидкости добавляй как обычные продукты в массив `detail` со своими граммовками/мл и КБЖУ (даже если там 0 ккал).

2. СТРОГОЕ УТОЧНЕНИЕ ГРАММОВОК И ПОРЦИЙ:
   - НИКОГДА не придумывай вес, объем или размер порции самостоятельно!
   - Если пользователь просит добавить еду или напиток, но НЕ указал вес или объем (например: "съел бургер и фри", "выпил чай"), НЕ ВЫЗЫВАЙ ИНСТРУМЕНТ. Ответь обычным текстом и спроси: "Укажите вес или размер порции для: [перечисли продукты]".

3. УТОЧНЕНИЕ ПРИ НЕОДНОЗНАЧНОСТИ:
   - Если пользователь просит удалить или изменить продукт ("удали чай", "исправь напиток"), но в последней записи таких продуктов несколько или запрос слишком общий, переспроси, что именно он имеет в виду.

4. СТРОГИЙ ПЕРЕСЧЕТ `total` ПРИ ИЗМЕНЕНИЯХ И УДАЛЕНИЯХ:
   - Твой единственный источник правды — блок "ПОСЛЕДНЯЯ ЗАПИСЬ ДНЕВНИКА В БД".
   - Если ты ИЗМЕНЯЕШЬ граммовку блюда или УДАЛЯЕШЬ блюдо из `detail`, ты ОБЯЗАН заново просуммировать КБЖУ всех оставшихся элементов в `detail` и обновить объект `total`. 
   - НИКОГДА не оставляй старый `total`, если состав `detail` изменился. Сумма должна сходиться математически!

5. ДОБАВЛЕНИЕ БЕЗ ЛИШНИХ ВОПРОСОВ (target_entry):
   - НИКОГДА НЕ СПРАШИВАЙ пользователя: "Добавить в текущую запись или создать новую?".
   - Если пользователь ДОБАВЛЯЕТ новую еду — всегда создавай новую запись (`target_entry`: "new"), чтобы фиксировать каждый прием пищи отдельно.
   - Если пользователь РЕДАКТИРУЕТ или УДАЛЯЕТ продукты из последней записи — обновляй текущую (`target_entry`: "current").

ПРАВИЛА УДАЛЕНИЯ ВОДЫ:
- При сбросе/удалении чистой воды устанавливай `water_action`: "reset" и `added_water_ml`: 0.

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
                        "description": "Краткий ответ пользователю. Например, 'Записал!', 'Удалил блюдо' и т.д."
                    },
                    "added_water_ml": {
                        "type": "number",
                        "description": "Количество чистой воды в мл."
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
    target_entry = args.get("target_entry", "new")  # По умолчанию новая запись для надежности
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

    # ОБРАБОТКА ВОДЫ (water_intake) - Сюда попадает только вода, т.к. чай уходит в detail
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

    # Если ИИ решил вызвать функцию (все данные есть)
    if response_msg.get("tool_calls"):
        for tool_call in response_msg.tool_calls:
            return execute_nutrition_action(tool_call, profile_obj)

    # Если ИИ решил ответить текстом (например, просит уточнить граммовку)
    return response_msg.content.strip()