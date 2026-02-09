"""
أمر إدارة لإنشاء بيانات افتراضية واقعية للمشروع
Management command to generate realistic dummy data for the project
"""
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

# استيراد النماذج
from accounts.models import CustomUser, StudentProfile, SheikhProfile, Notification, ActivityLog
from quran.models import Surah, Ayah, Juz, Hizb, QuranPage
from halaqat.models import Course, Halaqa, HalaqaEnrollment, Session, Attendance
from courses.models import (
    Curriculum, CurriculumLesson, StudentCurriculum,
    MotivationalQuote, TafseerLesson, ScheduledNotification,
    QuoteNotification, LessonReminder
)
from recitation.models import (
    RecitationRecord, RecitationError, MemorizationProgress, DailyGoal
)
from gamification.models import (
    Badge, StudentBadge, PointsLog, Streak, Achievement,
    StudentAchievement, Leaderboard
)
from reports.models import CertificateTemplate, Certificate, StudentReport

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate realistic dummy data for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing data before generating new data',
        )
        parser.add_argument(
            '--students',
            type=int,
            default=50,
            help='Number of students to create (default: 50)',
        )
        parser.add_argument(
            '--sheikhs',
            type=int,
            default=8,
            help='Number of sheikhs to create (default: 8)',
        )

    def handle(self, *args, **options):
        reset = options['reset']
        num_students = options['students']
        num_sheikhs = options['sheikhs']

        if reset:
            self.stdout.write(self.style.WARNING('Deleting existing data...'))
            self.delete_existing_data()

        self.stdout.write(self.style.SUCCESS(f'Generating dummy data: {num_students} students, {num_sheikhs} sheikhs...'))

        with transaction.atomic():
            # 1. إنشاء بيانات القرآن
            self.create_quran_data()
            
            # 2. إنشاء المستخدمين
            admin = self.create_admin()
            sheikhs = self.create_sheikhs(num_sheikhs)
            students = self.create_students(num_students)
            parents = self.create_parents(students[:20])  # 20 parents
            
            # 3. إنشاء المسارات والحلقات
            courses = self.create_courses()
            halaqat = self.create_halaqat(courses, sheikhs)
            self.enroll_students_in_halaqat(students, halaqat)
            
            # 4. إنشاء المناهج والدروس
            curriculums = self.create_curriculums()
            self.create_curriculum_lessons(curriculums)
            self.enroll_students_in_curriculums(students, curriculums, sheikhs)
            
            # 5. إنشاء الجلسات والحضور
            sessions = self.create_sessions(halaqat)
            self.create_attendance(sessions)
            
            # 6. إنشاء سجلات التسميع والتقييم
            self.create_recitation_records(students, sessions)
            
            # 7. إنشاء بيانات Gamification
            self.create_badges()
            self.create_achievements()
            self.assign_badges_and_points(students)
            
            # 8. إنشاء الكلمات التحفيزية والتفسير
            self.create_motivational_quotes(admin)
            self.create_tafseer_lessons(admin)
            
            # 9. إنشاء قوالب الشهادات والشهادات
            self.create_certificate_templates()
            self.create_certificates(students)
            
            # 10. إنشاء التقارير
            self.create_student_reports(students)
            
            # 11. إنشاء سجلات النشاط
            self.create_activity_logs(students + sheikhs + [admin])

        self.stdout.write(self.style.SUCCESS('✓ Dummy data generated successfully!'))
        self.print_summary(num_students, num_sheikhs, len(parents))

    def delete_existing_data(self):
        """حذف البيانات الموجودة مع الاحتفاظ بالمستخدمين المشرفين"""
        models_to_delete = [
            ActivityLog, Notification, StudentReport, Certificate,
            CertificateTemplate, PointsLog, StudentBadge, StudentAchievement,
            Leaderboard, Streak, RecitationError, RecitationRecord,
            MemorizationProgress, DailyGoal, Attendance, Session,
            HalaqaEnrollment, ScheduledNotification, QuoteNotification,
            LessonReminder, StudentCurriculum, CurriculumLesson,
            TafseerLesson, MotivationalQuote, Curriculum,
            Halaqa, Course, StudentProfile, SheikhProfile,
            Badge, Achievement, Ayah, Surah, Juz, Hizb, QuranPage,
        ]
        
        for model in models_to_delete:
            try:
                model.objects.all().delete()
            except:
                pass
        
        # حذف جميع المستخدمين ما عدا المشرفين الأساسيين
        User.objects.filter(is_superuser=False).delete()

    def create_quran_data(self):
        """إنشاء بيانات القرآن الكريم - السور الأساسية"""
        if Surah.objects.exists():
            self.stdout.write('  ✓ Quran data already exists')
            return

        self.stdout.write('  Creating Quran data...')
        
        surahs_data = [
            (1, 'الفاتحة', 'Al-Fatiha', 7, 'meccan', 1, 1, 1, 1),
            (2, 'البقرة', 'Al-Baqarah', 286, 'medinan', 2, 2, 49, 1),
            (3, 'آل عمران', 'Aal-E-Imran', 200, 'medinan', 3, 50, 76, 3),
            (4, 'النساء', 'An-Nisa', 176, 'medinan', 4, 77, 106, 4),
            (5, 'المائدة', 'Al-Ma\'idah', 120, 'medinan', 5, 106, 127, 5),
            (6, 'الأنعام', 'Al-An\'am', 165, 'meccan', 6, 128, 150, 6),
            (7, 'الأعراف', 'Al-A\'raf', 206, 'meccan', 7, 151, 176, 7),
            (8, 'الأنفال', 'Al-Anfal', 75, 'medinan', 8, 177, 186, 8),
            (9, 'التوبة', 'At-Tawbah', 129, 'medinan', 9, 187, 207, 9),
            (10, 'يونس', 'Yunus', 109, 'meccan', 10, 208, 221, 10),
            (15, 'الحجر', 'Al-Hijr', 99, 'meccan', 54, 262, 267, 14),
            (18, 'الكهف', 'Al-Kahf', 110, 'meccan', 69, 293, 304, 15),
            (36, 'يس', 'Ya-Sin', 83, 'meccan', 41, 440, 445, 22),
            (55, 'الرحمن', 'Ar-Rahman', 78, 'medinan', 97, 531, 534, 27),
            (56, 'الواقعة', 'Al-Waqi\'a', 96, 'meccan', 46, 534, 542, 27),
            (67, 'الملك', 'Al-Mulk', 30, 'meccan', 77, 562, 564, 29),
            (78, 'النبأ', 'An-Naba', 40, 'meccan', 80, 582, 583, 30),
            (112, 'الإخلاص', 'Al-Ikhlas', 4, 'meccan', 22, 604, 604, 30),
            (113, 'الفلق', 'Al-Falaq', 5, 'meccan', 20, 604, 604, 30),
            (114, 'الناس', 'An-Nas', 6, 'meccan', 21, 604, 604, 30),
        ]
        
        surahs = []
        for data in surahs_data:
            surah = Surah.objects.create(
                number=data[0],
                name_arabic=data[1],
                name_english=data[2],
                name_transliteration=data[2],
                total_ayat=data[3],
                revelation_type=data[4],
                revelation_order=data[5],
                page_start=data[6],
                page_end=data[7],
                juz_start=data[8],
            )
            surahs.append(surah)
        
        # إنشاء بعض الآيات
        sample_ayahs = [
            (1, 1, 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', 1, 1, 1, 1),
            (1, 2, 'الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ', 2, 1, 1, 1),
            (1, 7, 'صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ', 7, 1, 1, 1),
            (2, 1, 'الم', 1, 1, 1, 1),
            (2, 255, 'اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ', 255, 3, 3, 11),
            (112, 1, 'قُلْ هُوَ اللَّهُ أَحَدٌ', 604, 30, 60, 4),
            (112, 2, 'اللَّهُ الصَّمَدُ', 604, 30, 60, 4),
        ]
        
        for surah_num, ayah_num, text, page, juz, hizb, quarter in sample_ayahs:
            try:
                surah = Surah.objects.get(number=surah_num)
                Ayah.objects.create(
                    surah=surah,
                    number=ayah_num,
                    number_in_quran=ayah_num,
                    text_uthmani=text,
                    text_simple=text,
                    page=page,
                    juz=juz,
                    hizb=hizb,
                    quarter=quarter,
                )
            except Surah.DoesNotExist:
                continue
        
        # إنشاء الأجزاء
        for i in range(1, 31):
            Juz.objects.create(
                number=i,
                name=f"الجزء {i}",
                start_surah=Surah.objects.first(),
                start_ayah=1,
                end_surah=Surah.objects.last(),
                end_ayah=1,
            )
        
        self.stdout.write(f'    Created {len(surahs)} surahs and {Ayah.objects.count()} ayahs')

    def create_admin(self):
        """إنشاء حساب المشرف"""
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'محمد',
                'last_name': 'المدير',
                'email': 'admin@qurancourses.org',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'phone': '+966501234567',
                'country': 'المملكة العربية السعودية',
                'city': 'الرياض',
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        return admin

    def create_sheikhs(self, count):
        """إنشاء حسابات المشايخ"""
        self.stdout.write(f'  Creating {count} sheikhs...')
        
        sheikh_names = [
            ('أحمد', 'القرني', 'hifz'),
            ('محمد', 'العتيبي', 'tajweed'),
            ('عبدالله', 'الحصين', 'qiraat'),
            ('سعد', 'الشثري', 'ijazah'),
            ('خالد', 'المغربي', 'hifz'),
            ('فهد', 'السديري', 'tajweed'),
            ('إبراهيم', 'الأخضر', 'hifz'),
            ('يوسف', 'الدوسري', 'qiraat'),
        ]
        
        sheikhs = []
        for i in range(min(count, len(sheikh_names))):
            first, last, spec = sheikh_names[i]
            username = f"sheikh_{first.lower()}"
            
            sheikh, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@qurancourses.org',
                    'user_type': 'sheikh',
                    'gender': 'male',
                    'phone': f'+96650{random.randint(1000000, 9999999)}',
                    'country': 'المملكة العربية السعودية',
                    'city': random.choice(['الرياض', 'جدة', 'الدمام', 'مكة']),
                    'bio': f"شيخ متخصص في {spec} مع خبرة {random.randint(5, 20)} عاماً",
                }
            )
            if created:
                sheikh.set_password('sheikh123')
                sheikh.save()
                
                # إنشاء ملف الشيخ
                SheikhProfile.objects.create(
                    user=sheikh,
                    specialization=spec,
                    ijazah_info=f"إجازة في {spec} برواية حفص عن عاصم",
                    years_of_experience=random.randint(5, 20),
                    max_students=random.randint(10, 30),
                    available_days='sun,tue,thu',
                    available_times='16:00-20:00',
                    hourly_rate=random.choice([100, 150, 200, 250]),
                    rating=Decimal(str(random.uniform(4.0, 5.0))).quantize(Decimal('0.01')),
                )
            sheikhs.append(sheikh)
        
        return sheikhs

    def create_students(self, count):
        """إنشاء حسابات الطلاب"""
        self.stdout.write(f'  Creating {count} students...')
        
        first_names_male = [
            'محمد', 'أحمد', 'عبدالله', 'عمر', 'علي', 'يوسف', 'إبراهيم', 'خالد',
            'سعد', 'فهد', 'ناصر', 'سلطان', 'ماجد', 'فيصل', 'بندر', 'تركي',
            'عبدالرحمن', 'مشاري', 'فواز', 'عبدالعزيز', 'صالح', 'مبارك', 'نايف',
        ]
        first_names_female = [
            'فاطمة', 'عائشة', 'خديجة', 'مريم', 'نورة', 'سارة', 'هند', 'ليلى',
            'رنا', 'ريم', 'جود', 'جوري', 'شيخة', 'موضي', 'عبير', 'أمل',
            'هيا', 'دانا', 'لجين', 'رهف', 'غدير', 'أريج', 'فرح',
        ]
        last_names = [
            'الحارثي', 'الغامدي', 'الشهري', 'القحطاني', 'العتيبي', 'الدويس',
            'الزهراني', 'البلوي', 'المالكي', 'الشمري', 'الحربي', 'السهلي',
            'العنزي', 'المطيري', 'الرشيدي', 'الخالدي', 'العبيدي', 'السعدي',
            'الحربي', 'المقبل', 'الصاعدي', 'الدهمش', 'العجمي', 'الفهد',
        ]
        cities = ['الرياض', 'جدة', 'الدمام', 'مكة', 'المدينة المنورة', 'أبها', 'تبوك', 'بريدة']
        
        students = []
        for i in range(count):
            gender = random.choice(['male', 'female'])
            if gender == 'male':
                first = random.choice(first_names_male)
            else:
                first = random.choice(first_names_female)
            
            last = random.choice(last_names)
            username = f"student_{first.lower()}_{i+1}"
            
            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@student.qurancourses.org',
                    'user_type': 'student',
                    'gender': gender,
                    'phone': f'+9665{random.randint(0, 9)}{random.randint(1000000, 9999999)}',
                    'country': 'المملكة العربية السعودية',
                    'city': random.choice(cities),
                    'date_of_birth': date(
                        random.randint(1990, 2015),
                        random.randint(1, 12),
                        random.randint(1, 28)
                    ),
                    'bio': f"طالب طموح يسعى لحفظ كتاب الله",
                }
            )
            if created:
                student.set_password('student123')
                student.save()
                
                # إنشاء ملف الطالب
                current_surah = random.randint(1, 30)
                StudentProfile.objects.create(
                    user=student,
                    current_surah=current_surah,
                    current_ayah=random.randint(1, 20),
                    total_memorized_pages=random.randint(5, 200),
                    total_memorized_juz=random.randint(0, 10),
                    memorization_start_date=date(
                        random.randint(2020, 2023),
                        random.randint(1, 12),
                        random.randint(1, 28)
                    ),
                    notes=random.choice([
                        'يتقدم بخطى ثابتة',
                        'يحتاج إلى مزيد من المراجعة',
                        'متميز في التجويد',
                        'يلتزم بالحضور دائماً',
                        '',
                    ]),
                    total_points=random.randint(0, 5000),
                )
            students.append(student)
        
        return students

    def create_parents(self, students_with_parents):
        """إنشاء حسابات أولياء الأمور"""
        self.stdout.write(f'  Creating parents for {len(students_with_parents)} students...')
        
        parents = []
        for i, student in enumerate(students_with_parents):
            username = f"parent_{i+1}"
            
            parent, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': random.choice(['عبدالله', 'أحمد', 'خالد', 'سعد']),
                    'last_name': student.last_name,
                    'email': f'{username}@qurancourses.org',
                    'user_type': 'parent',
                    'gender': 'male',
                    'phone': f'+9665{random.randint(0, 9)}{random.randint(1000000, 9999999)}',
                    'country': 'المملكة العربية السعودية',
                    'city': student.city,
                }
            )
            if created:
                parent.set_password('parent123')
                parent.save()
                
                # ربط الطالب بولي الأمر
                profile = student.student_profile
                profile.parent = parent
                profile.save()
            
            parents.append(parent)
        
        return parents

    def create_courses(self):
        """إنشاء المسارات"""
        self.stdout.write('  Creating courses...')
        
        courses_data = [
            ('حفظ القرآن الكريم - المستوى الأول', 'hifz', 12, 0),
            ('حفظ القرآن الكريم - المستوى المتقدم', 'hifz', 24, 500),
            ('تجويد القرآن الكريم', 'tajweed', 6, 300),
            ('مراجعة الحفظ المتون', 'muraja', 6, 0),
            ('تلاوة القرآن الكريم', 'tilawa', 3, 200),
            ('برنامج الإجازة', 'ijazah', 36, 1000),
        ]
        
        courses = []
        for name, course_type, duration, price in courses_data:
            course, created = Course.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"برنامج {name} لتعلم القرآن الكريم",
                    'course_type': course_type,
                    'duration_months': duration,
                    'price': price,
                }
            )
            courses.append(course)
        
        return courses

    def create_halaqat(self, courses, sheikhs):
        """إنشاء الحلقات"""
        self.stdout.write('  Creating halaqat...')
        
        halaqat_data = [
            ('حلقة حفظ الفاتحة والبقرة', courses[0], 'sat,sun,mon', '16:00'),
            ('حلقة حفظ آل عمران والنساء', courses[0], 'tue,wed,thu', '17:00'),
            ('حلقة التجويد الأساسي', courses[2], 'sat,mon,wed', '18:00'),
            ('حلقة المراجعة المتقدمة', courses[3], 'sun,tue,thu', '19:00'),
            ('حلقة الإجازة - الشيخ أحمد', courses[5], 'sat,sun', '20:00'),
            ('حلقة التلاوة المنتظمة', courses[4], 'fri', '14:00'),
            ('حلقة حفظ المستوى الثاني', courses[1], 'sun,tue,thu', '16:30'),
            ('حلقة تجويد متقدم', courses[2], 'mon,wed', '19:00'),
        ]
        
        halaqat = []
        for i, (name, course, days, time) in enumerate(halaqat_data):
            sheikh = sheikhs[i % len(sheikhs)]
            halaqa, created = Halaqa.objects.get_or_create(
                name=name,
                defaults={
                    'course': course,
                    'sheikh': sheikh,
                    'description': f"{name} مع الشيخ {sheikh.get_full_name()}",
                    'max_students': random.randint(8, 15),
                    'schedule_days': days,
                    'schedule_time': time,
                    'duration_minutes': random.choice([30, 45, 60]),
                    'status': 'active',
                }
            )
            halaqat.append(halaqa)
        
        return halaqat

    def enroll_students_in_halaqat(self, students, halaqat):
        """تسجيل الطلاب في الحلقات"""
        self.stdout.write('  Enrolling students in halaqat...')
        
        for student in students:
            # تسجيل الطالب في 1-3 حلقات
            num_enrollments = random.randint(1, min(3, len(halaqat)))
            selected_halaqat = random.sample(halaqat, num_enrollments)
            
            for halaqa in selected_halaqat:
                HalaqaEnrollment.objects.get_or_create(
                    student=student,
                    halaqa=halaqa,
                    defaults={
                        'status': random.choice(['active', 'active', 'active', 'completed']),
                        'notes': random.choice(['', '', '', 'ملتزم جداً', 'يحتاج متابعة']),
                    }
                )

    def create_curriculums(self):
        """إنشاء المناهج"""
        self.stdout.write('  Creating curriculums...')
        
        curriculums_data = [
            ('منهج حفظ الجزء الأول', 'hifz', 1, 1, 1, 1, 12, 2, 60),
            ('منهج حفظ الجزء الثاني', 'hifz', 2, 2, 1, 1, 12, 2, 60),
            ('منهج حفظ الجزء الثالث', 'hifz', 3, 3, 1, 1, 12, 2, 60),
            ('منهج تجويد شامل', 'tajweed', 1, 30, 1, 30, 24, 2, 45),
            ('منهج تفسير الجزء الأول', 'tafseer', 1, 1, 1, 1, 24, 1, 90),
            ('منهج شامل لختم القرآن', 'comprehensive', 1, 30, 1, 30, 104, 3, 60),
        ]
        
        curriculums = []
        for name, ctype, juz_from, juz_to, surah_from, surah_to, weeks, lessons_per_week, minutes in curriculums_data:
            surah_from_obj = Surah.objects.filter(number=surah_from).first()
            surah_to_obj = Surah.objects.filter(number=surah_to).first()
            
            curriculum, created = Curriculum.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"{name} - برنامج منظم لحفظ القرآن",
                    'curriculum_type': ctype,
                    'target_surah_from': surah_from_obj,
                    'target_surah_to': surah_to_obj,
                    'target_juz_from': juz_from,
                    'target_juz_to': juz_to,
                    'duration_weeks': weeks,
                    'lessons_per_week': lessons_per_week,
                    'minutes_per_lesson': minutes,
                }
            )
            curriculums.append(curriculum)
        
        return curriculums

    def create_curriculum_lessons(self, curriculums):
        """إنشاء دروس المناهج"""
        self.stdout.write('  Creating curriculum lessons...')
        
        for curriculum in curriculums:
            total_lessons = curriculum.total_lessons
            
            for i in range(1, total_lessons + 1):
                lesson_type = random.choice(['hifz', 'muraja', 'tajweed', 'test'])
                if i % 4 == 0:
                    lesson_type = 'test'
                
                surah = Surah.objects.filter(number=random.randint(1, 20)).first()
                
                CurriculumLesson.objects.get_or_create(
                    curriculum=curriculum,
                    lesson_number=i,
                    defaults={
                        'title': f"الدرس {i}: {random.choice(['حفظ صفحتين', 'مراجعة', 'قواعد التجويد', 'اختبار'])}",
                        'description': f"درس رقم {i} من {curriculum.name}",
                        'lesson_type': lesson_type,
                        'surah_from': surah,
                        'ayah_from': random.randint(1, 10),
                        'surah_to': surah,
                        'ayah_to': random.randint(11, 20),
                        'duration_minutes': curriculum.minutes_per_lesson,
                    }
                )

    def enroll_students_in_curriculums(self, students, curriculums, sheikhs):
        """تسجيل الطلاب في المناهج"""
        self.stdout.write('  Enrolling students in curriculums...')
        
        statuses = ['not_started', 'in_progress', 'in_progress', 'in_progress', 'completed', 'on_hold']
        
        for student in students:
            # تسجيل في 1-2 منهج
            num_curriculums = random.randint(1, min(2, len(curriculums)))
            selected_curriculums = random.sample(curriculums, num_curriculums)
            
            for curriculum in selected_curriculums:
                sheikh = random.choice(sheikhs)
                status = random.choice(statuses)
                
                student_curriculum, created = StudentCurriculum.objects.get_or_create(
                    student=student,
                    curriculum=curriculum,
                    defaults={
                        'sheikh': sheikh,
                        'status': status,
                        'start_date': date(2024, random.randint(1, 6), random.randint(1, 28)),
                        'expected_end_date': date(2025, random.randint(1, 6), random.randint(1, 28)),
                        'enable_reminders': random.choice([True, False]),
                    }
                )

    def create_sessions(self, halaqat):
        """إنشاء الجلسات"""
        self.stdout.write('  Creating sessions...')
        
        sessions = []
        today = date.today()
        
        for halaqa in halaqat:
            # إنشاء جلسات للشهرين الماضيين والقادم
            for i in range(-30, 30):
                session_date = today + timedelta(days=i)
                
                # تخطي بعض الأيام عشوائياً
                if random.random() < 0.3:
                    continue
                
                status = 'completed' if i < 0 else ('scheduled' if i > 0 else 'in_progress')
                
                # حساب وقت الانتهاء
                if halaqa.schedule_time:
                    if isinstance(halaqa.schedule_time, str):
                        schedule_time = datetime.strptime(halaqa.schedule_time, '%H:%M').time()
                    else:
                        schedule_time = halaqa.schedule_time
                    start_dt = datetime.combine(date.today(), schedule_time)
                    end_time = (start_dt + timedelta(minutes=halaqa.duration_minutes)).time()
                else:
                    end_time = datetime.strptime('17:00', '%H:%M').time()
                
                # تحويل schedule_time لكائن time إذا كان نص
                if halaqa.schedule_time and isinstance(halaqa.schedule_time, str):
                    start_time = datetime.strptime(halaqa.schedule_time, '%H:%M').time()
                elif halaqa.schedule_time:
                    start_time = halaqa.schedule_time
                else:
                    start_time = datetime.strptime('16:00', '%H:%M').time()
                
                session, created = Session.objects.get_or_create(
                    halaqa=halaqa,
                    date=session_date,
                    defaults={
                        'start_time': start_time,
                        'end_time': end_time,
                        'status': status,
                        'meet_link': f"https://meet.google.com/abc-{random.randint(100, 999)}",
                        'notes': random.choice(['', '', '', 'جلسة ممتازة', 'تمت المراجعة']),
                    }
                )
                sessions.append(session)
        
        return sessions

    def create_attendance(self, sessions):
        """إنشاء سجلات الحضور"""
        self.stdout.write('  Creating attendance records...')
        
        for session in sessions:
            if session.status != 'completed':
                continue
            
            # الحصول على الطلاب المسجلين في الحلقة
            enrollments = HalaqaEnrollment.objects.filter(
                halaqa=session.halaqa,
                status='active'
            )
            
            for enrollment in enrollments:
                status = random.choices(
                    ['present', 'present', 'present', 'present', 'absent', 'excused', 'late'],
                    weights=[50, 20, 15, 10, 3, 1, 1]
                )[0]
                
                Attendance.objects.get_or_create(
                    student=enrollment.student,
                    session=session,
                    defaults={
                        'status': status,
                        'check_in_time': timezone.make_aware(datetime.combine(session.date, session.start_time)) if status == 'present' else None,
                        'notes': random.choice(['', '', '', '', 'حاضر بانتظام']),
                    }
                )

    def create_recitation_records(self, students, sessions):
        """إنشاء سجلات التسميع"""
        self.stdout.write('  Creating recitation records...')
        
        recitation_types = ['new', 'new', 'review', 'review', 'tilawa']
        
        completed_sessions = [s for s in sessions if s.status == 'completed']
        
        for student in students[:30]:  # للـ 30 طالباً الأولين
            # إنشاء 10-30 سجل تسميع لكل طالب
            num_records = random.randint(10, 30)
            
            for _ in range(num_records):
                session = random.choice(completed_sessions)
                surah = Surah.objects.filter(number=random.randint(1, 20)).first()
                
                if not surah:
                    continue
                
                grade = Decimal(str(random.uniform(60, 100))).quantize(Decimal('0.1'))
                recitation_type = random.choice(recitation_types)
                
                # حساب نطاق الآيات المناسب
                ayah_start = random.randint(1, min(5, surah.total_ayat))
                ayah_end = random.randint(min(ayah_start + 1, surah.total_ayat), min(surah.total_ayat, ayah_start + 10))
                
                record, created = RecitationRecord.objects.get_or_create(
                    student=student,
                    session=session,
                    defaults={
                        'surah_start': surah,
                        'ayah_start': ayah_start,
                        'surah_end': surah,
                        'ayah_end': ayah_end,
                        'recitation_type': recitation_type,
                        'grade': grade,
                        'total_errors': random.randint(0, 5),
                        'duration_minutes': random.randint(10, 30),
                        'notes': random.choice(['', '', 'أداء جيد', 'يحتاج مراجعة']),
                        'sheikh_feedback': random.choice(['', 'ممتاز', 'أحسنت']),
                    }
                )
                
                # إنشاء أخطاء للتسميع
                if record.total_errors > 0:
                    for _ in range(record.total_errors):
                        RecitationError.objects.create(
                            record=record,
                            surah=surah,
                            ayah=random.randint(1, surah.total_ayat),
                            error_type=random.choice(['tajweed', 'tashkeel', 'forget', 'pronunciation']),
                            severity=random.choice(['minor', 'minor', 'minor', 'major']),
                        )

    def create_badges(self):
        """إنشاء الأوسمة"""
        self.stdout.write('  Creating badges...')
        
        badges_data = [
            ('حافظ سورة الفاتحة', 'memorization', 'bronze', 100, 'fa-star'),
            ('حافظ الجزء الأول', 'memorization', 'silver', 500, 'fa-book'),
            ('حافظ خمسة أجزاء', 'memorization', 'gold', 1000, 'fa-book-open'),
            ('حافظ عشرة أجزاء', 'memorization', 'platinum', 2000, 'fa-quran'),
            ('حافظ القرآن الكريم', 'memorization', 'diamond', 5000, 'fa-crown'),
            ('الحاضر المنتظم', 'attendance', 'silver', 300, 'fa-calendar-check'),
            ('مثالي الحضور', 'attendance', 'gold', 1000, 'fa-award'),
            ('المجتهد', 'achievement', 'bronze', 200, 'fa-medal'),
            ('المتميز', 'achievement', 'gold', 1500, 'fa-trophy'),
            ('مواظب 7 أيام', 'streak', 'bronze', 100, 'fa-fire'),
            ('مواظب 30 يوماً', 'streak', 'silver', 500, 'fa-fire-alt'),
            ('مواظب 100 يوم', 'streak', 'gold', 1500, 'fa-burn'),
        ]
        
        for name, badge_type, level, points, icon in badges_data:
            Badge.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"حصل على وسام {name}",
                    'icon': icon,
                    'badge_type': badge_type,
                    'level': level,
                    'points_reward': points,
                    'criteria_type': badge_type,
                    'criteria_value': random.randint(1, 100),
                }
            )

    def create_achievements(self):
        """إنشاء الإنجازات"""
        self.stdout.write('  Creating achievements...')
        
        achievements_data = [
            ('إتمام أول سورة', 'surah_complete', 1, 100),
            ('إتمام 5 سور', 'surah_complete', 5, 300),
            ('إتمام 10 سور', 'surah_complete', 10, 600),
            ('إتمام الجزء الأول', 'juz_complete', 1, 500),
            ('إتمام 5 أجزاء', 'juz_complete', 5, 2000),
            ('إتمام 10 أجزاء', 'juz_complete', 10, 5000),
            ('ختم القرآن الكريم', 'hifz_complete', 1, 10000),
            ('50 جلسة تسميع', 'sessions_count', 50, 1000),
            ('100 جلسة تسميع', 'sessions_count', 100, 2500),
            ('درجة كاملة 100', 'perfect_grade', 1, 500),
            ('7 أيام مواظبة', 'streak_days', 7, 200),
            ('30 يوم مواظبة', 'streak_days', 30, 1000),
        ]
        
        for name, achievement_type, target, points in achievements_data:
            Achievement.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"أكمل إنجاز: {name}",
                    'achievement_type': achievement_type,
                    'icon': 'fa-trophy',
                    'points_reward': points,
                    'target_value': target,
                }
            )

    def assign_badges_and_points(self, students):
        """منح الأوسمة والنقاط للطلاب"""
        self.stdout.write('  Assigning badges and points...')
        
        badges = list(Badge.objects.all())
        achievements = list(Achievement.objects.all())
        
        for student in students:
            # منح 0-5 أوسمة عشوائية
            num_badges = random.randint(0, min(5, len(badges)))
            selected_badges = random.sample(badges, num_badges) if badges else []
            
            for badge in selected_badges:
                StudentBadge.objects.get_or_create(
                    student=student,
                    badge=badge,
                    defaults={
                        'notes': 'حصل عليه بجدارة',
                    }
                )
                
                # إضافة سجل النقاط
                PointsLog.objects.create(
                    student=student,
                    points=badge.points_reward,
                    points_type='badge',
                    reason=f'حصول على وسام: {badge.name}',
                )
            
            # منح إنجازات
            num_achievements = random.randint(0, min(3, len(achievements)))
            selected_achievements = random.sample(achievements, num_achievements) if achievements else []
            
            for achievement in selected_achievements:
                StudentAchievement.objects.get_or_create(
                    student=student,
                    achievement=achievement,
                    defaults={
                        'progress': random.randint(1, achievement.target_value),
                        'is_completed': random.choice([True, False]),
                    }
                )
            
            # إنشاء/تحديث سجل المواظبة
            Streak.objects.get_or_create(
                student=student,
                defaults={
                    'current_streak': random.randint(0, 30),
                    'longest_streak': random.randint(7, 100),
                    'last_activity_date': date.today() - timedelta(days=random.randint(0, 2)),
                    'total_active_days': random.randint(10, 200),
                }
            )
            
            # إضافة نقاط من التسميع والحضور
            for _ in range(random.randint(5, 15)):
                PointsLog.objects.create(
                    student=student,
                    points=random.randint(10, 100),
                    points_type=random.choice(['recitation', 'attendance', 'achievement']),
                    reason=random.choice([
                        'تسميع ممتاز',
                        'حضور الجلسة',
                        'إنجاز الدرس',
                        'المراجعة اليومية',
                    ]),
                )

    def create_motivational_quotes(self, admin):
        """إنشاء الكلمات التحفيزية"""
        self.stdout.write('  Creating motivational quotes...')
        
        quotes_data = [
            ('العلم نور', 'قال تعالى: "وَقُل رَّبِّ زِدْنِي عِلْمًا"', 'general', 'الله سبحانه وتعالى', 'سورة طه'),
            ('بركة الوقت', 'اغتنم خمساً قبل خمس: شبابك قبل هرمك', 'general', 'النبي ﷺ', 'حسنه الألباني'),
            ('صباح الخير', 'أصبحنا وأصبح الملك لله', 'morning', '', 'أذكار الصباح'),
            ('تذكير مسائي', 'بسم الله الذي لا يضر مع اسمه شيء', 'evening', '', 'أذكار المساء'),
            ('يوم الجمعة', 'خير يوم طلعت عليه الشمس يوم الجمعة', 'friday', 'النبي ﷺ', 'صحيح مسلم'),
            ('إنجاز اليوم', 'كنت أقرأ القرآن فيقول لي خذني على مهل', 'achievement', 'عبدالله بن عمر', 'رواه البخاري'),
            ('التشجيع', 'اقرؤوا القرآن ولا تأكلوا به', 'encouragement', 'النبي ﷺ', 'صحيح مسلم'),
        ]
        
        for title, content, category, author, source in quotes_data:
            MotivationalQuote.objects.get_or_create(
                title=title,
                defaults={
                    'content': content,
                    'category': category,
                    'author': author,
                    'source': source,
                    'is_published': True,
                    'published_at': timezone.now(),
                    'created_by': admin,
                }
            )

    def create_tafseer_lessons(self, admin):
        """إنشاء دروس التفسير"""
        self.stdout.write('  Creating tafseer lessons...')
        
        surahs_for_tafseer = Surah.objects.filter(number__in=[1, 2, 36, 67])[:4]
        
        for surah in surahs_for_tafseer:
            TafseerLesson.objects.get_or_create(
                surah=surah,
                ayah_from=1,
                ayah_to=min(10, surah.total_ayat),
                defaults={
                    'title': f"تفسير {surah.name_arabic} (1-{min(10, surah.total_ayat)})",
                    'content': f"درس تفسير لسورة {surah.name_arabic} يشرح الآيات الأولى...",
                    'summary': f"ملخص درس سورة {surah.name_arabic}",
                    'is_published': True,
                    'published_at': timezone.now(),
                    'created_by': admin,
                }
            )

    def create_certificate_templates(self):
        """إنشاء قوالب الشهادات"""
        self.stdout.write('  Creating certificate templates...')
        
        templates_data = [
            ('قالب شهادة إتمام السورة', 'template_1.jpg'),
            ('قالب شهادة إتمام الجزء', 'template_2.jpg'),
            ('قالب شهادة ختم القرآن', 'template_3.jpg'),
            ('قالب شهادة التقدم', 'template_4.jpg'),
        ]
        
        # Note: Images won't exist, but we'll create the records
        for name, image_name in templates_data:
            CertificateTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'description': f"{name} - قالب رسمي",
                    'name_font_size': random.randint(36, 60),
                    'name_font_color': '#000000',
                    'name_position_x': 540,
                    'name_position_y': random.randint(350, 450),
                    'degree_font_size': random.randint(28, 40),
                    'degree_font_color': '#333333',
                    'degree_position_x': 540,
                    'degree_position_y': random.randint(480, 550),
                    'date_font_size': 24,
                    'date_font_color': '#666666',
                    'date_position_x': 540,
                    'date_position_y': 600,
                    'default_title': name.replace('قالب ', ''),
                    'default_description': 'تم منح هذه الشهادة تقديراً للجهد المبذول',
                }
            )

    def create_certificates(self, students):
        """إنشاء الشهادات"""
        self.stdout.write('  Creating certificates...')
        
        templates = list(CertificateTemplate.objects.all())
        if not templates:
            return
        
        for student in students[:20]:  # للـ 20 طالباً الأولين
            template = random.choice(templates)
            
            Certificate.objects.get_or_create(
                student=student,
                template=template,
                defaults={
                    'degree_title': random.choice([
                        'إتمام سورة الفاتحة',
                        'إتمام الجزء الأول',
                        'التقدم المتميز',
                        'حفظ خمس سور',
                    ]),
                    'degree_description': 'بعد اجتياز المتطلبات بنجاح',
                    'issue_date': date(2024, random.randint(1, 12), random.randint(1, 28)),
                    'status': 'issued',
                }
            )

    def create_student_reports(self, students):
        """إنشاء تقارير الطلاب"""
        self.stdout.write('  Creating student reports...')
        
        for student in students[:15]:  # للـ 15 طالباً الأولين
            # إنشاء 1-3 تقارير لكل طالب
            for i in range(random.randint(1, 3)):
                start_date = date(2024, random.randint(1, 10), 1)
                end_date = start_date + timedelta(days=30)
                
                StudentReport.objects.create(
                    student=student,
                    report_period=random.choice(['weekly', 'monthly', 'quarterly']),
                    start_date=start_date,
                    end_date=end_date,
                    total_sessions=random.randint(4, 20),
                    total_recitations=random.randint(4, 20),
                    total_pages_memorized=random.randint(1, 10),
                    total_pages_reviewed=random.randint(5, 30),
                    average_grade=Decimal(str(random.uniform(70, 98))).quantize(Decimal('0.1')),
                    attendance_rate=Decimal(str(random.uniform(80, 100))).quantize(Decimal('0.1')),
                    total_errors=random.randint(0, 20),
                    tajweed_errors=random.randint(0, 10),
                    memorization_errors=random.randint(0, 10),
                    general_evaluation=random.choice([
                        'يتقدم بشكل جيد',
                        'متميز في الحفظ',
                        'يحتاج إلى مزيد من المراجعة',
                        'ملتزم ومجتهد',
                    ]),
                    recommendations=random.choice([
                        'الاستمرار في المراجعة اليومية',
                        'زيادة ورد الحفظ',
                        'مراجعة قواعد التجويد',
                        'الحفاظ على المواظبة',
                    ]),
                )

    def create_activity_logs(self, users):
        """إنشاء سجلات النشاط"""
        self.stdout.write('  Creating activity logs...')
        
        actions = [
            'تسجيل الدخول',
            'قراءة سورة',
            'تسجيل تسميع',
            'حضور جلسة',
            'مراجعة يومية',
            'تحديث الملف الشخصي',
            'مشاهدة درس',
        ]
        
        for user in users[:30]:  # للـ 30 مستخدماً
            for _ in range(random.randint(5, 15)):
                ActivityLog.objects.create(
                    user=user,
                    action=random.choice(actions),
                    details=random.choice(['', 'تم بنجاح', 'عبر الموقع', 'عبر التطبيق']),
                    ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                )

    def print_summary(self, num_students, num_sheikhs, num_parents):
        """طباعة ملخص البيانات"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📊 ملخص البيانات المُنشأة:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        summary = {
            'المستخدمون': User.objects.count(),
            '  - المشرفون': User.objects.filter(user_type='admin').count(),
            '  - المشايخ': User.objects.filter(user_type='sheikh').count(),
            '  - الطلاب': User.objects.filter(user_type='student').count(),
            '  - أولياء الأمور': User.objects.filter(user_type='parent').count(),
            'السور': Surah.objects.count(),
            'الآيات': Ayah.objects.count(),
            'المسارات': Course.objects.count(),
            'الحلقات': Halaqa.objects.count(),
            'تسجيلات الحلقات': HalaqaEnrollment.objects.count(),
            'الجلسات': Session.objects.count(),
            'سجلات الحضور': Attendance.objects.count(),
            'المناهج': Curriculum.objects.count(),
            'دروس المناهج': CurriculumLesson.objects.count(),
            'تسجيلات المناهج': StudentCurriculum.objects.count(),
            'سجلات التسميع': RecitationRecord.objects.count(),
            'أخطاء التسميع': RecitationError.objects.count(),
            'الأوسمة': Badge.objects.count(),
            'أوسمة الطلاب': StudentBadge.objects.count(),
            'الإنجازات': Achievement.objects.count(),
            'إنجازات الطلاب': StudentAchievement.objects.count(),
            'سجلات النقاط': PointsLog.objects.count(),
            'سجلات المواظبة': Streak.objects.count(),
            'الكلمات التحفيزية': MotivationalQuote.objects.count(),
            'دروس التفسير': TafseerLesson.objects.count(),
            'قوالب الشهادات': CertificateTemplate.objects.count(),
            'الشهادات': Certificate.objects.count(),
            'التقارير': StudentReport.objects.count(),
            'سجلات النشاط': ActivityLog.objects.count(),
        }
        
        for key, value in summary.items():
            self.stdout.write(f'  {key}: {value}')
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('🔑 بيانات تسجيل الدخول:'))
        self.stdout.write(self.style.SUCCESS('  المشرف: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('  الشيوخ: sheikh_ahmad / sheikh123'))
        self.stdout.write(self.style.SUCCESS('  الطلاب: student_محمد_1 / student123'))
        self.stdout.write(self.style.SUCCESS('  أولياء الأمور: parent_1 / parent123'))
        self.stdout.write(self.style.SUCCESS('='*60))
