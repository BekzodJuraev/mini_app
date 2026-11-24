import json
import openai
from .models import DoctorProfile,Consultation
from django.db.models import Max, F
MODEL = "gpt-4o-mini"
import io
import re
import zipfile
import xml.etree.ElementTree as ET
def extract_file_text(file_obj, max_chars: int = 4000) -> str:
    """
    Универсально извлекает текст из PDF, DOCX, DOC и TXT (UploadedFile / FieldFile),
    не ломая указатель файла (seek(0)).
    """
    if not file_obj:
        return ""

    filename = (getattr(file_obj, 'name', '') or '').lower()

    try:
        if hasattr(file_obj, 'closed') and file_obj.closed:
            file_obj.open('rb')

        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

        raw_bytes = file_obj.read()

        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)

        if not raw_bytes:
            return ""

        text = ""

        # 1. PDF
        if filename.endswith('.pdf'):
            text_parts = []
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(raw_bytes))
                for page in reader.pages[:5]:
                    t = (page.extract_text() or "").strip()
                    if t:
                        text_parts.append(t)
            except ImportError:
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
                    for page in reader.pages[:5]:
                        t = (page.extract_text() or "").strip()
                        if t:
                            text_parts.append(t)
                except ImportError:
                    import fitz  # PyMuPDF
                    with fitz.open(stream=raw_bytes, filetype="pdf") as doc:
                        for page in doc[:5]:
                            t = (page.get_text() or "").strip()
                            if t:
                                text_parts.append(t)
            text = "\n".join(text_parts)

        # 2. DOCX (сначала python-docx, если не установлен — стандартный zipfile + XML)
        elif filename.endswith('.docx'):
            try:
                import docx
                document = docx.Document(io.BytesIO(raw_bytes))
                parts = [p.text.strip() for p in document.paragraphs if p.text.strip()]
                for table in document.tables:
                    for row in table.rows:
                        row_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                        if row_text:
                            parts.append(row_text)
                text = "\n".join(parts)
            except ImportError:
                with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                    xml_content = zf.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                parts = [elem.text for elem in tree.iter() if elem.tag.endswith('}t') and elem.text]
                text = " ".join(parts)

        # 3. Старый бинарный DOC (Word 97-2003)
        elif filename.endswith('.doc'):
            # Иногда .doc на самом деле является .docx или RTF/TXT — пробуем безопасно
            if zipfile.is_zipfile(io.BytesIO(raw_bytes)):
                with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                    if 'word/document.xml' in zf.namelist():
                        tree = ET.fromstring(zf.read('word/document.xml'))
                        parts = [e.text for e in tree.iter() if e.tag.endswith('}t') and e.text]
                        text = " ".join(parts)

            if not text:
                # Извлекаем читаемые кириллические/латинские фрагменты из UTF-16LE (стандартный формат .doc)
                decoded_u16 = raw_bytes.decode('utf-16le', errors='ignore')
                chunks = re.findall(r'[А-Яа-яЁёA-Za-z0-9.,:;()/\-\s]{6,}', decoded_u16)
                text = "\n".join(c.strip() for c in chunks if len(c.strip()) >= 6)

                if len(text) < 20:
                    # Fallback на cp1251
                    decoded_1251 = raw_bytes.decode('cp1251', errors='ignore')
                    chunks = re.findall(r'[А-Яа-яЁёA-Za-z0-9.,:;()/\-\s]{6,}', decoded_1251)
                    text = "\n".join(c.strip() for c in chunks if len(c.strip()) >= 6)

        # 4. TXT
        elif filename.endswith('.txt'):
            try:
                text = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text = raw_bytes.decode('cp1251', errors='ignore')

        return text.strip()[:max_chars]

    except Exception as e:
        print(f"File text extraction error ({filename}): {e}")
        try:
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
        except Exception:
            pass
        return ""

def match_online_doctor_with_ai(
    profile,
    complaint_text: str,
    filename: str = None,
    file_obj=None,
    exclude_doctor_ids: list = None
) -> DoctorProfile:
    """
    Подбирает подходящего СВОБОДНОГО врача Online с учётом жалобы И содержимого PDF.
    Между подходящими свободными врачами распределяет заявки по очереди (Round-Robin).
    """
    busy_doctor_ids = list(
        Consultation.objects.filter(status='active').values_list('doctor_id', flat=True)
    )
    excluded = set(busy_doctor_ids)
    if exclude_doctor_ids:
        excluded.update(exclude_doctor_ids)

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

    pdf_content = extract_file_text(file_obj)

    patient_context = {
        "gender": profile.gender,
        "height": profile.height,
        "weight": profile.weight,
        "medical_history": profile.medical_history if isinstance(profile.medical_history, dict) else {},
        "complaint": complaint_text,
        "attached_file_name": filename or (getattr(file_obj, 'name', None) or "Нет файла"),
        "attached_file_content": pdf_content or "Текст из файла не извлечён или файл не прикреплён",
    }

    system_prompt = """Ты — медицинский диспетчер системы телемедицины MEDAVATAR.
Проанализируй проблему пациента, данные его медицинской карты, СОДЕРЖИМОЕ прикреплённого файла (если оно есть) и список свободных врачей Online.

Правила подбора:
1. ОБЯЗАТЕЛЬНО анализируй и текст жалобы (`complaint`), и содержимое прикреплённого файла (`attached_file_content`) вместе.
   - Даже если жалоба общая (например, «Помогите разобраться с результатом обследования»), определяй нужную специальность по содержимому файла: ЭКГ / Холтер / ЭхоКГ / сердце → Кардиолог; ЭЭГ / МРТ мозга / неврология → Невролог; гормоны / ТТГ / щитовидка → Эндокринолог и т.д.
2. Если жалоба и файл общие (ОАК, простуда, давление, слабость, температура) — подходят Терапевты и Врачи общей практики.
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
                        f"Данные пациента, жалоба и содержимое файла:\n{json.dumps(patient_context, ensure_ascii=False, default=str)}\n\n"
                        f"Список свободных врачей Online:\n{json.dumps(doctors_catalog, ensure_ascii=False)}"
                    )
                }
            ],
            response_format={"type": "json_object"}
        )
        res_data = json.loads(response["choices"][0]["message"]["content"])
        suitable_ids = {int(i) for i in (res_data.get("suitable_doctor_ids") or [])}

        for doc in online_doctors:
            if doc.id in suitable_ids:
                return doc

        return None
    except Exception as e:
        print(f"AI doctor match error: {e}")
        return online_doctors[0]