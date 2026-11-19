from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from .models import ChildCalendarEvent

# Расписание по месяцам и дням со скриншотов:
# (months, extra_days, event_type, title, description)
SCHEDULE_TEMPLATE = [
    # Рождение (0 месяцев)
    (
        0, 1, 'vaccine',
        'БЦЖ',
        'BSJ',
        'BCG',
        'Вакцинация против туберкулёза для формирования раннего иммунитета к тяжёлым формам заболевания.',
        'Sil kasalligining og‘ir shakllariga qarshi erta immunitet shakllantirish uchun emlash.',
        'Vaccination against tuberculosis to build early immunity against severe forms of the disease.',
    ),
    (
        0, 3, 'vaccine',
        'Гепатит B (1 доза)',
        'Gepatit B (1-doza)',
        'Hepatitis B (Dose 1)',
        'Первая вакцина против вирусного гепатита B для формирования иммунитета к инфекции печени.',
        'Jigar infeksiyasiga qarshi immunitet shakllantirish uchun virusli gepatit B ga qarshi birinchi vaksina.',
        'First dose of the hepatitis B vaccine to build immunity against liver infection.',
    ),

    # 1 месяц
    (
        1, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Плановый осмотр для оценки общего состояния ребёнка, роста, веса и питания.',
        'Bolaning umumiy holati, bo‘yi, vazni va ovqatlanishini baholash uchun rejali ko‘rik.',
        'Routine checkup to assess the child’s general health, height, weight, and feeding.',
    ),
    (
        1, 5, 'vaccine',
        'Гепатит B (2 доза)',
        'Gepatit B (2-doza)',
        'Hepatitis B (Dose 2)',
        'Продолжение формирования иммунитета против вирусного гепатита B.',
        'Virusli gepatit B ga qarshi immunitet shakllantirishni davom ettirish.',
        'Continuation of immunity development against viral hepatitis B.',
    ),

    # 2 месяца
    (
        2, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Контроль физического развития ребёнка и оценка состояния здоровья.',
        'Bolaning jismoniy rivojlanishini nazorat qilish va sog‘lig‘ini baholash.',
        'Monitoring the child’s physical development and assessing overall health.',
    ),
    (
        2, 5, 'vaccine',
        'Пневмококковая вакцина (1 доза)',
        'Pnevmokokk vaksinasi (1-doza)',
        'Pneumococcal vaccine (Dose 1)',
        'Вакцина против инфекций, вызываемых пневмококком: пневмонии, менингита и других осложнений.',
        'Pnevmokokk keltirib chiqaradigan infeksiyalar: pnevmoniya, meningit va boshqa asoratlarga qarshi vaksina.',
        'Vaccine against pneumococcal infections, including pneumonia, meningitis, and other complications.',
    ),

    # 3 месяца
    (
        3, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Оценка физического и нервно-психического развития ребёнка.',
        'Bolaning jismoniy va asab-ruhiy rivojlanishini baholash.',
        'Assessment of the child’s physical and neuropsychiatric development.',
    ),
    (
        3, 5, 'vaccine',
        'АКДС (1 доза)',
        'AKDS (1-doza)',
        'DTP (Dose 1)',
        'Вакцина против коклюша, дифтерии и столбняка.',
        'Ko‘kyo‘tal, difteriya va qoqsholga qarshi vaksina.',
        'Vaccine against pertussis (whooping cough), diphtheria, and tetanus.',
    ),
    (
        3, 8, 'vaccine',
        'Полиомиелит (1 доза)',
        'Poliomiyelit (1-doza)',
        'Polio (Dose 1)',
        'Вакцинация против полиомиелита.',
        'Poliomiyelitga qarshi emlash.',
        'Vaccination against poliomyelitis.',
    ),
    (
        3, 11, 'vaccine',
        'Хиб-инфекция (1 доза)',
        'Hib-infeksiya (1-doza)',
        'Hib infection (Dose 1)',
        'Вакцина против гемофильной инфекции, которая может вызывать менингит и пневмонию.',
        'Meningit va pnevmoniya keltirib chiqarishi mumkin bo‘lgan gemofil infeksiyaga qarshi vaksina.',
        'Vaccine against Haemophilus influenzae type b, which can cause meningitis and pneumonia.',
    ),

    # 4 месяца 15 дней
    (
        4, 15, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Контроль развития ребёнка и подготовка к следующей вакцинации.',
        'Bola rivojlanishini nazorat qilish va keyingi emlashga tayyorgarlik.',
        'Monitoring the child’s development and preparing for the next vaccination.',
    ),
    (
        4, 20, 'vaccine',
        'АКДС (2 доза)',
        'AKDS (2-doza)',
        'DTP (Dose 2)',
        'Продолжение вакцинации против коклюша, дифтерии и столбняка.',
        'Ko‘kyo‘tal, difteriya va qoqsholga qarshi emlashni davom ettirish.',
        'Continuation of vaccination against pertussis, diphtheria, and tetanus.',
    ),
    (
        4, 23, 'vaccine',
        'Полиомиелит (2 доза)',
        'Poliomiyelit (2-doza)',
        'Polio (Dose 2)',
        'Вторая доза против полиомиелита.',
        'Poliomiyelitga qarshi ikkinchi doza.',
        'Second dose against poliomyelitis.',
    ),
    (
        4, 26, 'vaccine',
        'Хиб-инфекция (2 доза)',
        'Hib-infeksiya (2-doza)',
        'Hib infection (Dose 2)',
        'Вторая доза против гемофильной инфекции.',
        'Gemofil infeksiyaga qarshi ikkinchi doza.',
        'Second dose against Haemophilus influenzae type b.',
    ),
    (
        4, 29, 'vaccine',
        'Пневмококковая вакцина (2 доза)',
        'Pnevmokokk vaksinasi (2-doza)',
        'Pneumococcal vaccine (Dose 2)',
        'Продолжение защиты от пневмококковых инфекций.',
        'Pnevmokokk infeksiyalaridan himoyani davom ettirish.',
        'Continued protection against pneumococcal infections.',
    ),

    # 6 месяцев
    (
        6, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Проверка физического развития и общего состояния здоровья.',
        'Jismoniy rivojlanish va umumiy sog‘liq holatini tekshirish.',
        'Checking physical development and general health.',
    ),
    (
        6, 5, 'vaccine',
        'АКДС (3 доза)',
        'AKDS (3-doza)',
        'DTP (Dose 3)',
        'Завершение основного курса вакцинации АКДС.',
        'AKDS emlashining asosiy kursini yakunlash.',
        'Completion of the primary DTP vaccination series.',
    ),
    (
        6, 8, 'vaccine',
        'Полиомиелит (3 доза)',
        'Poliomiyelit (3-doza)',
        'Polio (Dose 3)',
        'Продолжение вакцинации против полиомиелита.',
        'Poliomiyelitga qarshi emlashni davom ettirish.',
        'Continuation of vaccination against poliomyelitis.',
    ),
    (
        6, 11, 'vaccine',
        'Хиб-инфекция (3 доза)',
        'Hib-infeksiya (3-doza)',
        'Hib infection (Dose 3)',
        'Завершение основного курса вакцинации против гемофильной инфекции.',
        'Gemofil infeksiyaga qarshi asosiy emlash kursini yakunlash.',
        'Completion of the primary vaccination series against Hib infection.',
    ),
    (
        6, 14, 'vaccine',
        'Гепатит B (3 доза)',
        'Gepatit B (3-doza)',
        'Hepatitis B (Dose 3)',
        'Завершение базовой вакцинации против гепатита B.',
        'Gepatit B ga qarshi asosiy emlash kursini yakunlash.',
        'Completion of the primary vaccination series against hepatitis B.',
    ),

    # 9 месяцев
    (
        9, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Оценка развития ребёнка, питания и общего состояния здоровья.',
        'Bola rivojlanishi, ovqatlanishi va umumiy sog‘liq holatini baholash.',
        'Assessment of the child’s development, nutrition, and general health.',
    ),

    # 12 месяцев (1 год)
    (
        12, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Комплексная оценка физического развития ребёнка.',
        'Bolaning jismoniy rivojlanishini kompleks baholash.',
        'Comprehensive assessment of the child’s physical development.',
    ),
    (
        12, 3, 'checkup',
        'Осмотр невролога',
        'Nevrolog ko‘rigi',
        'Neurologist checkup',
        'Проверка развития нервной системы и двигательных навыков.',
        'Asab tizimi va harakat ko‘nikmalari rivojlanishini tekshirish.',
        'Evaluation of nervous system development and motor skills.',
    ),
    (
        12, 6, 'checkup',
        'Осмотр ортопеда',
        'Ortoped ko‘rigi',
        'Orthopedist checkup',
        'Оценка развития опорно-двигательного аппарата и осанки.',
        'Tayanch-harakat tizimi va qomat rivojlanishini baholash.',
        'Assessment of the musculoskeletal system and posture.',
    ),
    (
        12, 9, 'checkup',
        'Осмотр офтальмолога',
        'Oftalmolog ko‘rigi',
        'Ophthalmologist checkup',
        'Проверка зрения и состояния глаз.',
        'Ko‘rish qobiliyati va ko‘z holatini tekshirish.',
        'Vision and eye health examination.',
    ),
    (
        12, 12, 'checkup',
        'Осмотр стоматолога',
        'Stomatolog ko‘rigi',
        'Dentist checkup',
        'Проверка формирования зубов и профилактика заболеваний полости рта.',
        'Tishlarning shakllanishini tekshirish va og‘iz bo‘shlig‘i kasalliklarining oldini olish.',
        'Checking tooth development and preventing oral diseases.',
    ),
    (
        12, 16, 'vaccine',
        'КПК (корь, краснуха, паротит)',
        'QPK (qizamiq, qizilcha, parotit)',
        'MMR (Measles, Mumps, Rubella)',
        'Вакцина формирует иммунитет против кори, краснухи и эпидемического паротита.',
        'Vaksina qizamiq, qizilcha va epidemik parotitga qarshi immunitet shakllantiradi.',
        'The vaccine builds immunity against measles, rubella, and mumps.',
    ),

    # 15 месяцев
    (
        15, 0, 'vaccine',
        'Пневмококковая ревакцинация',
        'Pnevmokokk revaksinatsiyasi',
        'Pneumococcal booster',
        'Поддержание иммунитета против пневмококковой инфекции.',
        'Pnevmokokk infeksiyasiga qarshi immunitetni saqlab turish.',
        'Maintaining immunity against pneumococcal infection.',
    ),

    # 18 месяцев (1.5 года)
    (
        18, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Контроль физического и психомоторного развития ребёнка.',
        'Bolaning jismoniy va psixomotor rivojlanishini nazorat qilish.',
        'Monitoring the child’s physical and psychomotor development.',
    ),
    (
        18, 5, 'vaccine',
        'АКДС (ревакцинация)',
        'AKDS (revaksinatsiya)',
        'DTP (Booster)',
        'Поддержание иммунитета против коклюша, дифтерии и столбняка.',
        'Ko‘kyo‘tal, difteriya va qoqsholga qarshi immunitetni saqlab turish.',
        'Maintaining immunity against pertussis, diphtheria, and tetanus.',
    ),
    (
        18, 8, 'vaccine',
        'Полиомиелит (ревакцинация)',
        'Poliomiyelit (revaksinatsiya)',
        'Polio (Booster)',
        'Поддержание иммунитета против полиомиелита.',
        'Poliomiyelitga qarshi immunitetni saqlab turish.',
        'Maintaining immunity against poliomyelitis.',
    ),

    # 2 года (24 месяца)
    (
        24, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Плановая оценка физического развития ребёнка.',
        'Bolaning jismoniy rivojlanishini rejali baholash.',
        'Routine assessment of the child’s physical development.',
    ),
    (
        24, 7, 'checkup',
        'Осмотр стоматолога',
        'Stomatolog ko‘rigi',
        'Dentist checkup',
        'Проверка состояния зубов и профилактика кариеса.',
        'Tishlar holatini tekshirish va kariyesning oldini olish.',
        'Checking dental health and preventing cavities.',
    ),

    # 3 года (36 месяцев)
    (
        36, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Контроль роста, веса и общего состояния здоровья.',
        'Bo‘y, vazn va umumiy sog‘liq holatini nazorat qilish.',
        'Monitoring height, weight, and general health.',
    ),
    (
        36, 3, 'checkup',
        'Осмотр невролога',
        'Nevrolog ko‘rigi',
        'Neurologist checkup',
        'Проверка нервной системы и развития моторики.',
        'Asab tizimi va motorika rivojlanishini tekshirish.',
        'Checking the nervous system and motor development.',
    ),
    (
        36, 6, 'checkup',
        'Осмотр ортопеда',
        'Ortoped ko‘rigi',
        'Orthopedist checkup',
        'Оценка осанки и развития опорно-двигательной системы.',
        'Qomat va tayanch-harakat tizimi rivojlanishini baholash.',
        'Evaluating posture and musculoskeletal development.',
    ),
    (
        36, 9, 'checkup',
        'Осмотр офтальмолога',
        'Oftalmolog ko‘rigi',
        'Ophthalmologist checkup',
        'Диагностика зрения.',
        'Ko‘rish qobiliyatini diagnostika qilish.',
        'Vision diagnostics.',
    ),
    (
        36, 12, 'checkup',
        'Осмотр стоматолога',
        'Stomatolog ko‘rigi',
        'Dentist checkup',
        'Контроль состояния зубов.',
        'Tishlar holatini nazorat qilish.',
        'Dental health checkup.',
    ),

    # 6 лет (72 месяца)
    (
        72, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Плановый осмотр перед началом школьного возраста.',
        'Maktab yoshidan oldingi rejali ko‘rik.',
        'Routine checkup before starting school.',
    ),
    (
        72, 3, 'checkup',
        'Осмотр невролога',
        'Nevrolog ko‘rigi',
        'Neurologist checkup',
        'Оценка нервной системы и когнитивного развития.',
        'Asab tizimi va kognitiv rivojlanishni baholash.',
        'Assessment of the nervous system and cognitive development.',
    ),
    (
        72, 6, 'checkup',
        'Осмотр ортопеда',
        'Ortoped ko‘rigi',
        'Orthopedist checkup',
        'Проверка позвоночника и осанки.',
        'Umurtqa pog‘onasi va qomatni tekshirish.',
        'Spine and posture examination.',
    ),
    (
        72, 9, 'checkup',
        'Осмотр офтальмолога',
        'Oftalmolog ko‘rigi',
        'Ophthalmologist checkup',
        'Проверка зрения.',
        'Ko‘rish qobiliyatini tekshirish.',
        'Vision check.',
    ),
    (
        72, 12, 'checkup',
        'Осмотр стоматолога',
        'Stomatolog ko‘rigi',
        'Dentist checkup',
        'Контроль состояния зубов.',
        'Tishlar holatini nazorat qilish.',
        'Dental health checkup.',
    ),
    (
        72, 16, 'vaccine',
        'КПК (ревакцинация)',
        'QPK (revaksinatsiya)',
        'MMR (Booster)',
        'Повторная вакцина против кори, краснухи и паротита.',
        'Qizamiq, qizilcha va parotitga qarshi takroriy vaksina.',
        'Booster vaccine against measles, rubella, and mumps.',
    ),
    # ПРАВКА 2: 6 лет + 10 дней (было 20 -> стало 10)
    (
        72, 10, 'vaccine',
        'Дифтерия и столбняк',
        'Difteriya va qoqshol',
        'Diphtheria and Tetanus',
        'Вакцина для поддержания иммунитета против дифтерии и столбняка.',
        'Difteriya va qoqsholga qarshi immunitetni saqlab turish uchun vaksina.',
        'Vaccine to maintain immunity against diphtheria and tetanus.',
    ),

    # 7 лет (84 месяца) — ПРАВКА 3: обновлённое описание БЦЖ
    (
        84, 0, 'vaccine',
        'БЦЖ',
        'BSJ',
        'BCG',
        'Проводится при отсутствии иммунитета к туберкулёзу. Необходимость ревакцинации определяет врач по результатам обследования. Уточните у педиатра, показана ли она ребёнку.',
        'Sil kasalligiga qarshi immunitet bo‘lmaganda o‘tkaziladi. Revaksinatsiya zarurligini shifokor tekshiruv natijalariga ko‘ra belgilaydi. Bolaga bu emlash kerakligini pediatrdan aniqlashtiring.',
        'Administered in the absence of immunity to tuberculosis. The need for revaccination is determined by a doctor based on examination results. Check with your pediatrician whether it is indicated for your child.',
    ),

    # 10 лет (120 месяцев)
    (
        120, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Плановый контроль физического развития.',
        'Jismoniy rivojlanishni rejali nazorat qilish.',
        'Routine monitoring of physical development.',
    ),
    (
        120, 5, 'checkup',
        'Осмотр ортопеда',
        'Ortoped ko‘rigi',
        'Orthopedist checkup',
        'Проверка осанки и позвоночника.',
        'Qomat va umurtqa pog‘onasini tekshirish.',
        'Posture and spine examination.',
    ),
    (
        120, 10, 'checkup',
        'Осмотр офтальмолога',
        'Oftalmolog ko‘rigi',
        'Ophthalmologist checkup',
        'Контроль состояния зрения.',
        'Ko‘rish holatini nazorat qilish.',
        'Vision monitoring.',
    ),

    # 14 лет (168 месяцев)
    (
        168, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Контроль состояния здоровья в период подросткового развития.',
        'O‘smirlik davrida sog‘liq holatini nazorat qilish.',
        'Health monitoring during adolescent development.',
    ),
    (
        168, 5, 'checkup',
        'Осмотр стоматолога',
        'Stomatolog ko‘rigi',
        'Dentist checkup',
        'Профилактика заболеваний зубов и дёсен.',
        'Tish va milk kasalliklarining oldini olish.',
        'Prevention of tooth and gum diseases.',
    ),
    (
        168, 10, 'vaccine',
        'Дифтерия и столбняк (ревакцинация)',
        'Difteriya va qoqshol (revaksinatsiya)',
        'Diphtheria and Tetanus (Booster)',
        'Поддержание иммунитета против дифтерии и столбняка.',
        'Difteriya va qoqsholga qarshi immunitetni saqlab turish.',
        'Maintaining immunity against diphtheria and tetanus.',
    ),

    # 16 лет (192 месяца)
    (
        192, 0, 'checkup',
        'Осмотр педиатра',
        'Pediatr ko‘rigi',
        'Pediatrician checkup',
        'Оценка физического и общего состояния здоровья подростка.',
        'O‘smirning jismoniy va umumiy sog‘liq holatini baholash.',
        'Assessment of the adolescent’s physical and general health.',
    ),
    (
        192, 5, 'checkup',
        'Осмотр невролога',
        'Nevrolog ko‘rigi',
        'Neurologist checkup',
        'Проверка нервной системы.',
        'Asab tizimini tekshirish.',
        'Nervous system checkup.',
    ),
    (
        192, 10, 'checkup',
        'Осмотр офтальмолога',
        'Oftalmolog ko‘rigi',
        'Ophthalmologist checkup',
        'Контроль зрения.',
        'Ko‘rish qobiliyatini nazorat qilish.',
        'Vision check.',
    ),

    # 17 лет (204 месяца)
    (
        204, 0, 'checkup',
        'Осмотр педиатра / терапевта',
        'Pediatr / terapevt ko‘rigi',
        'Pediatrician / General practitioner checkup',
        'Контроль состояния здоровья перед переходом во взрослую медицинскую систему.',
        'Kattalar tibbiy tizimiga o‘tishdan oldin sog‘liq holatini nazorat qilish.',
        'Health checkup before transitioning to the adult healthcare system.',
    ),

    # 18 лет (216 месяцев)
    (
        216, 0, 'checkup',
        'Итоговый медицинский осмотр',
        'Yakuniy tibbiy ko‘rik',
        'Final medical checkup',
        'Заключительный профилактический осмотр перед переходом во взрослую медицинскую систему наблюдения.',
        'Kattalar tibbiy kuzatuv tizimiga o‘tishdan oldingi yakuniy profilaktik ko‘rik.',
        'Final preventive checkup before transitioning to adult medical care.',
    ),
]
def generate_child_calendar_events(profile, birth_date: date):
    """
    Генерирует календарь прививок и осмотров для ребенка на основе даты рождения
    сразу с переводами (ru, uz, en).
    """
    if ChildCalendarEvent.objects.filter(profile=profile).exists():
        return

    today = date.today()
    events_to_create = []

    for (
        months, extra_days, event_type,
        title_ru, title_uz, title_en,
        desc_ru, desc_uz, desc_en
    ) in SCHEDULE_TEMPLATE:
        target_date = birth_date + relativedelta(months=months) + timedelta(days=extra_days)

        if target_date >= today:
            events_to_create.append(
                ChildCalendarEvent(
                    profile=profile,
                    event_type=event_type,
                    title=title_ru,
                    title_uz=title_uz,
                    title_en=title_en,
                    description=desc_ru,
                    description_uz=desc_uz,
                    description_en=desc_en,
                    scheduled_date=target_date,
                )
            )

    if events_to_create:
        ChildCalendarEvent.objects.bulk_create(events_to_create)