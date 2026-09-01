import os
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from django.conf import settings

# Глобальные переменные для хранения инстансов моделей (Singleton)
_APP = None
_SWAPPER = None


def get_face_app():
    """Загружает FaceAnalysis только при первом вызове функции генерации."""
    global _APP
    if _APP is None:
        _APP = FaceAnalysis(
            name="buffalo_l", providers=["CPUExecutionProvider"]
        )
        _APP.prepare(ctx_id=-1, det_size=(640, 640))
    return _APP


def get_swapper():
    """Загружает inswapper_128.onnx только при первом вызове функции генерации."""
    global _SWAPPER
    if _SWAPPER is None:
        swapper_path = os.path.join(settings.BASE_DIR, "inswapper_128.onnx")
        if not os.path.exists(swapper_path):
            raise FileNotFoundError(f"Файл модели не найден по пути: {swapper_path}")
        _SWAPPER = insightface.model_zoo.get_model(swapper_path, download=False)
    return _SWAPPER


def apply_blue_hologram_tone(swapped_img, original_template, face_bbox):
    """Корректирует тон пересаженного лица под синее свечение шаблона с безопасным ROI."""
    h, w, _ = swapped_img.shape
    x1, y1, x2, y2 = map(int, face_bbox)

    # Зажимаем границы, чтобы не выйти за пределы изображения
    x1, y1 = max(0, x1 - 10), max(0, y1 - 10)
    x2, y2 = min(w, x2 + 10), min(h, y2 + 10)

    # Вырезаем ROI
    face_roi = swapped_img[y1:y2, x1:x2]
    template_roi = original_template[y1:y2, x1:x2]

    # Если ROI получился пустым или размеры не совпадают
    if face_roi.size == 0 or face_roi.shape != template_roi.shape:
        return swapped_img

    hsv_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    hsv_template = cv2.cvtColor(template_roi, cv2.COLOR_BGR2HSV)

    # Коррекция тона и насыщенности
    hsv_face[:, :, 0] = hsv_template[:, :, 0]
    hsv_face[:, :, 1] = cv2.addWeighted(
        hsv_face[:, :, 1], 0.3, hsv_template[:, :, 1], 0.7, 0
    )

    corrected_roi = cv2.cvtColor(hsv_face, cv2.COLOR_HSV2BGR)
    mask = np.full(corrected_roi.shape, 255, dtype=np.uint8)

    # Центр бесшовного наложения
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)

    # Проверка безопасного центра для seamlessClone
    if center_x <= 0 or center_y <= 0 or center_x >= w or center_y >= h:
        return swapped_img

    try:
        return cv2.seamlessClone(
            corrected_roi, swapped_img, mask, (center_x, center_y), cv2.NORMAL_CLONE
        )
    except cv2.error:
        # Если бесшовное клонирование упало по геометрии — возвращаем соединенный ROI напрямую
        swapped_img[y1:y2, x1:x2] = corrected_roi
        return swapped_img


def generate_avatars_for_profile(profile, request=None):
    if not profile.photo or not profile.gender:
        return False

    gender_folder = str(profile.gender).lower()
    if gender_folder not in ["male", "female"]:
        return False

    user_photo_path = profile.photo.path
    if not os.path.exists(user_photo_path):
        return False

    templates_dir = os.path.join(settings.BASE_DIR, "templates_avatar", gender_folder)

    # Формируем папки
    folder_name = str(profile.id)
    abs_output_dir = os.path.join(settings.MEDIA_ROOT, "result_avatar", folder_name)

    if not os.path.exists(templates_dir):
        return False

    user_img = cv2.imread(user_photo_path)
    if user_img is None:
        return False

    # Получаем инстансы моделей (загрузятся в ОЗУ только на этой строчке)
    app = get_face_app()
    swapper = get_swapper()

    user_faces = app.get(user_img)
    if not user_faces:
        return False

    user_face = max(
        user_faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
    )

    os.makedirs(abs_output_dir, exist_ok=True)
    avatar_urls = []

    for filename in os.listdir(templates_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            template_path = os.path.join(templates_dir, filename)
            template_img = cv2.imread(template_path)

            if template_img is None:
                continue

            template_faces = app.get(template_img)
            if not template_faces:
                continue

            template_face = max(
                template_faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            )

            res = swapper.get(template_img, template_face, user_face, paste_back=True)
            final_res = apply_blue_hologram_tone(res, template_img, template_face.bbox)

            out_file_path = os.path.join(abs_output_dir, filename)
            cv2.imwrite(out_file_path, final_res)

            # Формируем правильный относительный URL через прямые слэши
            file_url = f"{settings.MEDIA_URL}result_avatar/{folder_name}/{filename}"

            avatar_urls.append(file_url)

    profile.generated_avatars = avatar_urls
    profile.save(update_fields=["generated_avatars"])

    return avatar_urls