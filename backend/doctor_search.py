import json
import openai
from .models import DoctorProfile

MODEL = "gpt-4o-mini"


def match_online_doctor_with_ai(profile, complaint_text: str, filename: str = None) -> DoctorProfile:
    """
    ИИ анализирует описание проблемы клиента, прикрепленный файл и данные профиля,
    после чего выбирает подходящего врача среди тех, кто сейчас Online (is_online=True).
    Если подходящего специалиста нет — возвращает None (для экрана 'Врач не найден').
    """
    online_doctors = list(DoctorProfile.objects.filter(is_active=True, is_online=True))
    if not online_doctors:
        return None

    doctors_Catalog = [
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
Проанализируй проблему пациента, данные его медицинской карты и список врачей, которые сейчас находятся в статусе Online.

Правила подбора:
1. Выбери наиболее подходящего врача по специализации и опыту из списка доступных онлайн-врачей.
2. Если жалоба общая (простуда, давление, слабость, температура, анализы и т.д.) — отлично подходит Терапевт или Врач общей практики.
3. Если среди врачей онлайн есть подходящий специалист (или терапевт для первичного приёма), верни его ID в поле "selected_doctor_id".
4. Если проблема узкоспециализированная, а среди врачей онлайн нет ни профильного специалиста, ни терапевта — верни "selected_doctor_id": null.

Верни ответ СТРОГО в формате JSON:
{
  "selected_doctor_id": 12,
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
                        f"Список врачей Online:\n{json.dumps(doctors_Catalog, ensure_ascii=False)}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )
        res_data = json.loads(response["choices"][0]["message"]["content"])
        selected_id = res_data.get("selected_doctor_id")
        if selected_id:
            for doc in online_doctors:
                if doc.id == int(selected_id):
                    return doc
        return None
    except Exception as e:
        print(f"AI doctor match error: {e}")
        # Fallback: если OpenAI недоступен, берем первого онлайн-врача с лучшим рейтингом
        return sorted(online_doctors, key=lambda x: x.rating, reverse=True)[0]