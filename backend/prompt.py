import openai
from config import KEY,MODEL
openai.api_key = KEY
import json
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

    Оцени состояние по шкале от 1 до 10 для следующих категорий, добавляя общий показатель для каждой группы:

    - Общий тонус (Overall tone)
    - Дыхательная система (Respiratory System)
      - Общий показатель
      - Легкие (Lungs)
      - Трахея (Trachea)
      - Носоглотка (Nasopharynx)
      - Бронхи (Bronchi)
      - Рёбра (Ribs)
      - Диафрагма (Diaphragm)
    - Сердечно-сосудистая система (Cardiovascular System)
      - Общий показатель
      - Пульс (Pulse)
      - Систолическое давление (Systolic Pressure)
      - Диастолическое давление (Diastolic Pressure)
    - Опорно-двигательная система (Skeletal Muscle System)
      - Общий показатель
      - Скелет (Skeleton)
      - Мышцы (Muscles)
      - Защита (Protection)
      - Гибкость суставов (Joint Flexibility)
      - Амортизация (Shock Absorption)
      - Позвоночник (Spine)
    - Эндокринная система (Endocrine System)
      - Общий показатель
      - Щитовидная железа (Thyroid Gland)
      - Шишковидная железа (Pineal Gland)
      - Надпочечники (Adrenal Glands)
      - Поджелудочная железа (Pancreas)
      - Вилочковая железа (Thymus)
      - Половые железы (Sex Glands)
    - Иммунная система (Immune System) - Общий показатель
    - Пищеварительная система (Digestive System)
      - Общий показатель
      - Пищевод (Esophagus)
      - Печень (Liver)
      - Желудок (Stomach)
      - Толстый кишечник (Large Intestine)
      - Тонкий кишечник (Small Intestine)
      - Ротовая полость (Oral Cavity)
    - Выделительная система (Excretory System) - Общий показатель
    - Зубочелюстная система (Dental Jaw System) - Общий показатель
    - Сенсорная система (Sensory System) - Общий показатель
    - Кроветворение и обмен (Hematopoietic Metabolic System) - Общий показатель
    - Психическое здоровье (Mental Health System) - Общий показатель

    Ответ должен быть ТОЛЬКО в формате JSON, например:
    {{
        "Общий тонус": 7,
        "Дыхательная система": {{
            "Общий показатель": 6,
            "Легкие": 5,
            "Трахея": 6,
            "Носоглотка": 7,
            "Бронхи": 6,
            "Рёбра": 7,
            "Диафрагма": 6
        }},
        "Сердечно-сосудистая система": {{
            "Общий показатель": 7,
            "Пульс": 7,
            "Систолическое давление": 6,
            "Диастолическое давление": 7
        }},
        "Опорно-двигательная система": {{
            "Общий показатель": 8,
            "Скелет": 8,
            "Мышцы": 7,
            "Защита": 7,
            "Гибкость суставов": 8,
            "Амортизация": 7,
            "Позвоночник": 8
        }},
        "Эндокринная система": {{
            "Общий показатель": 7,
            "Щитовидная железа": 6,
            "Шишковидная железа": 7,
            "Надпочечники": 7,
            "Поджелудочная железа": 6,
            "Вилочковая железа": 7,
            "Половые железы": 7
        }},
        "Иммунная система": 7,
        "Пищеварительная система": {{
            "Общий показатель": 7,
            "Пищевод": 7,
            "Печень": 7,
            "Желудок": 6,
            "Толстый кишечник": 7,
            "Тонкий кишечник": 7,
            "Ротовая полость": 6
        }},
        "Выделительная система": 7,
        "Зубочелюстная система": 7,
        "Сенсорная система": 7,
        "Кроветворение и обмен": 7,
        "Психическое здоровье": 7
    }}
    """

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты медицинский анализатор. Оцени состояние организма по шкале от 1 до 10."},
            {"role": "user", "content": user_input}
        ],
        response_format={"type": "json_object"}
    )

    return response["choices"][0]["message"]["content"]






def chat_system(message):
    SYSTEM_PROMPT = """Вы — медицинский ассистент. Вы предоставляете только информацию, связанную со здоровьем.  
    Если пользователь спрашивает о других темах, ответьте:  
    'Извините, я предоставляю только медицинскую информацию.'"""

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],


    )

    return response["choices"][0]["message"]["content"]


def crash_test(user_data):
    prompt = f"""
    Попробуйте проверить, насколько прочен ваш организм. В режиме краш-тест вы можете вводить любые параметры вредных привычек и получить расчет, на сколько это сократит вашу жизнь.

    Данные пользователя:
    - Сигареты в день: {user_data['smoke_day']}
    - Стаж курения (лет): {user_data['exp_smoke']}
    - Бросал курить: {user_data['drop_smoke']}
    - Алкоголь в неделю: {user_data['alcohol_week']}
    - Алкоголь за день (максимум): {user_data['alcohol_litr']}
    - Психотропные вещества (дни в месяц): {user_data['drug_day']}
    - Сон (часов в сутки): {user_data['day_sleep']}
    - Переработки: {user_data['work']}
    - Уровень стресса: {user_data['level_stress']}
    - Склонность к самоповреждению: {user_data['habit']}
    - Беспорядочные связи: {user_data['sex']}
    - Экологическая среда: {user_data['environment']}
    - Рациональное питание: {user_data['food']}

    Определи ожидаемую продолжительность жизни и сформулируй краткий анализ состояния здоровья.
    
    Ответ должен быть ТОЛЬКО в формате JSON, например:
      {{"life_expectancy": 10,
       "message": str (краткий анализ состояния здоровья, который варьируется в зависимости от введенных данных)}}

    """

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты эксперт в анализе здоровья и вредных привычек."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" }
    )

    result_text = response["choices"][0]["message"]["content"]
    result_dict = json.loads(result_text)


    return result_dict


def lifestyle_test(user_data):
    prompt = f"""
    Оцените образ жизни на основе следующих данных:
    - Считаете ли вы свой сон качественным? (1-7): {user_data['sleep']}
    - Считаете ли вы, что ваш рацион состоит из полезной еды? (1-7): {user_data['food']}
    - Каждый свой день вы начинаете с зарядки? (1-7): {user_data['training']}
    - У вас есть вторая половинка или супруг(а)? (да/нет): {user_data['couple']}

    Определите уровень физической подготовки и сформулируйте краткий анализ состояния здоровья.

    Ответ должен быть ТОЛЬКО в формате JSON, например:
      {{ "message": "Ваш уровень физической подготовки является средним. Возможно, стоит уделить больше внимания физической активности."}}
    """

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты эксперт в области здоровья и образа жизни."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    result_text = response["choices"][0]["message"]["content"]
    result_dict = json.loads(result_text)

    return result_dict


def symptoms_test(user_data):
    prompt = f"""
    Оцените симптомы на основе следующих данных:
    - Выбор симптомов: {', '.join(user_data['symptoms'])}
    - Насколько нормальной была температура тела в последние дни? (1-7): {user_data['temp']}
    - Болели ли вы COVID-19 в последние пару лет? (да/нет): {user_data['covid']}
    - Оцените затрудненность дыхания (1-7): {user_data['breath']}
    - Было ли у вас  кашель ?(1-7): {user_data['cough']}
    - Было ли у вас  заложенность носа?(1-7): {user_data['congestion']}
    - Боль в мышцах (1-7): {user_data['muscle']}
    - Боль в груди (1-7): {user_data['chest']}
    - Головная боль и слабость (1-7): {user_data['headache']}
    - Тошнота, рвота или диарея (1-7): {user_data['vomit']}

    Определите общее состояние здоровья и сформулируйте краткий анализ.

    Ответ должен быть ТОЛЬКО в формате JSON, например:
      {{ "message": "Согласно отправленным вами данных мы можем предположить, что вам не стоит волноваться по этому поводу." }}
    """

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты медицинский помощник, который анализирует симптомы."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    result_text = response["choices"][0]["message"]["content"]
    result_dict = json.loads(result_text)

    return result_dict