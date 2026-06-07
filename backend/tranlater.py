import hashlib
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response
from .prompt import translate_text_on_the_fly



import json
from functools import wraps
from rest_framework.response import Response


def translate_api_response(fields=None, key_fields=None):
    """
    Полностью универсальный декоратор для любых методов APIView (GET, POST и др.).

    :param fields: список полей для ПОЛНОГО перевода строк.
    :param key_fields: список полей, где переводятся ТОЛЬКО КЛЮЧИ/НАЗВАНИЯ (цифры остаются из БД).
    """
    target_fields = set(fields) if fields else set()
    target_keys = set(key_fields) if key_fields else set()

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # 1. Читаем язык строго из заголовка Accept-Language
            lang = request.headers.get('Accept-Language', 'ru')[:2].lower()

            # 2. Выполняем саму вьюху (работает для GET, POST, PUT)
            response = view_func(self, request, *args, **kwargs)

            # Если язык русский или ответ не успешный (не 200/201) — сразу отдаем оригинал
            if lang == 'ru' or not isinstance(response, Response) or response.status_code not in [200, 201]:
                return response

            def get_cached_translation(text, target_lang):
                """Хелпер точечного кэширования строк и названий через MD5"""
                if not text or not isinstance(text, str) or text.isdigit() or text.startswith(('http://', 'https://')):
                    return text

                text_hash = hashlib.md5(f"{text}_{target_lang}".encode('utf-8')).hexdigest()
                cache_key = f"ai_trans_{text_hash}"

                translated = cache.get(cache_key)
                if not translated:
                    # Вызов твоей базовой функции gpt-4o-mini
                    translated = translate_text_on_the_fly(text, target_lang)
                    cache.set(cache_key, translated, timeout=60 * 60 * 24 * 30)  # Кэш на 30 дней
                return translated

            def transform_data(data):
                """Рекурсивный обход и мутация чистого Python JSON-а"""
                if isinstance(data, dict):
                    # Если мы обрабатываем элемент структуры, чьё имя (или ключ) числится в key_fields
                    if 'name' in data and data['name'] in target_keys:
                        translated_name = get_cached_translation(data['name'], lang)
                        if isinstance(data.get('value'), dict):
                            # Переводим только ключи внутреннего словаря, цифры не трогаем
                            return {
                                "name": translated_name,
                                "value": {get_cached_translation(k, lang): v for k, v in data['value'].items()}
                            }
                        return {"name": translated_name, "value": data.get('value')}

                    new_dict = {}
                    for key, value in data.items():
                        # РЕЖИМ 1: Полный перевод строк (сообщения, текстовые отчеты)
                        if key in target_fields and isinstance(value, str) and value:
                            new_dict[key] = get_cached_translation(value, lang)

                        # РЕЖИМ 2: Перевод только ключей словаря, если сам ключ совпал с key_fields
                        elif key in target_keys and isinstance(value, dict):
                            new_dict[key] = {get_cached_translation(k, lang): v for k, v in value.items()}

                        # Стандартный рекурсивный проход вглубь структуры
                        elif isinstance(value, (dict, list)):
                            new_dict[key] = transform_data(value)
                        else:
                            new_dict[key] = value
                    return new_dict

                elif isinstance(data, list):
                    return [transform_data(item) for item in data]

                return data

            # 3. Сброс DRF-типов и запуск трансформации
            if response.data:
                pure_python_data = json.loads(json.dumps(response.data))
                response.data = transform_data(pure_python_data)

            return response

        return _wrapped_view

    return decorator


def translate_health_keys_api(view_func):
    """
    Декоратор для APIView. Переводит НАЗВАНИЯ систем и органов (ключи),
    сохраняя актуальные цифровые значения из БД. Использует кэш.
    """

    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        # 1. Читаем язык из заголовка Accept-Language
        lang = request.headers.get('Accept-Language', 'ru')[:2].lower()

        # 2. Выполняем саму вьюху (получаем свежие данные из БД)
        response = view_func(self, request, *args, **kwargs)

        # Если язык русский или ответ не 200 OK — отдаем оригинал без затрат ресурсов
        if lang == 'ru' or not isinstance(response, Response) or response.status_code != 200:
            return response

        def get_cached_word_translation(word, target_lang):
            """Кэширует перевод одиночных слов/названий органов, чтобы не дёргать ИИ"""
            if not word or not isinstance(word, str) or word.isdigit():
                return word

            # Создаем уникальный ключ кэша для конкретного слова
            word_hash = hashlib.md5(f"{word}_{target_lang}".encode('utf-8')).hexdigest()
            cache_key = f"dict_trans_{word_hash}"

            translated = cache.get(cache_key)
            if not translated:
                # Вызываем твою базовую функцию перевода gpt-4o-mini
                translated = translate_text_on_the_fly(word, target_lang)
                # Сохраняем в кэш на 30 дней, так как названия органов не меняются
                cache.set(cache_key, translated, timeout=60 * 60 * 24 * 30)
            return translated

        def transform_health_structure(data):
            """Рекурсивно обрабатывает структуру, переводя только имена и ключи"""
            if isinstance(data, dict):
                # Если это элемент твоей структуры с ключами 'name' и 'value'
                if 'name' in data and 'value' in data:
                    translated_name = get_cached_word_translation(data['name'], lang)

                    # Если внутри value лежит словарь (метрики органов)
                    if isinstance(data['value'], dict):
                        translated_inner_dict = {}
                        for inner_key, inner_val in data['value'].items():
                            # Переводим КЛЮЧ (название органа), а inner_val (цифру) берем как есть из БД
                            translated_key = get_cached_word_translation(inner_key, lang)
                            translated_inner_dict[translated_key] = inner_val

                        return {
                            "name": translated_name,
                            "value": translated_inner_dict
                        }

                    # Если value — это не словарь (например, просто число 8 для Общего тонуса)
                    return {
                        "name": translated_name,
                        "value": data['value']
                    }

                # Стандартный обход для верхнего уровня JSON
                new_dict = {}
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        new_dict[key] = transform_health_structure(value)
                    else:
                        new_dict[key] = value
                return new_dict

            elif isinstance(data, list):
                return [transform_health_structure(item) for item in data]

            return data

        # 3. Очищаем DRF-типы и запускаем безопасный перевод ключей
        if response.data:
            pure_python_data = json.loads(json.dumps(response.data))
            response.data = transform_health_structure(pure_python_data)

        return response

    return _wrapped_view