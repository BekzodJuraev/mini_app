import json
from datetime import datetime
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

1. СТРОГОЕ ТРЕБОВАНИЕ К ВЫЗОВУ ИНСТРУМЕНТА:
   - Если пользователь передал достаточные данные для добавления/изменения/удаления еды или воды, ты ОБЯЗАН вызвать функцию `update_nutrition_log`.
   - ЗАПРЕЩЕНО писать в текстовом ответе "Я добавил...", "Записал...", если ты НЕ вызвал функцию `update_nutrition_log`. Простой текстовый ответ без вызова функции используется ТОЛЬКО для уточняющих вопросов!

2. ДАТЫ И ЗАПИСИ ЗА ПРОШЛЫЕ ДНИ ("ВЧЕРА", "ПОЗАВЧЕРА", КОНКРЕТНАЯ ДАТА):
   - Обращай внимание на указание даты. Если пользователь пишет "вчера", "позавчера", "в прошедший понедельник" или указывает дату (например, "15 мая"), вычисли эту дату относительно ТЕКУЩЕЙ ДАТЫ в формате YYYY-MM-DD и обязательно передай её в поле `date`.
   - Если дата не указана явно, передавай в `date` текущую дату или оставь поле пустым.

3. НАПИТКИ (ЧАЙ, КОФЕ, СОКИ) И УТОЧНЕНИЕ САХАРА:
   - В счетчик чистой воды (`water_action`, `added_water_ml`) идет ТОЛЬКО чистая питьевая вода.
   - Чай, кофе, соки и другие напитки добавляй как обычные продукты в массив `detail` со своими граммовками/мл и КБЖУ.
   - Если пользователь пишет "выпил чай" или "кофе", но НЕ указывает объем ИЛИ наличие сахара/добавок (например, просто "выпил чай"), НЕ ВЫЗЫВАЙ ИНСТРУМЕНТ. Спроси текстом: "Укажите объем напитка и с сахаром/молоком или без?".
   - В поле `message` НЕ НУЖНО писать технические пояснения. Отвечай коротко и естественно: "Записал чай без сахара (250 мл)".

4. ГРАММОВКИ, ОЦЕНКА ПОРЦИЙ И ОПИСАТЕЛЬНЫЕ РАЗМЕРЫ:
   - Если пользователь вообще не указал ни размер, ни вес, ни количество (например: "съел бургер и фри"), спроси: "Укажите объем, вес или размер порции для: [список]".
   - Если пользователь указывает понятные описательные размеры ("маленький бургер", "средняя порция фри", "1 яблоко", "большой стакан сока"), НЕ ТРЕБУЙ точные граммы. Оцени стандартный вес и КБЖУ самостоятельно и сразу вызывай инструмент!

5. УТОЧНЕНИЕ ПРИ НЕОДНОЗНАЧНОСТИ:
   - Если пользователь просит удалить или изменить продукт ("удали чай", "исправь напиток"), но в последней записи таких продуктов несколько или запрос слишком общий, переспроси, что именно он имеет в виду.

6. СТРОГИЙ ПЕРЕСЧЕТ `total` ПРИ ИЗМЕНЕНИЯХ И УДАЛЕНИЯХ:
   - Твой единственный источник правды — блок "ПОСЛЕДНЯЯ ЗАПИСЬ ДНЕВНИКА В БД".
   - Если ты ИЗМЕНЯЕШЬ граммовку блюда или УДАЛЯЕШЬ блюдо из `detail`, ты ОБЯЗАН заново просуммировать КБЖУ всех оставшихся элементов в `detail` и обновить объект `total`.

7. ДОБАВЛЕНИЕ БЕЗ ЛИШНИХ ВОПРОСОВ (target_entry):
   - НИКОГДА НЕ СПРАШИВАЙ пользователя: "Добавить в текущую запись или создать новую?".
   - При добавлении еды всегда создавай новую запись (`target_entry`: "new").
   - При изменении/удалении продуктов из записи — обновляй текущую (`target_entry`: "current").

ПРАВИЛА УДАЛЕНИЯ ВОДЫ:
- При сбросе/удалении чистой воды устанавливай `water_action`: "reset" и `added_water_ml`: 0.

ЕДИНИЦЫ ИЗМЕРЕНИЯ (СТРОГО В ГРАММАХ И МИЛЛИЛИТРАХ):
- Вес и объем в `detail` всегда переводи в абсолютные числа (г/мл): 500 г -> 500, 1 кг -> 1000, 1 л -> 1000."""


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
                    "date": {
                        "type": "string",
                        "description": "Дата записи в формате YYYY-MM-DD. Если пользователь просит добавить/изменить за прошлый день (вчера, позавчера и т.д.), укажи соответствующую дату."
                    },
                    "water_action": {
                        "type": "string",
                        "enum": ["add", "reset", "set"],
                        "description": "'add' — прибавить воду, 'reset' — сбросить воду в 0, 'set' — установить конкретное значение."
                    },
                    "message": {
                        "type": "string",
                        "description": "Краткий и естественный ответ пользователю. Без мета-пояснений о правилах БД."
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
# 3. ИСПОЛНИТЕЛЬ ДЕЙСТВИЙ (ОБРАБОТКА ВОДЫ, ГРАММОВОК И ДАТ)
# ==============================================================
def execute_nutrition_action(tool_call, profile_obj) -> str:
    # Безопасное получение аргументов независимо от версии SDK (dict или object)
    if isinstance(tool_call, dict):
        raw_args = tool_call["function"]["arguments"]
    else:
        raw_args = tool_call.function.arguments

    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

    message = args.get("message", "Дневник успешно обновлен.")
    target_entry = args.get("target_entry", "new")
    water_action = args.get("water_action", "add")
    added_water_ml = float(args.get("added_water_ml", 0))
    updated_detail = args.get("detail", [])
    updated_total = args.get("total", {})
    date_str = args.get("date")

    # Обработка целевой даты
    target_datetime = None
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            now = timezone.now()
            target_datetime = timezone.make_aware(
                datetime.combine(parsed_date.date(), now.time())
            )
        except Exception:
            target_datetime = None

    # Поиск соответствующей записи в зависимости от указанной даты
    if date_str and target_datetime:
        target_date_only = target_datetime.date()
        last_entry = Calories.objects.filter(
            profile=profile_obj,
            created_at__date=target_date_only
        ).order_by('-created_at').first()
    else:
        last_entry = Calories.objects.filter(profile=profile_obj).order_by('-created_at').first()

    if target_entry == "new" or last_entry is None:
        entry = Calories(profile=profile_obj, saved=True, water_intake=0.0)
    else:
        entry = last_entry

    # Обновление воды
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

    # Если была передана специфичная дата (например, вчера) — переопределяем created_at в БД
    if target_datetime:
        entry.created_at = target_datetime
        entry.save(update_fields=['created_at'])

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
        "water_intake_liters": current_water_liters,
        "created_at": entry.created_at.strftime("%Y-%m-%d %H:%M") if entry and entry.created_at else None
    }

    now_str = timezone.now().strftime("%Y-%m-%d %H:%M")

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

    # Безопасное получение tool_calls для любой версии OpenAI SDK (Pydantic / Dict)
    tool_calls = None
    if hasattr(response_msg, "tool_calls") and response_msg.tool_calls:
        tool_calls = response_msg.tool_calls
    elif isinstance(response_msg, dict) and response_msg.get("tool_calls"):
        tool_calls = response_msg.get("tool_calls")

    if tool_calls:
        for tool_call in tool_calls:
            return execute_nutrition_action(tool_call, profile_obj)

    # Если инструмент не был вызван (например, AI задает уточняющий вопрос)
    content = getattr(response_msg, "content", None) or (response_msg.get("content") if isinstance(response_msg, dict) else "")
    return content.strip() if content else "Запрос обработан."