from django.core.exceptions import ValidationError
from .validate_photo import validate_user_avatar  # твоя функция с InsightFace

def validate_face_photo(image_file):

    if hasattr(image_file, 'file'):
        is_valid, error_msg = validate_user_avatar(image_file)
        if not is_valid:
            raise ValidationError(error_msg)