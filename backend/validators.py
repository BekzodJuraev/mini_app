from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .validate_photo import validate_user_avatar


def validate_face_photo(image_file):
    if not image_file:
        return

    try:
        is_valid, error_msg = validate_user_avatar(image_file)

        # Сбрасываем указатель файла обратно в начало
        if hasattr(image_file, "seek"):
            image_file.seek(0)

        if not is_valid:
            # Извлекаем чистую строку, если error_msg случайно оказался ErrorDetail/списком
            clean_msg = (
                error_msg.message
                if hasattr(error_msg, "message")
                else str(error_msg)
            )
            raise DjangoValidationError(clean_msg)

    except (DRFValidationError, DjangoValidationError) as e:
        if hasattr(image_file, "seek"):
            image_file.seek(0)

        # Вытаскиваем только чистый текст сообщения без ErrorDetail и кодов
        if hasattr(e, "detail"):
            if isinstance(e.detail, list) and len(e.detail) > 0:
                msg = str(e.detail[0])
            else:
                msg = str(e.detail)
        elif hasattr(e, "message"):
            msg = e.message
        else:
            msg = str(e)

        raise DjangoValidationError(msg)

    except Exception as e:
        if hasattr(image_file, "seek"):
            image_file.seek(0)
        raise DjangoValidationError(f"Ошибка при обработке файла: {str(e)}")