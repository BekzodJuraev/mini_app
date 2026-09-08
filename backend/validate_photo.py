import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from rest_framework.exceptions import ValidationError

class InsightFaceSingleton:
    _app = None

    @classmethod
    def get_app(cls):
        if cls._app is None:
            cls._app = FaceAnalysis(
                name='buffalo_l',
                providers=['CPUExecutionProvider']
            )
            # ВАЖНО: для CPU ctx_id должен быть -1
            cls._app.prepare(ctx_id=-1, det_size=(640, 640))
        return cls._app


def validate_user_avatar(image_file):
    """
    Проверяет загруженный файл изображения на пригодность для генерации.
    """
    try:
        app = InsightFaceSingleton.get_app()

        # Читаем байты и сразу возвращаем указатель в начало
        image_bytes = image_file.read()
        image_file.seek(0)

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValidationError("Не удалось прочитать файл как изображение.")

        faces = app.get(img)

        # 1. Проверка на наличие
        if len(faces) == 0:
            raise ValidationError("На фото не найдено лицо. Загрузите четкое селфи.")

        # 2. Проверка на количество
        if len(faces) > 1:
            raise ValidationError("На фото найдено несколько лиц. Загрузите фото, где вы один(одна).")

        # 3. Проверка уверенности
        face = faces[0]
        if face.det_score < 0.6:
            raise ValidationError("Лицо распознано неуверенно. Попробуйте сделать фото при хорошем освещении.")

        return image_file

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Ошибка при обработке изображения: {str(e)}")