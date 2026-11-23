import json
from datetime import datetime
import openai
from django.utils import timezone
from .models import Calories  # Убедись, что путь к модели Calories верный

from config import KEY, MODEL
openai.api_key = KEY

# ==============================================================
# 1. СИСТЕМНЫЙ ПРОМПТ
# ==============================================================
NUTRITION_SYSTEM_PROMPT = """Ты — умный ассистент дневника питания.
Твоя задача — принимать запросы пользователя (добавление, изменение или удаление еды/воды) и вызывать инструмент `update_nutrition_log`, либо задавать уточняющие вопросы.

КРИТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ):

1. СТРОГОЕ ТРЕБОВАНИЕ К ВЫЗОВУ ИНСТРУМЕНТА:
   - Если пользователь передал достаточные данные для добавления/изменения/удаления еды или воды, ты ОБЯЗАН вызвать `update_nutrition_log`.
   - ЗАПРЕЩЕНО писать в текстовом ответе "Я добавил...", "Записал...", если ты НЕ вызвал `update_nutrition_log`. Текстовый ответ без вызова функции используется ТОЛЬКО для уточняющих вопросов.

2. НЕСКОЛЬКО ДАТ В ОДНОМ СООБЩЕНИИ (например, "19 и 20 ноября"):
   - Вычисли каждую дату относительно ТЕКУЩЕЙ ДАТЫ в формате `YYYY-MM-DD`.
   - Для КАЖДОЙ даты создай отдельный объект в массиве `entries` со своим `date`, `detail`, `total` и `added_water_ml`.
   - НИКОГДА не пропускай вторую дату и не объединяй разные дни в одну запись.
   - В итоговом `message` обязательно подтверди КАЖДУЮ созданную/обновлённую дату (например: "Добавил записи за 19 ноября и 20 ноября: ...").
   - Если дата не указана явно — передавай текущую дату в формате `YYYY-MM-DD`.

3. НАПИТКИ (ЧАЙ, КОФЕ, СОКИ) И УТОЧНЕНИЕ САХАРА:
   - В счетчик чистой воды (`water_action`, `added_water_ml`) идет ТОЛЬКО чистая питьевая вода.
   - Чай, кофе, соки и другие напитки добавляй как обычные продукты в массив `detail` со своими мл и КБЖУ.
   - Если пользователь пишет "выпил чай" или "кофе", но НЕ указывает объем ИЛИ наличие сахара/добавок, НЕ ВЫЗЫВАЙ ИНСТРУМЕНТ. Спроси текстом: "Укажите объем напитка и с сахаром/молоком или без?".
   - В `message` отвечай коротко и естественно, без технических пояснений о БД.

4. ГРАММОВКИ И ОПИСАТЕЛЬНЫЕ РАЗМЕРЫ:
   - Если не указаны ни размер, ни вес, ни количество (например: "съел бургер и фри"), спроси: "Укажите объем, вес или размер порции для: [список]".
   - Если указаны понятные размеры ("маленький бургер", "средняя порция фри", "1 яблоко", "большой стакан сока"), НЕ ТРЕБУЙ точные граммы — оцени стандартный вес и КБЖУ сам и сразу вызывай инструмент.

5. УТОЧНЕНИЕ ПРИ НЕОДНОЗНАЧНОСТИ:
   - Если пользователь просит удалить или изменить продукт ("удали чай"), но в последней записи таких продуктов несколько или запрос слишком общий, переспроси.

6. СТРОГИЙ ПЕРЕСЧЕТ `total`:
   - Источник правды при редактировании — блок "ПОСЛЕДНЯЯ ЗАПИСЬ ДНЕВНИКА В БД".
   - При изменении граммовки или удалении блюда из `detail` обязательно пересчитай сумму КБЖУ всех оставшихся элементов и запиши в `total`.

7. ДОБАВЛЕНИЕ БЕЗ ЛИШНИХ ВОПРОСОВ (`target_entry`):
   - НИКОГДА не спрашивай: "Добавить в текущую запись или создать новую?".
   - При добавлении еды всегда ставь `target_entry`: "new".
   - При изменении/удалении продуктов из записи — `target_entry`: "current".

ПРАВИЛА УДАЛЕНИЯ ВОДЫ:
- При сбросе/удалении чистой воды ставь `water_action`: "reset" и `added_water_ml`: 0.

ЕДИНИЦЫ ИЗМЕРЕНИЯ:
- Вес и объем в `detail` всегда переводи в абсолютные числа (г/мл): 500 г -> 500, 1 кг -> 1000, 1 л -> 1000."""


# ==============================================================
# 2. ОПИСАНИЕ TOOLS ДЛЯ OPENAI (С ПОДДЕРЖКОЙ МАССИВА ENTRIES)
# ==============================================================
NUTRITION_ENTRY_SCHEMA = {
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
            "description": "'current' — обновить запись за эту дату, 'new' — создать новую."
        },
        "date": {
            "type": "string",
            "description": "Дата записи в формате YYYY-MM-DD."
        },
        "water_action": {
            "type": "string",
            "enum": ["add", "reset", "set"],
            "description": "'add' — прибавить воду, 'reset' — сбросить воду в 0, 'set' — установить значение."
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
            "description": "Суммарные показатели КБЖУ всех элементов из detail.",
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
    "required": ["action_type", "target_entry", "date", "water_action", "added_water_ml", "detail", "total"]
}

NUTRITION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_nutrition_log",
            "description": "Создать или обновить одну или несколько записей в дневнике питания (в том числе сразу за несколько дат).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entries": {
                        "type": "array",
                        "description": "Список записей для сохранения. Если пользователь указал несколько дат (например, 19 и 20 ноября), передай отдельный объект для каждой даты.",
                        "items": NUTRITION_ENTRY_SCHEMA,
                        "minItems": 1
                    },
                    "message": {
                        "type": "string",
                        "description": "Краткий и естественный итоговый ответ пользователю с подтверждением ВСЕХ обработанных дат."
                    }
                },
                "required": ["entries", "message"]
            }
        }
    }
]


# ==============================================================
# 3. ИСПОЛНИТЕЛЬ ДЕЙСТВИЙ
# ==============================================================
def _parse_target_datetime(date_str):
    if not date_str:
        return None
    try:
        parsed_date = datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
        local_now = timezone.localtime(timezone.now())
        naive_dt = datetime.combine(parsed_date, local_now.time())
        return timezone.make_aware(naive_dt, timezone.get_current_timezone())
    except Exception:
        return None


def _save_single_entry(item: dict, profile_obj):
    target_entry = item.get("target_entry", "new")
    water_action = item.get("water_action", "add")
    added_water_ml = float(item.get("added_water_ml", 0) or 0)
    updated_detail = item.get("detail", [])
    updated_total = item.get("total", {})
    date_str = item.get("date")

    target_datetime = _parse_target_datetime(date_str)

    if target_datetime:
        last_entry = Calories.objects.filter(
            profile=profile_obj,
            created_at__date=target_datetime.date()
        ).order_by('-created_at').first()
    else:
        last_entry = Calories.objects.filter(profile=profile_obj).order_by('-created_at').first()

    if target_entry == "new" or last_entry is None:
        entry = Calories(profile=profile_obj, saved=True, water_intake=0.0)
    else:
        entry = last_entry

    if water_action == "reset":
        entry.water_intake = 0.0
    elif water_action == "set":
        entry.water_intake = round(added_water_ml / 1000.0, 3)
    elif water_action == "add" and added_water_ml > 0:
        current_water = float(entry.water_intake or 0.0)
        entry.water_intake = round(current_water + (added_water_ml / 1000.0), 3)

    entry.detail = updated_detail
    entry.total = updated_total
    entry.saved = True
    entry.save()

    # Надёжно выставляем нужную дату (обходит auto_now / auto_now_add)
    if target_datetime:
        Calories.objects.filter(pk=entry.pk).update(created_at=target_datetime)


def execute_nutrition_action(tool_call, profile_obj) -> str:
    if isinstance(tool_call, dict):
        raw_args = tool_call["function"]["arguments"]
    else:
        raw_args = tool_call.function.arguments

    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    message = args.get("message", "Дневник успешно обновлен.")

    # Поддерживаем и новый формат (entries: [...]), и старый плоский формат на всякий случай
    entries = args.get("entries")
    if isinstance(entries, list) and entries:
        for item in entries:
            _save_single_entry(item, profile_obj)
    else:
        _save_single_entry(args, profile_obj)

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

    local_now = timezone.localtime(timezone.now())
    now_str = local_now.strftime("%Y-%m-%d %H:%M")

    entry_created_str = None
    if entry and entry.created_at:
        entry_created_str = timezone.localtime(entry.created_at).strftime("%Y-%m-%d %H:%M")

    last_record_context = {
        "record_id": entry.id if entry else None,
        "detail": current_detail,
        "total": current_total,
        "water_intake_liters": current_water_liters,
        "created_at": entry_created_str
    }

    messages = [
        {"role": "system", "content": NUTRITION_SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"ТЕКУЩАЯ ДАТА И ВРЕМЯ СЕРВЕРА (СЕГОДНЯ): {now_str}\n\n"
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

    tool_calls = None
    if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
        tool_calls = response_msg.tool_calls
    elif isinstance(response_msg, dict) and response_msg.get("tool_calls"):
        tool_calls = response_msg.get("tool_calls")

    if tool_calls:
        results = []
        for tool_call in tool_calls:
            res_msg = execute_nutrition_action(tool_call, profile_obj)
            if res_msg and res_msg not in results:
                results.append(res_msg)
        return "\n".join(results) if results else "Дневник успешно обновлен."

    content = getattr(response_msg, "content", None) or (
        response_msg.get("content") if isinstance(response_msg, dict) else ""
    )
    return content.strip() if content else "Запрос обработан."