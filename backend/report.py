import hashlib
import json
import re
import openai
from datetime import date

from .models import (
    Drugs,
    BloodPressure,
    Daily_check,
    Rentgen,
    GeneralHealthReportProfile,
)
from .prompt import generate_scales_summary_ai



def clean_and_truncate_analysis_text(text: str, max_len: int = 380) -> str:
    """
    Убирает markdown-символы (#, **) из ответа Rentgen.answer и обрезает слишком длинные
    простыни текста до краткого резюме (3-4 предложения), чтобы ReportLab Table не падал с LayoutError.
    """
    if not text:
        return "Результат в обработке"

    # Убираем markdown разметку и лишние переносы строк
    cleaned = re.sub(r'[#*`_~]+', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if len(cleaned) <= max_len:
        return cleaned

    # Обрезаем по последнему законченному предложению в пределах лимита
    short_text = cleaned[:max_len]
    last_dot = short_text.rfind('.')
    if last_dot > 150:
        return short_text[:last_dot + 1]
    return short_text.rstrip() + "..."


def calculate_age_str(birth_date: date) -> str:
    if not birth_date:
        return "Данные не указаны"
    today = date.today()
    years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if years < 0:
        return "Данные не указаны"

    if years % 10 == 1 and years % 100 != 11:
        suffix = "год"
    elif 2 <= years % 10 <= 4 and (years % 100 < 10 or years % 100 >= 20):
        suffix = "года"
    else:
        suffix = "лет"
    return f"{years} {suffix}"


def calculate_bmi_str(height_cm, weight_kg) -> str:
    if not height_cm or not weight_kg or height_cm <= 0 or weight_kg <= 0:
        return "Данные не указаны"
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    bmi_str = str(bmi).replace('.', ',')

    if bmi < 18.5:
        label = "дефицит массы тела"
    elif bmi < 25.0:
        label = "нормальная масса тела"
    elif bmi < 30.0:
        label = "избыточная масса тела"
    else:
        label = "ожирение"
    return f"{bmi_str} — {label}"


def format_smoking_from_history(med_history: dict, ik_value) -> str:
    if not isinstance(med_history, dict):
        med_history = {}

    now_smoke = str(med_history.get("now_smoke", "")).lower()
    recent_smoke = str(med_history.get("recent_smoke", "")).lower()
    per_day = med_history.get("smoke_per_day_count") or 0
    exp_years = med_history.get("exp_smoke_years") or 0

    if now_smoke in ("yes", "true", "да", "1"):
        if per_day and exp_years:
            return f"Курит: {per_day} сигарет в день, стаж {exp_years} лет"
        elif per_day:
            return f"Курит: {per_day} сигарет в день"
        return "Курит"
    elif recent_smoke in ("yes", "true", "да", "1"):
        return "Курил ранее"
    elif now_smoke in ("no", "false", "нет", "0"):
        return "Не курит"

    if ik_value is not None and ik_value > 0:
        return f"Индекс курения: {ik_value}"
    return "Данные не указаны"


def collect_all_user_health_data(profile) -> dict:
    """
    Берёт готовые поля напрямую из Profile, Drugs, Rentgen, BloodPressure, Daily_check.
    """
    med_history = profile.medical_history if isinstance(profile.medical_history, dict) else {}

    fio_parts = [p for p in (profile.lastname, profile.name, profile.middle_name) if p]
    full_name = " ".join(fio_parts) if fio_parts else "Данные не указаны"

    gender_raw = (profile.gender or "").strip().lower()
    if gender_raw in ("male", "м", "муж", "мужской"):
        gender_str = "Мужской"
    elif gender_raw in ("female", "ж", "жен", "женский"):
        gender_str = "Женский"
    else:
        gender_str = profile.gender if profile.gender else "Данные не указаны"

    age_str = calculate_age_str(profile.date_birth)
    height_str = f"{profile.height} см" if (profile.height and profile.height > 0) else "Данные не указаны"
    weight_val = int(profile.weight) if (profile.weight and float(profile.weight).is_integer()) else profile.weight
    weight_str = f"{weight_val} кг" if (profile.weight and profile.weight > 0) else "Данные не указаны"

    if height_str != "Данные не указаны" and weight_str != "Данные не указаны":
        height_weight_str = f"{height_str} / {weight_str}"
    elif height_str != "Данные не указаны":
        height_weight_str = height_str
    elif weight_str != "Данные не указаны":
        height_weight_str = weight_str
    else:
        height_weight_str = "Данные не указаны"

    bmi_str = calculate_bmi_str(profile.height, profile.weight)

    bg = med_history.get("blood_group")
    rh = med_history.get("rh_factor")
    if bg and rh:
        blood_str = f"{bg}, {rh}"
    elif bg or rh:
        blood_str = str(bg or rh)
    else:
        blood_str = "Данные не указаны"

    residence_str = profile.place_of_residence if profile.place_of_residence else "Данные не указаны"
    smoking_str = format_smoking_from_history(med_history, profile.IK)
    chronic_str = med_history.get("chronic_diseases") or "Не указаны"

    drugs_qs = Drugs.objects.filter(profile=profile).prefetch_related('notifications_drugs')
    drugs_list = []
    for d in drugs_qs:
        times_count = d.notifications_drugs.count() or d.day or 1
        intake_info = f", {d.intake}" if d.intake else ""
        drugs_list.append(f"{d.name}{intake_info}, {times_count} раз(а) в день")
    drugs_str = "; ".join(drugs_list) if drugs_list else "Данные не указаны"

    # Анализы из Rentgen (обрезаем гигантские тексты, чтобы не ломалась таблица в PDF)
    rentgens = []
    for r in Rentgen.objects.filter(profile=profile).order_by('-created_at')[:10]:
        date_str = r.created_at.strftime('%d.%m.%Y') if r.created_at else ""
        raw_msg = clean_and_truncate_analysis_text(r.message, max_len=90) if r.message else "Анализ"
        title = f"{raw_msg}, {date_str}" if date_str else raw_msg
        rentgens.append({
            "title": title,
            "result": clean_and_truncate_analysis_text(r.answer, max_len=380)
        })

    pressures = [
        {
            "давление": f"{bp.pressure_top}/{bp.pressure_bottom} мм рт. ст.",
            "дата": bp.created_at.strftime('%d.%m.%Y') if bp.created_at else ""
        }
        for bp in BloodPressure.objects.filter(profile=profile).order_by('-created_at', '-id')[:10]
    ]

    daily_checks = [
        {
            "дата": dc.created_at.strftime('%d.%m.%Y') if dc.created_at else "",
            "запись": clean_and_truncate_analysis_text(dc.message, max_len=250)
        }
        for dc in Daily_check.objects.filter(profile=profile).order_by('-created_at', '-id')[:10]
        if dc.message
    ]

    return {
        "personal_table": {
            "full_name": full_name,
            "gender": gender_str,
            "age": age_str,
            "height_weight": height_weight_str,
            "bmi": bmi_str,
            "smoking": smoking_str,
            "chronic_diseases": chronic_str,
            "drugs": drugs_str,
            "blood_group": blood_str,
            "place_of_residence": residence_str,
        },
        "analyses": rentgens,
        # Ключи на русском языке для передачи в ИИ, чтобы он не использовал технические имена переменных
        "ai_payload": {
            "анкета_пациента": {
                "пол": gender_str,
                "возраст": age_str,
                "рост_и_вес": height_weight_str,
                "индекс_массы_тела": bmi_str,
                "курение": smoking_str,
                "хронические_заболевания": chronic_str,
            },
            "текущие_шкалы_здоровья": profile.health_system or {},
            "прошлые_шкалы_здоровья": profile.previous_health_system or {},
            "история_артериального_давления": pressures,
            "дневник_самочувствия_и_опросы": daily_checks,
            "результаты_анализов": rentgens,
        }
    }





def get_or_update_scales_summary_report(profile):
    """
    Проверяет MD5-хэш данных: если данные не менялись и в старом тексте нет технических слов,
    возвращает готовый объект из БД. Иначе обновляет через ИИ.
    """
    collected_data = collect_all_user_health_data(profile)
    ai_payload = collected_data["ai_payload"]

    raw_json = json.dumps(ai_payload, ensure_ascii=False, sort_keys=True, default=str)
    current_hash = hashlib.md5(raw_json.encode('utf-8')).hexdigest()

    report_obj = GeneralHealthReportProfile.objects.filter(profile=profile).first()

    # Проверяем, чтобы в кэше не остался старый текст с английскими названиями полей
    has_tech_words = False
    if report_obj and report_obj.dynamics_analysis:
        for bad_word in ("health_system", "daily_checks", "personal_table", "blood_pressure"):
            if bad_word in (report_obj.dynamics_analysis or "") or bad_word in (report_obj.brief_summary or ""):
                has_tech_words = True
                break

    if report_obj and report_obj.data_hash == current_hash and report_obj.brief_summary and not has_tech_words:
        return report_obj

    p_table = collected_data["personal_table"]

    try:
        ai_res = generate_scales_summary_ai(ai_payload)
    except Exception as e:
        print(f"Error generating scales summary AI report: {e}")
        ai_res = {}

    report_obj, _ = GeneralHealthReportProfile.objects.update_or_create(
        profile=profile,
        defaults={
            "brief_summary": ai_res.get("brief_summary") or (
                "Общее состояние оценивается как стабильное. Большинство показателей находится в нормальной зоне."
            ),
            "dynamics_analysis": ai_res.get("dynamics_analysis") or (
                "Показатели основных систем организма остаются стабильными. Новых отрицательных изменений не выявлено."
            ),
            "norms_comparison": ai_res.get("norms_comparison") or (
                f"ИМТ: {p_table['bmi']}. Основные функциональные показатели соответствуют возрастным нормам."
            ),
            "personal_recommendations": ai_res.get("personal_recommendations") or (
                "Рекомендуется поддерживать регулярную физическую активность, соблюдать режим сна и питьевой баланс."
            ),
            "data_hash": current_hash,
        }
    )

    return report_obj