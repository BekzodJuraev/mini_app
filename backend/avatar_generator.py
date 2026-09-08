import os
import shutil
import time
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from django.conf import settings

_APP = None
_SWAPPER = None


def get_face_app():
    global _APP
    if _APP is None:
        _APP = FaceAnalysis(
            name="buffalo_l", providers=["CPUExecutionProvider"]
        )
        _APP.prepare(ctx_id=-1, det_size=(640, 640))
    return _APP


def get_swapper():
    global _SWAPPER
    if _SWAPPER is None:
        swapper_path = os.path.join(settings.BASE_DIR, "inswapper_128.onnx")
        if not os.path.exists(swapper_path):
            raise FileNotFoundError(f"Файл модели не найден по пути: {swapper_path}")
        _SWAPPER = insightface.model_zoo.get_model(swapper_path, download=False)
    return _SWAPPER


def is_system_avatar(filename: str) -> bool:
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
    folder_name = str(profile.id)
    abs_output_dir = os.path.join(settings.MEDIA_ROOT, "result_avatar", folder_name)

    if not os.path.exists(templates_dir):
        return False

    user_img = cv2.imread(user_photo_path)
    if user_img is None:
        return False

    app = get_face_app()
    swapper = get_swapper()

    user_faces = app.get(user_img)
    if not user_faces:
        return False

    user_face = max(
        user_faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
    )

    # 1. ОЧИСТКА: если папка пользователя с результатами уже существует — удаляем её полностью
    if os.path.exists(abs_output_dir):
        shutil.rmtree(abs_output_dir)

    os.makedirs(abs_output_dir, exist_ok=True)

    general_avatar_urls = []
    system_avatar_urls = []

    # Генерируем уникальный таймштамп для этой итерации
    timestamp = int(time.time())

    for filename in os.listdir(templates_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            template_path = os.path.join(templates_dir, filename)

            template_img = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
            if template_img is None:
                continue

            has_alpha = len(template_img.shape) == 3 and template_img.shape[2] == 4

            if has_alpha:
                alpha_channel = template_img[:, :, 3]
                bgr_template = template_img[:, :, :3]
            else:
                alpha_channel = None
                bgr_template = template_img

            template_faces = app.get(bgr_template)
            if not template_faces:
                continue

            template_face = max(
                template_faces,
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
            )

            swapped_bgr = swapper.get(bgr_template, template_face, user_face, paste_back=True)

            if has_alpha and alpha_channel is not None:
                final_res = cv2.merge([
                    swapped_bgr[:, :, 0],
                    swapped_bgr[:, :, 1],
                    swapped_bgr[:, :, 2],
                    alpha_channel
                ])
            else:
                final_res = swapped_bgr

            # 2. УНИКАЛЬНОЕ ИМЯ: добавляем timestamp к имени сохраняемого файла
            name_without_ext, ext = os.path.splitext(filename)
            out_filename = f"{name_without_ext}_{timestamp}{ext}"
            out_file_path = os.path.join(abs_output_dir, out_filename)

            cv2.imwrite(out_file_path, final_res)

            file_url = f"{settings.MEDIA_URL}result_avatar/{folder_name}/{out_filename}"

            # Проверку на системную аватарку делаем по ИСХОДНОМУ имени шаблона
            if is_system_avatar(filename):
                system_avatar_urls.append(file_url)
            else:
                general_avatar_urls.append(file_url)

    profile.generated_avatars = general_avatar_urls
    profile.system_avatars = system_avatar_urls
    profile.save(update_fields=["generated_avatars", "system_avatars"])

    return {
        "generated_avatars": general_avatar_urls,
        "system_avatars": system_avatar_urls,
    }