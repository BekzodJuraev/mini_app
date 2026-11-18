def get_user_and_pet_context(profile):
    from datetime import timedelta
    from django.db.models import Count, Q
    from django.utils import timezone
    from .models import (
        Calories,
        Check_Drugs,
        ChildCalendarEvent,
        ChildHealthAnalysisProfile,
        ChildIllnessReport,
        ChildMeasurement,
        Drugs,
        Pet,
        Rentgen,
        Tracking_Habit,
    )
    from .views import calculate_next_measurement_date  # если функция в другом файле — поправь импорт

    strict_short_date = timezone.now().date() - timedelta(days=3)
    today_date = timezone.now().date()
    MAX_FAMILY_MEMBERS = 5

    # --- СХЕМА НАВИГАЦИИ ПО ИНТЕРФЕЙСУ ПРИЛОЖЕНИЯ (ИЗ DOCX) ---
    APP_NAVIGATION_GUIDE = """
Профиль и семья:
- Как открыть главную ребёнка? В нижней панели нажмите «Меню», откройте «Семья» и нажмите на карточку нужного ребёнка. Если вы уже на детской главной и видите стрелки рядом с именем, ребёнка можно переключить этими стрелками.
- Как добавить ребёнка или взрослого? Откройте «Меню» → «Семья», нажмите «Добавить члена семьи» и выберите «Добавить ребенка» или «Добавить взрослого». Если хотите пригласить человека, а не создавать профиль за него, используйте «Семейная ссылка» в том же окне.
- Как добавить питомца? Откройте «Меню» → «Семья» и нажмите «Добавить семейного питомца».

Где скачать отчёт:
- Мой общий PDF (PDF пользователя): Путь: «Меню» → «PDF-отчёт» → скачать общий PDF. Анализы, питание, сводка здоровья и приём лекарств находятся в отдельных разделах одного файла. Скачивать их по отдельности не нужно.
- Детский отчёт по замерам ребёнка: Путь: Главная ребёнка → «Параметры для отслеживания» → «Скачать отчет» (внизу списка периодов). В этот отчёт входят сохранённые замеры и данные о режиме ребёнка.
- Отчёт для педиатра по жалобам: Путь: Главная ребёнка → «Симптомы и жалобы» → «Отчёт для педиатра». Это отчёт по жалобам, а не по замерам роста или пульса.

Параметры для отслеживания ребёнка:
- Как внести рост, вес или окружности? Где посмотреть ИМТ? Главная ребёнка → «Параметры для отслеживания» → нажмите на период с отметкой «Требуется внести данные» → вкладка «Физическое развитие». ИМТ отображается в этой же вкладке и рассчитывается по росту и весу.
- Куда внести температуру, пульс или частоту дыхания? Главная ребёнка → «Параметры для отслеживания» → выберите период с отметкой «Требуется внести данные» → вкладка «Витальные показатели». Если хотите описать, что ребёнку нездоровится, откройте «Симптомы и жалобы».
- Где записать сон, кормление, стул, мочеиспускание, настроение или активность? Главная ребёнка → «Параметры для отслеживания» → период «Требуется внести данные» → вкладка «Режим и поведение». Для дневника еды, калорий и воды используйте отдельный раздел «Питание».
- Как сохранить замер? В «Параметрах для отслеживания» откройте нужную вкладку текущего периода, внесите данные и нажмите «Зафиксировать данные» внизу экрана.
- Где посмотреть старый замер? В «Параметрах для отслеживания» нажмите на период с отметкой «Данные внесены» и откройте нужную вкладку: «Физическое развитие», «Витальные показатели» или «Режим и поведение».
- Когда следующий замер? Откройте «Параметры для отслеживания» и посмотрите дату начала следующего периода. Внутри карточки замера дата также указана рядом с подписью «Следующий замер».

События ребёнка (Прививки и Осмотры):
- Где календарь и события на конкретный день? Главная ребёнка → «События» → выберите нужный месяц и нажмите на дату.
- Где посмотреть запланированные прививки? Главная ребёнка → «События» → нажмите «Прививки» над календарём.
- Где посмотреть запланированные осмотры? Главная ребёнка → «События» → нажмите «Осмотры» над календарём.
- Как отметить сделанную прививку? В «Событиях» выберите дату прививки. Под календарём найдите нужную прививку и нажмите «Прививка пройдена», если кнопка доступна.
- Где посмотреть, что уже пройдено? В разделе «События» нажмите «Пройденные» над календарём. Там отображаются пройденные прививки и осмотры. («Пройденные тесты» в меню — другой раздел).
- Где посмотреть или записать реакцию на прививку? Откройте «События» → нажмите «Реакции» → найдите нужную прививку по названию и дозе → заполните поле и нажмите «Зафиксировать».
- Куда внести результат осмотра или прикрепить файл? В «Событиях» нажмите на дату осмотра и откройте форму результата в карточке события (или «Изменить результаты осмотра») → введите текст или прикрепите файл → «Сохранить».

Симптомы и жалобы ребёнка:
- Как записать новую жалобу? Главная ребёнка → «Симптомы и жалобы» → нажмите «Ребёнку нездоровится» → выберите «Основная жалоба», укажите начало в поле «Когда началось?», действия в поле «Что уже предприняли?», вложение через «Загрузить фото или файл» → нажмите «Зафиксировать».
- Где прошлые жалобы и детали конкретной записи? Главная ребёнка → «Симптомы и жалобы» → в блоке «Прошлые жалобы» нажмите на нужную запись (внутри видны интенсивность, дата начала в поле «Когда началось?», комментарий и вложение; дата в списке — это дата сохранения записи).
- Где посмотреть анализ по жалобам? Главная ребёнка → «Симптомы и жалобы» → блок «Анализ и рекомендации» (нажмите «Показать полностью», если свёрнут).

Анализы, питание, лекарства, тесты и прочее:
- Где мои лабораторные анализы? «Меню» → блок «Разделы для пользователя» → «Анализы» → «Загрузить результаты обследования» (для ребёнка или питомца — в их блоке меню).
- Где мои калории, нутриенты и вода? На своей главной → «Расчет килокалорий». Для ребёнка: главная ребёнка → «Питание».
- Где питание за определённый день? «Расчет килокалорий» (или «Питание» ребёнка) → «Статистика питания» → выберите дату → «Детали».
- Где цели питания или история фотографий еды? На экране «Расчет килокалорий» (или «Питание» ребёнка) → «Цели питания» или «Фотоотчет питания».
- Где добавить лекарство или отметить приём? «Меню» → «Прием лекарств» в блоке нужного профиля → «Добавить лекарство» или «Выпил».
- Где справочная информация о лекарствах? «Меню» → «Аптечка» в блоке нужного профиля.
- Где пройти тест или посмотреть результат? «Меню» → блок нужного профиля → «Тесты» (для нового) или «Пройденные тесты» (для сохранённого результата).
- Где анализ по фото питомца? «Меню» → блок «Разделы для питомца» → «Анализ по фото».
- Как добавить привычку? «Меню» → «Трекер привычек» → «Добавить привычку».
- Как поменять язык или тему? Нижняя панель → «Профиль» → «Настройки» → «Язык приложения» или «Тема приложения».
- Где настроить уведомления? Нижняя панель → «Профиль» → «Уведомления».
- Где ежедневный опрос? На главной пользователя, когда доступен → заполните форму → «Отправить».
- Где квесты и их история? Нижняя панель → «Квесты» → «Пройденные».
- Где риски окружения ребёнка? Главная ребёнка → «Динамика рисков».
- Где мой аватар? Главная пользователя → «Персональный аватар».
- Как открыть чат с ИИ? Круглая синяя кнопка по центру нижней панели.
- Как начать онлайн-консультацию? «Меню» → «Запись на консультацию» → «Начать консультацию» → опишите проблему → «Продолжить».
""".strip()

    def build_child_tracking_data(p) -> dict:
        """
        Собирает полные данные ребёнка:
        1) Жалобы (ChildIllnessReport) со всеми полями (жалоба, когда началось, интенсивность, что предприняли, дата сохранения).
        2) Замеры (ChildMeasurement): физическое развитие, витальные показатели (включая последний сохранённый пульс с датой!), режим, а также текущий и следующий периоды замеров.
        3) Прививки и осмотры (ChildCalendarEvent): ближайшая прививка, ближайший осмотр, список запланированных и пройденных.
        """
        # 1. ИСТОРИЯ ЖАЛОБ РЕБЁНКА (ChildIllnessReport)
        illness_qs = ChildIllnessReport.objects.filter(profile=p).order_by("-created_at")[:15]
        illness_records = []
        for rep in illness_qs:
            illness_records.append({
                "id": rep.id,
                "saved_date": rep.created_at.strftime("%d.%m.%Y %H:%M") if rep.created_at else None,
                "main_complaints": rep.main_complaints,
                "started_at": rep.started_at,
                "intensity": rep.intensity,
                "actions_taken": rep.actions_taken,
                "has_attachment": bool(rep.file_attachment),
            })

        ai_child_analysis = None
        if hasattr(p, "child_health_analysis") and p.child_health_analysis:
            ai_child_analysis = p.child_health_analysis.anaylis_chilld

        # 2. ЗАМЕРЫ, ПОСЛЕДНИЙ ПУЛЬС И ПЕРИОДЫ ЗАМЕРОВ (ChildMeasurement)
        measurements_qs = list(ChildMeasurement.objects.filter(child=p).order_by("scheduled_date", "id"))
        measurements_list = []
        latest_saved_pulse = None
        latest_vital_signs_record = None

        for idx, m in enumerate(measurements_qs):
            # Вычисляем конец периода (за 1 день до следующего замера или через calculate_next_measurement_date)
            if idx + 1 < len(measurements_qs):
                next_sched = measurements_qs[idx + 1].scheduled_date
            else:
                next_sched = calculate_next_measurement_date(p.date_birth, m.scheduled_date)

            period_end = next_sched - timedelta(days=1) if next_sched else m.scheduled_date

            vital = m.vital_signs or {}
            # Ищем сохранённый пульс в разных возможных ключах JSON
            pulse_val = (
                vital.get("pulse")
                or vital.get("пульс")
                or vital.get("Пульс")
                or vital.get("heart_rate")
                or vital.get("ЧСС")
            )
            record_date_str = (
                m.actual_date.strftime("%d.%m.%Y")
                if m.actual_date
                else m.scheduled_date.strftime("%d.%m.%Y")
            )

            if pulse_val not in [None, ""]:
                latest_saved_pulse = {
                    "pulse_value": pulse_val,
                    "measurement_date": record_date_str,
                    "scheduled_period": f"{m.scheduled_date.strftime('%d.%m.%Y')} - {period_end.strftime('%d.%m.%Y')}",
                }

            if vital:
                latest_vital_signs_record = {
                    "date": record_date_str,
                    "vital_signs": vital,
                }

            measurements_list.append({
                "period_start": m.scheduled_date.strftime("%d.%m.%Y"),
                "period_end": period_end.strftime("%d.%m.%Y"),
                "period_display": f"{m.scheduled_date.strftime('%d.%m.%Y')} – {period_end.strftime('%d.%m.%Y')}",
                "next_measurement_start_date": next_sched.strftime("%d.%m.%Y") if next_sched else None,
                "actual_filled_date": m.actual_date.strftime("%d.%m.%Y") if m.actual_date else None,
                "status": m.get_status_display(),
                "status_code": m.status,
                "physical_development": m.physical_development or {},
                "vital_signs": vital,
                "regime_and_behavior": m.regime_and_behavior or {},
            })

        # Определяем текущий и следующий периоды замеров
        current_period_info = None
        next_period_info = None

        for idx, m in enumerate(measurements_qs):
            if idx + 1 < len(measurements_qs):
                next_sched = measurements_qs[idx + 1].scheduled_date
            else:
                next_sched = calculate_next_measurement_date(p.date_birth, m.scheduled_date)
            period_end = next_sched - timedelta(days=1) if next_sched else m.scheduled_date

            if m.scheduled_date <= today_date <= period_end or (m.status == "pending" and m.scheduled_date <= today_date):
                current_period_info = {
                    "period_start": m.scheduled_date.strftime("%d.%m.%Y"),
                    "period_end": period_end.strftime("%d.%m.%Y"),
                    "status": m.get_status_display(),
                }
                next_next_sched = calculate_next_measurement_date(p.date_birth, next_sched)
                next_period_end = next_next_sched - timedelta(days=1) if next_next_sched else next_sched
                next_period_info = {
                    "period_start": next_sched.strftime("%d.%m.%Y"),
                    "period_end": next_period_end.strftime("%d.%m.%Y"),
                }

        # Если все замеры в прошлом или только один последний замер в списке:
        if not current_period_info and measurements_qs:
            last_m = measurements_qs[-1]
            next_sched = calculate_next_measurement_date(p.date_birth, last_m.scheduled_date)
            if last_m.scheduled_date > today_date and len(measurements_qs) >= 2:
                prev_m = measurements_qs[-2]
                prev_end = last_m.scheduled_date - timedelta(days=1)
                current_period_info = {
                    "period_start": prev_m.scheduled_date.strftime("%d.%m.%Y"),
                    "period_end": prev_end.strftime("%d.%m.%Y"),
                    "status": prev_m.get_status_display(),
                }
                next_period_end = next_sched - timedelta(days=1)
                next_period_info = {
                    "period_start": last_m.scheduled_date.strftime("%d.%m.%Y"),
                    "period_end": next_period_end.strftime("%d.%m.%Y"),
                }
            else:
                last_end = next_sched - timedelta(days=1)
                current_period_info = {
                    "period_start": last_m.scheduled_date.strftime("%d.%m.%Y"),
                    "period_end": last_end.strftime("%d.%m.%Y"),
                    "status": last_m.get_status_display(),
                }
                next_next = calculate_next_measurement_date(p.date_birth, next_sched)
                next_period_info = {
                    "period_start": next_sched.strftime("%d.%m.%Y"),
                    "period_end": (next_next - timedelta(days=1)).strftime("%d.%m.%Y"),
                }

        # 3. КАЛЕНДАРЬ ПРИВИВОК И ОСМОТРОВ (ChildCalendarEvent)
        events_qs = ChildCalendarEvent.objects.filter(profile=p).order_by("scheduled_date", "id")

        upcoming_vaccines = []
        upcoming_checkups = []
        completed_events = []

        for ev in events_qs:
            ev_dict = {
                "type": ev.get_event_type_display(),
                "title": ev.title,
                "scheduled_date": ev.scheduled_date.strftime("%d.%m.%Y"),
                "description": ev.description,
                "is_completed": ev.is_completed,
                "completed_at": ev.completed_at.strftime("%d.%m.%Y") if ev.completed_at else None,
                "parent_comment": ev.parent_comment,
                "reaction_text": ev.reaction_text,
                "reaction_date": ev.reaction_date.strftime("%d.%m.%Y") if ev.reaction_date else None,
            }
            if ev.is_completed:
                completed_events.append(ev_dict)
            else:
                if ev.event_type == "vaccine":
                    upcoming_vaccines.append(ev_dict)
                elif ev.event_type == "checkup":
                    upcoming_checkups.append(ev_dict)

        nearest_vaccine = upcoming_vaccines[0] if upcoming_vaccines else None
        nearest_checkup = upcoming_checkups[0] if upcoming_checkups else None

        return {
            "child_name": p.name,
            "birth_date": p.date_birth.strftime("%d.%m.%Y") if p.date_birth else None,
            "illness_complaints_history": illness_records,
            "ai_illness_summary": ai_child_analysis,
            "latest_saved_pulse": latest_saved_pulse,
            "latest_vital_signs": latest_vital_signs_record,
            "current_measurement_period": current_period_info,
            "next_measurement_period": next_period_info,
            "all_measurements_history": measurements_list[-10:],
            "nearest_upcoming_vaccine": nearest_vaccine,
            "nearest_upcoming_checkup": nearest_checkup,
            "upcoming_vaccines_list": upcoming_vaccines[:10],
            "upcoming_checkups_list": upcoming_checkups[:10],
            "completed_vaccines_and_checkups": completed_events[-10:],
        }

    def get_avatar_info(p, previous_health_system: dict | None = None) -> dict:
        """
        Расчет текущего аватара и лаконичной причины выбора на основе обновленной иерархии.
        """
        health_data = getattr(p, "health_system", {}) or {}

        def get_score(data: dict, key: str, default: float = 10.0) -> float:
            val = data.get(key, default)
            if isinstance(val, dict):
                val = val.get("Общий показатель", default)
            try:
                return float(val)
            except (ValueError, TypeError):
                return float(default)

        system_keys = [
            "Дыхательная система", "Пищеварительная система", "Иммунная система",
            "Сердечно-сосудистая система", "Нервная система", "Психологическое состояние",
            "Общий тонус", "Зубочелюстная система", "Опорно-двигательный аппарат",
            "Эндокринная система", "Половая система", "Выделительная система",
            "Органы чувств", "Органы кроветворения"
        ]

        tone = get_score(health_data, "Общий тонус")
        respiratory = get_score(health_data, "Дыхательная система")
        digestive = get_score(health_data, "Пищеварительная система")
        immune = get_score(health_data, "Иммунная система")
        cardio = get_score(health_data, "Сердечно-сосудистая система")
        nervous = get_score(health_data, "Нервная система")
        psychological = get_score(health_data, "Психологическое состояние")

        all_scores = [get_score(health_data, k) for k in system_keys]
        other_scores = [respiratory, digestive, immune, cardio, nervous, psychological]

        is_recovery_condition = False
        if previous_health_system:
            prev_scores = [get_score(previous_health_system, k) for k in system_keys]

            prev_low_4_count = sum(1 for s in prev_scores if s < 4.0)
            curr_low_4_count = sum(1 for s in all_scores if s < 4.0)

            left_red_zone = curr_low_4_count < prev_low_4_count

            has_significant_growth = any(
                (get_score(health_data, k) - get_score(previous_health_system, k)) >= 1.5
                for k in system_keys
                if get_score(previous_health_system, k) < 8.0
            )

            if left_red_zone or has_significant_growth:
                is_recovery_condition = True

        low_4_count = sum(1 for s in all_scores if s < 4.0)
        low_1_count = sum(1 for s in all_scores if s == 1.0)
        low_5_count = sum(1 for s in all_scores if s < 5.0)

        if low_4_count >= 2 or (low_1_count >= 1 and low_5_count >= 3):
            status_name = "Критическое состояние"
            reason = "Когда у пользователя есть выраженные красные показатели, сильные симптомы или сочетание нескольких факторов риска."

        elif is_recovery_condition:
            status_name = "Процесс восстановления"
            reason = "Когда у пользователя показатели начали улучшаться после ухудшения, болезни, стресса, недосыпа или нагрузки."

        elif respiratory < 7.0:
            status_name = "Проблема дыхательной системы"
            reason = "Когда у пользователя есть признаки ухудшения дыхания или повышенные риски для дыхательной системы."

        elif digestive < 7.0:
            status_name = "Проблемы с пищеварением"
            reason = "Когда у пользователя есть признаки ухудшения работы пищеварительной системы или питания."

        elif immune < 7.0:
            status_name = "Снижение иммунитета"
            reason = "Когда у пользователя есть признаки ослабления защитных сил организма или частых воспалительных/инфекционных состояний."

        elif cardio < 7.0 and (nervous < 7.0 or psychological < 7.0):
            status_name = "Стресс / повышенное давление"
            reason = "Когда у пользователя есть признаки стресса, эмоционального напряжения или отклонения по давлению/пульсу."

        elif (4.0 <= tone <= 6.9) and (nervous < 7.0 or psychological < 7.0):
            status_name = "Недостаток сна"
            reason = "Когда у пользователя есть признаки недосыпа, плохого восстановления или регулярного нарушения режима сна."

        elif tone < 4.0:
            status_name = "Переутомление"
            reason = "Когда у пользователя накапливается усталость из-за нагрузки, стресса, недосыпа или плохого восстановления."

        elif (7.0 <= tone <= 8.9) and all(s >= 7.0 for s in other_scores):
            status_name = "Небольшая усталость"
            reason = "Когда у пользователя есть легкое снижение общего тонуса, но без выраженных критических отклонений."

        elif tone >= 9.0 and all(s >= 7.0 for s in other_scores):
            status_name = "Обычное состояние"
            reason = "Когда основные показатели находятся в пределах нормы."

        else:
            status_name = "Обычное состояние"
            reason = "Когда основные показатели находятся в пределах нормы."

        return {
            "current_avatar_status": status_name,
            "algorithm_selection_reason": reason,
            "health_scores_used": {
                "tone": tone,
                "respiratory": respiratory,
                "digestive": digestive,
                "immune": immune,
                "cardio": cardio,
                "nervous": nervous,
                "psychological": psychological,
            },
        }

    def get_object_drugs(obj):
        relation_name = "pet_drugs" if isinstance(obj, Pet) else "drugs"
        if not hasattr(obj, relation_name):
            return []

        drugs_queryset = getattr(obj, relation_name).all().order_by(
            "-created_at"
        )[:10]
        today = timezone.now().date()

        rows = []
        for d in drugs_queryset:
            is_taken_today = False
            if hasattr(d, "notifications"):
                is_taken_today = Check_Drugs.objects.filter(
                    notification__in=d.notifications.all(),
                    date=today,
                    is_taken=True,
                ).exists()

            status_taken = "Принято" if is_taken_today else "Еще не принято"

            rows.append([
                d.catigories,
                d.name,
                d.time_day,
                d.day,
                d.intake,
                str(d.interval) if d.interval else None,
                status_taken,
            ])

        if not rows:
            return []

        return {
            "fields": [
                "category",
                "name",
                "times_per_day",
                "duration_days",
                "intake_instructions",
                "interval",
                "status_taken_today",
            ],
            "rows": rows,
        }

    def build_habits_block(habits_qs):
        rows = [
            [
                h.name_habit,
                (
                    "полезная привычка"
                    if h.type == "good"
                    else "вредная привычка"
                ),
                h.lenght,
                h.completed_days_count,
            ]
            for h in habits_qs
        ]
        if not rows:
            return []
        return {
            "fields": ["name", "type", "streak_days", "completed_days"],
            "rows": rows,
        }

    # === 1. ЦЕЛИ ПОЛЬЗОВАТЕТЕЛЯ (КБЖУ + Вода) ===
    user_nutrition_goals = {}
    if hasattr(profile, "nutrition_goal") and profile.nutrition_goal:
        goal = profile.nutrition_goal
        user_nutrition_goals = {
            "target_calories": goal.calories,
            "target_proteins": goal.proteins,
            "target_fats": goal.fats,
            "target_carbs": goal.carbs,
            "target_fiber": goal.fiber,
        }
    user_nutrition_goals["target_water_liters"] = getattr(
        profile, "water_goal", None
    )

    # === 2. ДАННЫЕ О СЕМЬЕ И ДЕТЯХ ===
    family_data = []
    family_members = set()
    if profile.family:
        family_members.add(profile.family)
        # Если мы находимся внутри дочернего профиля, добавляем и остальных членов семьи родителя
        for sibling in profile.family.family_family.all():
            if sibling.pk != profile.pk:
                family_members.add(sibling)

    for member in profile.family_family.all():
        family_members.add(member)

    children_health_data = []
    # Если сам текущий профиль имеет детские записи (или роль baby), тоже включаем его
    if (
        getattr(profile, "who_is", "") in ["baby", "child", "ребенок", "ребёнок"]
        or ChildMeasurement.objects.filter(child=profile).exists()
        or ChildIllnessReport.objects.filter(profile=profile).exists()
        or ChildCalendarEvent.objects.filter(profile=profile).exists()
    ):
        children_health_data.append(build_child_tracking_data(profile))

    for member in list(family_members)[:MAX_FAMILY_MEMBERS]:
        m_tests = list(
            member.tests.exclude(message=None).order_by("-created_at")[:3]
        )
        m_tests_history = [f"{t.name}: {t.message}" for t in m_tests]

        m_habits_with_counts = member.habit.all().annotate(
            completed_days_count=Count(
                "habit_tracking",
                filter=Q(
                    habit_tracking__profile=member, habit_tracking__check_is=True
                ),
            )
        )
        m_habits = build_habits_block(m_habits_with_counts)

        member_child_tracking = build_child_tracking_data(member)
        if (
            member_child_tracking["illness_complaints_history"]
            or member_child_tracking["all_measurements_history"]
            or member_child_tracking["upcoming_vaccines_list"]
            or member_child_tracking["upcoming_checkups_list"]
            or getattr(member, "who_is", "") in ["baby", "child", "ребенок", "ребёнок"]
        ):
            children_health_data.append(member_child_tracking)

        family_data.append({
            "name": member.name,
            "who_is": getattr(member, "who_is", None),
            "gender": member.gender,
            "birth_date": (
                member.date_birth.strftime("%Y-%m-%d")
                if member.date_birth
                else None
            ),
            "height": member.height,
            "weight": member.weight,
            "medical_history_anamnesis": member.medical_history or {},
            "health_indicators_score": member.health_system or {},
            "active_drugs_list": get_object_drugs(member),
            "habits": m_habits,
            "recent_medical_tests": m_tests_history,
            "child_tracking_data": member_child_tracking,
        })

    # === 3. ДАННЫЕ О ПИТОМЦАХ ===
    pets_data = []
    for pet in profile.pet.all():
        pet_tests = list(
            pet.tests_pet.exclude(message=None).order_by("-created_at")[:3]
        )
        pet_tests_history = [f"{pt.name}: {pt.message}" for pt in pet_tests]

        pet_calories_short = pet.pet_calories.filter(
            created_at__gte=strict_short_date, saved=True
        ).order_by("-created_at")

        pet_food_history = [
            {"date": pc.created_at.strftime("%Y-%m-%d"), "detail": pc.detail}
            for pc in pet_calories_short
            if pc.detail
        ]

        pet_nutrition_goals = {}
        if hasattr(pet, "nutrition_goal_pet") and pet.nutrition_goal_pet:
            p_goal = pet.nutrition_goal_pet
            pet_nutrition_goals = {
                "target_calories": p_goal.calories,
                "target_proteins": p_goal.proteins,
                "target_fats": p_goal.fats,
                "target_carbs": p_goal.carbs,
                "target_fiber": p_goal.fiber,
            }

        pet_habits_with_counts = (
            pet.habit.all().annotate(
                completed_days_count=Count(
                    "habit_tracking", filter=Q(habit_tracking__check_is=True)
                )
            )
            if hasattr(pet, "habit")
            else []
        )

        pet_habits_list = build_habits_block(pet_habits_with_counts)

        pets_data.append({
            "name": pet.klichka,
            "type": pet.pet,
            "gender": pet.gender,
            "birth_date": (
                pet.age.strftime("%Y-%m-%d") if pet.age else None
            ),
            "medical_history_anamnesis": pet.medical_history or {},
            "health_system_metrics": pet.health_system or {},
            "active_drugs_list": get_object_drugs(pet),
            "habits_list": pet_habits_list,
            "last_medical_tests_details": pet_tests_history,
            "nutrition_history_last_3_days": pet_food_history,
            "nutrition_goals": pet_nutrition_goals,
        })

    # === 4. ДИНАМИЧЕСКИЕ ЗАПИСИ ПОЛЬЗОВАТЕЛЯ ===
    human_tests = list(
        profile.tests.exclude(message=None)
        .order_by("-created_at", "-id")[:3]
    )

    human_tests_history = [
        f"[{t.created_at.strftime('%Y-%m-%d %H:%M')}] {t.name}: {t.message}"
        for t in human_tests
    ]

    rentgen_records = list(
        profile.rentgen.exclude(answer=None).order_by("-created_at")[:3]
    )
    rentgen_history = [f"{r.message}: {r.answer}" for r in rentgen_records]

    pressure_records = list(
        profile.pressure_history.order_by("-created_at")[:3]
    )
    pressure_history = [
        f"{p.pressure_top}/{p.pressure_bottom}" for p in pressure_records
    ]

    habits_with_counts = profile.habit.all().annotate(
        completed_days_count=Count(
            "habit_tracking",
            filter=Q(
                habit_tracking__profile=profile, habit_tracking__check_is=True
            ),
        )
    )
    habits_list = build_habits_block(habits_with_counts)

    daily_checks = list(
        profile.daily_check.exclude(message=None).order_by(
            "-created_at", "-id"
        )[:3]
    )
    daily_checks.reverse()
    daily_checks_history = [
        {
            "date": (
                check.created_at.strftime("%Y-%m-%d")
                if check.created_at
                else "Неизвестно"
            ),
            "report": check.message,
        }
        for check in daily_checks
    ]

    calories_short_days = Calories.objects.filter(
        profile=profile, created_at__date__gte=strict_short_date, saved=True
    ).order_by("-created_at")

    human_food_history = []
    total_water_short_days = 0.0

    for c in calories_short_days:
        if c.detail:
            human_food_history.append({
                "date": c.created_at.strftime("%Y-%m-%d"),
                "detail": c.detail,
            })
        if c.water_intake:
            total_water_short_days += c.water_intake

    # === 5. ДАННЫЕ О ЖЕНСКОМ ЗДОРОВЬЕ И ЦИКЛЕ ===
    women_health_data = {}
    if getattr(profile, "gender", "").lower() in ["female", "ж", "женский"]:
        cycle_periods = list(
            profile.periods.all().order_by("-start_date")[:3]
        )
        periods_history = [
            {
                "start_date": p.start_date.strftime("%Y-%m-%d"),
                "end_date": (
                    p.end_date.strftime("%Y-%m-%d") if p.end_date else "Текущий"
                ),
            }
            for p in cycle_periods
        ]

        daily_logs = list(
            profile.daily_logs.all().order_by("-created_at")[:5]
        )
        logs_history = [
            {
                "date": log.created_at.strftime("%Y-%m-%d"),
                "note": log.note,
                "pain": log.pain or {},
                "mood": log.mood or {},
                "activities": log.activities or {},
                "pregnancy_symptoms": log.pregnancy or {},
            }
            for log in daily_logs
        ]

        notifications = list(
            profile.notificationfemale.all().order_by("-created_at")[:3]
        )
        notifs_history = [
            {
                "title": n.title,
                "description": n.description,
                "date": n.created_at.strftime("%Y-%m-%d"),
                "three_days_before": n.three_days_before,
            }
            for n in notifications
        ]

        women_health_data = {
            "is_pregnant": getattr(profile, "is_pregnant", False),
            "pregnancy_start_date": (
                profile.pregnancy_start_date.strftime("%Y-%m-%d")
                if getattr(profile, "pregnancy_start_date", None)
                else None
            ),
            "recent_cycle_periods": periods_history,
            "recent_daily_symptom_logs": logs_history,
            "female_calendar_notifications": notifs_history,
        }

    # === 6. ИТОГОВЫЙ СБОР КЛИЕНТСКИХ ДАННЫХ ===
    return {
        "user_info": {
            "name": profile.name,
            "who_is": getattr(profile, "who_is", None),
            "gender": profile.gender,
            "birth_date": (
                profile.date_birth.strftime("%Y-%m-%d")
                if profile.date_birth
                else None
            ),
            "height": profile.height,
            "weight": profile.weight,
            "place_of_residence": profile.place_of_residence,
            "medical_history_anamnesis": profile.medical_history or {},
            "health_indicators_score": profile.health_system or {},
            "calculated_life_expectancy": profile.life_expectancy,
            "active_drugs_list": get_object_drugs(profile),
        },
        "user_avatar": get_avatar_info(profile, profile.previous_health_system),
        "user_nutrition_and_water_goals": user_nutrition_goals,
        "user_family_members": family_data,
        "user_children_health": children_health_data,
        "app_navigation": APP_NAVIGATION_GUIDE,
        "user_pets": pets_data,
        "user_daily_checkups_recent_days": daily_checks_history,
        "user_medical_tests": human_tests_history,
        "user_rentgen_and_mri_reports": rentgen_history,
        "user_blood_pressure_history": pressure_history,
        "user_habits": habits_list,
        "user_nutrition_history_recent_days": {
            "food_records": human_food_history,
            "total_water_intake_liters_recent_days": total_water_short_days,
        },
        "user_women_health": women_health_data,
    }