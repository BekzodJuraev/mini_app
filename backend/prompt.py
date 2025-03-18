import openai
openai.api_key = "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"

def get_health_scale(height, weight, smoking_now, smoking_past, location, gender, date_birth, exp_smoke):
    user_input = f"""
    Рост: {height}
    Вес: {weight}
    Пол: {gender}
    Дата рождения: {date_birth}
    Курите ли вы сейчас: {smoking_now}
    Курили ли вы раньше: {smoking_past}
    Стаж курения: {exp_smoke}
    Место проживания: {location}

    Оцени состояние по шкале от 1 до 10 для следующих категорий:

    - Общий тонус (Overall tone)
    - Дыхательная система (Respiratory System)
      - Легкие (Lungs)
      - Трахея (Trachea)
      - Носоглотка (Nasopharynx)
      - Бронхи (Bronchi)
      - Рёбра (Ribs)
      - Диафрагма (Diaphragm)
    - Сердечно-сосудистая система (Cardiovascular System)
      - Пульс (Pulse)
      - Систолическое давление (Systolic Pressure)
      - Диастолическое давление (Diastolic Pressure)
    - Опорно-двигательная система (Skeletal Muscle System)
      - Скелет (Skeleton)
      - Мышцы (Muscles)
      - Защита (Protection)
      - Гибкость суставов (Joint Flexibility)
      - Амортизация (Shock Absorption)
      - Позвоночник (Spine)
    - Эндокринная система (Endocrine System)
      - Щитовидная железа (Thyroid Gland)
      - Шишковидная железа (Pineal Gland)
      - Надпочечники (Adrenal Glands)
      - Поджелудочная железа (Pancreas)
      - Вилочковая железа (Thymus)
      - Половые железы (Sex Glands)
    - Иммунная система (Immune System)
    - Пищеварительная система (Digestive System)
      - Пищевод (Esophagus)
      - Печень (Liver)
      - Желудок (Stomach)
      - Толстый кишечник (Large Intestine)
      - Тонкий кишечник (Small Intestine)
      - Ротовая полость (Oral Cavity)
    - Выделительная система (Excretory System)
    - Зубочелюстная система (Dental Jaw System)
    - Сенсорная система (Sensory System)
    - Кроветворение и обмен (Hematopoietic Metabolic System)
    - Психическое здоровье (Mental Health System)

    Ответ должен быть ТОЛЬКО в формате JSON, например:
    {{
        "Общий тонус": 1,
        "Дыхательная система": {{
            "Легкие": 1,
            "Трахея": 1,
            "Носоглотка": 1,
            "Бронхи": 1,
            "Рёбра": 1,
            "Диафрагма": 1
        }},
        "Сердечно-сосудистая система": {{
            "Пульс": 1,
            "Систолическое давление": 1,
            "Диастолическое давление": 1
        }},
        "Опорно-двигательная система": {{
            "Скелет": 1,
            "Мышцы": 1,
            "Защита": 1,
            "Гибкость суставов": 1,
            "Амортизация": 1,
            "Позвоночник": 1
        }},
        "Эндокринная система": {{
            "Щитовидная железа": 1,
            "Шишковидная железа": 1,
            "Надпочечники": 1,
            "Поджелудочная железа": 1,
            "Вилочковая железа": 1,
            "Половые железы": 1
        }},
        "Иммунная система": 1,
        "Пищеварительная система": {{
            "Пищевод": 1,
            "Печень": 1,
            "Желудок": 1,
            "Толстый кишечник": 1,
            "Тонкий кишечник": 1,
            "Ротовая полость": 1
        }},
        "Выделительная система": 1,
        "Зубочелюстная система": 1,
        "Сенсорная система": 1,
        "Кроветворение и обмен": 1,
        "Психическое здоровье": 1
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Ты медицинский анализатор. Оцени состояние организма по шкале от 1 до 10."},
            {"role": "user", "content": user_input}
        ]
    )

    return response["choices"][0]["message"]["content"]




def chat_system(message):
    SYSTEM_PROMPT = """Вы — медицинский ассистент. Вы предоставляете только информацию, связанную со здоровьем.  
    Если пользователь спрашивает о других темах, ответьте:  
    'Извините, я предоставляю только медицинскую информацию.'"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
    )

    return response["choices"][0]["message"]["content"]
