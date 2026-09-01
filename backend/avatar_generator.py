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


def make_background_white(image):
    """
    Удаляет темный/цветной фон у шаблона и заменяет его на чистый белый (255, 255, 255).
    """
    # Если изображение имеет альфа-канал (PNG с прозрачностью)
    if image.shape[2] == 4:
        alpha = image[:, :, 3]
        bgr = image[:, :, :3]
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha_factor = alpha[:, :, np.newaxis] / 255.0
        result = (bgr * alpha_factor + white_bg * (1 - alpha_factor)).astype(np.uint8)
        return result

    # Для 3-канальных BGR изображений: выделяем объект и отсекаем темный/голографический фон
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Создаем маску заднего фона (все, что слишком темное или фоновое)
    _, mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    # Очищаем шум маски
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # Создаем белый холст
    white_bg = np.full_like(image, 255, dtype=np.uint8)

    # Смешиваем передний план и белый фон
    alpha = (mask / 255.0)[:, :, np.newaxis]
    white_result = (image * alpha + white_bg * (1.0 - alpha)).astype(np.uint8)

    return white_result


def is_system_avatar(filename: str) -> bool:
    """
    Фильтр для системных шаблонов:
    Отбирает файлы, заканчивающиеся на '-old.png' или имеющие префикс 'image-'.
    """
    fn = filename.lower()
    return fn.endswith("-old.png") or fn.startswith("image-")


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

    # Формируем папки для результатов
    folder_name = str(profile.id)
    abs_output_dir = os.path.join(settings.MEDIA_ROOT, "result_avatar", folder_name)

    if not os.path.exists(templates_dir):
        return False

    user_img = cv2.imread(user_photo_path)
    if user_img is None:
        return False

    # Получаем инстансы моделей (Singleton)
    app = get_face_app()
    swapper = get_swapper()

    user_faces = app.get(user_img)
    if not user_faces:
        return False

    # Берем самое крупное лицо на фото
    user_face = max(
        user_faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
    )

    os.makedirs(abs_output_dir, exist_ok=True)

    general_avatar_urls = []
    system_avatar_urls = []

    for filename in os.listdir(templates_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            template_path = os.path.join(templates_dir, filename)

            # Читаем шаблон (с поддержкой альфа-канала, если это PNG)
            template_img = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)

            if template_img is None:
                continue

            # 1. Заменяем фон шаблона на чистый белый
            white_template = make_background_white(template_img)

            # 2. Ищем лицо на шаблоне с белым фоном
            template_faces = app.get(white_template)
            if not template_faces:
                continue

            template_face = max(
                template_faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            )

            # 3. Делаем Face Swap на шаблон с БЕЛЫМ фоном
            final_res = swapper.get(white_template, template_face, user_face, paste_back=True)

            # Сохраняем итоговое изображение
            out_file_path = os.path.join(abs_output_dir, filename)
            cv2.imwrite(out_file_path, final_res)

            # Ссылка на сгенерированный файл
            file_url = f"{settings.MEDIA_URL}result_avatar/{folder_name}/{filename}"

            # Распределение по спискам
            if is_system_avatar(filename):
                system_avatar_urls.append(file_url)
            else:
                general_avatar_urls.append(file_url)

    # Сохраняем результат в Django-модель
    profile.generated_avatars = general_avatar_urls
    profile.system_avatars = system_avatar_urls
    profile.save(update_fields=["generated_avatars", "system_avatars"])

    return {
        "generated_avatars": general_avatar_urls,
        "system_avatars": system_avatar_urls,
    }