from datetime import date, datetime
from django.apps import apps
from django.db import models


def serialize_model_instance(obj):
    """Преобразует экземпляр модели в словарь,

    пропуская файлы/картинки и форматируя даты.
    """
    if not obj:
        return None

    data = {}
    for field in obj._meta.fields:
        if isinstance(field, (models.FileField, models.ImageField)):
            continue

        val = getattr(obj, field.name)

        if isinstance(val, (date, datetime)):
            val = val.isoformat()
        elif hasattr(val, "hex"):  # UUID
            val = str(val)

        data[field.name] = val

    return data


def build_user_data_payload(
    profile, models_list: list = None, records: int = 3
) -> dict:
    """Собирает данные из профиля и указанных моделей.

    :param profile: Объект модели Profile
    :param models_list: Список названий моделей/связей (например, ['tests',
    'daily_check', 'chat'])
    :param records: Количество последних записей для каждой модели (по умолчанию
    3)
    """
    if not profile:
        return {}

    # 1. Базовая информация из самого Profile
    payload = {
        "profile": {
           # "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "age": profile.date_birth,
            "height": profile.height,
            "weight": profile.weight,
            "medical_history": profile.medical_history,
           # "health_system": profile.health_system,
        }
    }

    # Если список моделей не передан, берем дефолтный набор
    if models_list is None:
        models_list = [
            "tests",
            "daily_check",
            "chat",
            "men_health",
            "Critical_analysis",
        ]

    # 2. Обходим каждую запрошенную модель/связь
    for model_item in models_list:
        # Приводим к нижнему регистру для гибкости (например, "Tests" -> "tests")
        key = model_item.lower()

        # Случай 1: Если это OneToOne связь (например, men_health)
        if hasattr(profile, key) and isinstance(
            getattr(profile, key), models.Model
        ):
            payload[key] = serialize_model_instance(getattr(profile, key))

        # Случай 2: Если это RelatedManager / ForeignKey связь (tests, daily_check, chat)
        elif hasattr(profile, key):
            rel_attr = getattr(profile, key)
            qs = rel_attr.all()

            # Сортируем по дате создания или ID, если есть
            model_fields = [f.name for f in qs.model._meta.fields]
            if "created_at" in model_fields:
                qs = qs.order_by("-created_at")
            elif "id" in model_fields:
                qs = qs.order_by("-id")

            payload[key] = [
                serialize_model_instance(obj) for obj in qs[:records]
            ]

        # Случай 3: Если передали имя модели без прямого FK на Profile (например, Critical_analysis)
        else:
            try:
                # Пытаемся найти модель в приложении (замени 'backend' на имя своего app)
                model_cls = apps.get_model(
                    app_label="backend", model_name=model_item
                )
                qs = model_cls.objects.all()

                model_fields = [f.name for f in model_cls._meta.fields]
                if "id" in model_fields:
                    qs = qs.order_by("-id")

                payload[key] = [
                    serialize_model_instance(obj) for obj in qs[:records]
                ]
            except Exception:
                # Если связь не найдена — просто пропускаем
                continue

    return payload