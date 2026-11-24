import json
import openai
from .models import DoctorProfile,Consultation
from django.db.models import Max, F
MODEL = "gpt-4o-mini"


def match_online_doctor_with_ai(
    profile,
    complaint_text: str,
    filename: str = None,
    exclude_doctor_ids: list = None
) -> DoctorProfile:
    """
    Подбирает подходящего СВОБОДНОГО врача со статусом Online.
    Между подходящими свободными врачами распределяет заявки по очереди (Round-Robin):
    первым идёт врач, которому дольше всего не назначали заявки.
    """
    # 1. Исключаем врачей, у которых сейчас идёт активная консультация
    busy_doctor_ids = list(
        Consultation.objects.filter(status='active').values_list('doctor_id', flat=True)
    )
    excluded = set(busy_doctor_ids)
    if exclude_doctor_ids:
        excluded.update(exclude_doctor_ids)

    # 2. Берём свободных врачей Online и сразу сортируем по очереди (давно не получал заявку -> первый)
    online_doctors = list(
        DoctorProfile.objects.filter(is_active=True, is_online=True)
        .exclude(id__in=excluded)
        .annotate(last_assigned_at=Max('doctor_consultations__created_at'))
        .order_by(F('last_assigned_at').asc(nulls_first=True), 'id')
    )
    if not online_doctors:
        return None

    doctors_catalog = [
        {
            "doctor_id": doc.id,
            "full_name": doc.full_name,
            "specialization": doc.specialization,
            "short_description": doc.short_description,
            "qualification": doc.qualification,
            "experience_years": doc.experience_years,
            "rating": doc.rating,
        }
        for doc in online_doctors
    ]

    patient_context = {
        "gender": profile.gender,
        "height": profile.height,
        "weight": profile.weight,
        "medical_history": profile.medical_history if isinstance(profile.medical_history, dict) else {},
        "complaint": complaint_text,
        "attached_file_name": filename or "Нет файла",
    }

    system_prompt = """Ты — медицинский диспетчер системы телемедицины MEDAVATAR.
Проанализируй проблему пациента, данные его медицинской карты и список свободных врачей Online.

Правила подбора:
1. Найди ВСЕХ врачей из списка, чья специализация подходит под жалобу пациента.
2. Если жалоба общая (простуда, давление, слабость, температура, анализы и т.д.) — подходят Терапевты и Врачи общей практики.
3. Если есть несколько подходящих врачей одной специальности (например, два Кардиолога) — ОБЯЗАТЕЛЬНО верни ID ВСЕХ подходящих врачей в массиве "suitable_doctor_ids".
4. Если проблема узкоспециализированная, а среди врачей онлайн нет ни профильного специалиста, ни терапевта — верни пустой массив "suitable_doctor_ids": [].

Верни ответ СТРОГО в формате JSON:
{
  "suitable_doctor_ids": [12, 15],
  "reason": "Краткое обоснование выбора"
}
"""

    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Данные пациента и жалоба:\n{json.dumps(patient_context, ensure_ascii=False, default=str)}\n\n"
                        f"Список свободных врачей Online:\n{json.dumps(doctors_catalog, ensure_ascii=False)}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )
        res_data = json.loads(response["choices"][0]["message"]["content"])
        suitable_ids = {int(i) for i in (res_data.get("suitable_doctor_ids") or [])}

        # Так как online_doctors уже отсортирован по очереди (last_assigned_at ASC NULLS FIRST),
        # первый совпавший врач — это именно тот, чья сейчас очередь.
        for doc in online_doctors:
            if doc.id in suitable_ids:
                return doc

        return None
    except Exception as e:
        print(f"AI doctor match error: {e}")
        # Fallback: берём первого по очереди среди свободных онлайн-врачей
        return online_doctors[0]