import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

class InsightFaceSingleton:
    _instance = None
    _app = None

    @classmethod
    def get_app(cls):
        if cls._app is None:
            # Загружаем модель только при первом реальном запросе
            cls._app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            cls._app.prepare(ctx_id=0, det_size=(640, 640))
        return cls._app


def validate_user_avatar(image_file):
    """
    Проверяет загруженный файл изображения на пригодность для генерации.
    """
    try:
        # Получаем единственный экземпляр модели
        app = InsightFaceSingleton.get_app()

        # Читаем байты из Django InMemoryUploadedFile / TemporaryUploadedFile
        image_bytes = image_file.read()
        image_file.seek(0)  # Сбрасываем указатель файла назад

        # Преобразуем в формат OpenCV (BGR)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return False, "Не удалось прочитать файл как изображение."

        # Детектируем лица
        faces = app.get(img)

        # 1. Проверка на наличие
        if len(faces) == 0:
            return False, "На фото не найдено лицо. Загрузите четкое селфи."

        # 2. Проверка на количество
        if len(faces) > 1:
            return False, "На фото найдено несколько лиц. Загрузите фото, где вы один(одна)."

        # 3. Проверка уверенности детектирования
        face = faces[0]
        if face.det_score < 0.6:
            return False, "Лицо распознано неуверенно. Попробуйте сделать фото при хорошем освещении."

        return True, None

    except Exception as e:
        return False, f"Ошибка при обработке изображения: {str(e)}"