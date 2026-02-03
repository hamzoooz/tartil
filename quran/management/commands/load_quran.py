"""
أمر تحميل بيانات القرآن الكريم
Load Quran Data Command
"""
from django.core.management.base import BaseCommand
from quran.models import Surah, Ayah, Juz, QuranPage

# بيانات السور (114 سورة)
SURAHS_DATA = [
    # (رقم, اسم عربي, اسم إنجليزي, عدد الآيات, نوع النزول, صفحة البداية, صفحة النهاية, الجزء)
    (1, "الفاتحة", "Al-Fatiha", 7, "meccan", 1, 1, 1),
    (2, "البقرة", "Al-Baqarah", 286, "medinan", 2, 49, 1),
    (3, "آل عمران", "Aal-E-Imran", 200, "medinan", 50, 76, 3),
    (4, "النساء", "An-Nisa", 176, "medinan", 77, 106, 4),
    (5, "المائدة", "Al-Ma'idah", 120, "medinan", 106, 127, 6),
    (6, "الأنعام", "Al-An'am", 165, "meccan", 128, 150, 7),
    (7, "الأعراف", "Al-A'raf", 206, "meccan", 151, 176, 8),
    (8, "الأنفال", "Al-Anfal", 75, "medinan", 177, 186, 9),
    (9, "التوبة", "At-Tawbah", 129, "medinan", 187, 207, 10),
    (10, "يونس", "Yunus", 109, "meccan", 208, 221, 11),
    (11, "هود", "Hud", 123, "meccan", 221, 235, 11),
    (12, "يوسف", "Yusuf", 111, "meccan", 235, 248, 12),
    (13, "الرعد", "Ar-Ra'd", 43, "medinan", 249, 255, 13),
    (14, "إبراهيم", "Ibrahim", 52, "meccan", 255, 261, 13),
    (15, "الحجر", "Al-Hijr", 99, "meccan", 262, 267, 14),
    (16, "النحل", "An-Nahl", 128, "meccan", 267, 281, 14),
    (17, "الإسراء", "Al-Isra", 111, "meccan", 282, 293, 15),
    (18, "الكهف", "Al-Kahf", 110, "meccan", 293, 304, 15),
    (19, "مريم", "Maryam", 98, "meccan", 305, 312, 16),
    (20, "طه", "Ta-Ha", 135, "meccan", 312, 321, 16),
    (21, "الأنبياء", "Al-Anbiya", 112, "meccan", 322, 331, 17),
    (22, "الحج", "Al-Hajj", 78, "medinan", 332, 341, 17),
    (23, "المؤمنون", "Al-Mu'minun", 118, "meccan", 342, 349, 18),
    (24, "النور", "An-Nur", 64, "medinan", 350, 359, 18),
    (25, "الفرقان", "Al-Furqan", 77, "meccan", 359, 366, 18),
    (26, "الشعراء", "Ash-Shu'ara", 227, "meccan", 367, 376, 19),
    (27, "النمل", "An-Naml", 93, "meccan", 377, 385, 19),
    (28, "القصص", "Al-Qasas", 88, "meccan", 385, 396, 20),
    (29, "العنكبوت", "Al-Ankabut", 69, "meccan", 396, 404, 20),
    (30, "الروم", "Ar-Rum", 60, "meccan", 404, 410, 21),
    (31, "لقمان", "Luqman", 34, "meccan", 411, 414, 21),
    (32, "السجدة", "As-Sajdah", 30, "meccan", 415, 417, 21),
    (33, "الأحزاب", "Al-Ahzab", 73, "medinan", 418, 427, 21),
    (34, "سبأ", "Saba", 54, "meccan", 428, 434, 22),
    (35, "فاطر", "Fatir", 45, "meccan", 434, 440, 22),
    (36, "يس", "Ya-Sin", 83, "meccan", 440, 445, 22),
    (37, "الصافات", "As-Saffat", 182, "meccan", 446, 452, 23),
    (38, "ص", "Sad", 88, "meccan", 453, 458, 23),
    (39, "الزمر", "Az-Zumar", 75, "meccan", 458, 467, 23),
    (40, "غافر", "Ghafir", 85, "meccan", 467, 476, 24),
    (41, "فصلت", "Fussilat", 54, "meccan", 477, 482, 24),
    (42, "الشورى", "Ash-Shura", 53, "meccan", 483, 489, 25),
    (43, "الزخرف", "Az-Zukhruf", 89, "meccan", 489, 495, 25),
    (44, "الدخان", "Ad-Dukhan", 59, "meccan", 496, 498, 25),
    (45, "الجاثية", "Al-Jathiya", 37, "meccan", 499, 502, 25),
    (46, "الأحقاف", "Al-Ahqaf", 35, "meccan", 502, 506, 26),
    (47, "محمد", "Muhammad", 38, "medinan", 507, 510, 26),
    (48, "الفتح", "Al-Fath", 29, "medinan", 511, 515, 26),
    (49, "الحجرات", "Al-Hujurat", 18, "medinan", 515, 517, 26),
    (50, "ق", "Qaf", 45, "meccan", 518, 520, 26),
    (51, "الذاريات", "Adh-Dhariyat", 60, "meccan", 520, 523, 26),
    (52, "الطور", "At-Tur", 49, "meccan", 523, 525, 27),
    (53, "النجم", "An-Najm", 62, "meccan", 526, 528, 27),
    (54, "القمر", "Al-Qamar", 55, "meccan", 528, 531, 27),
    (55, "الرحمن", "Ar-Rahman", 78, "medinan", 531, 534, 27),
    (56, "الواقعة", "Al-Waqi'ah", 96, "meccan", 534, 537, 27),
    (57, "الحديد", "Al-Hadid", 29, "medinan", 537, 541, 27),
    (58, "المجادلة", "Al-Mujadilah", 22, "medinan", 542, 545, 28),
    (59, "الحشر", "Al-Hashr", 24, "medinan", 545, 548, 28),
    (60, "الممتحنة", "Al-Mumtahanah", 13, "medinan", 549, 551, 28),
    (61, "الصف", "As-Saff", 14, "medinan", 551, 552, 28),
    (62, "الجمعة", "Al-Jumu'ah", 11, "medinan", 553, 554, 28),
    (63, "المنافقون", "Al-Munafiqun", 11, "medinan", 554, 555, 28),
    (64, "التغابن", "At-Taghabun", 18, "medinan", 556, 557, 28),
    (65, "الطلاق", "At-Talaq", 12, "medinan", 558, 559, 28),
    (66, "التحريم", "At-Tahrim", 12, "medinan", 560, 561, 28),
    (67, "الملك", "Al-Mulk", 30, "meccan", 562, 564, 29),
    (68, "القلم", "Al-Qalam", 52, "meccan", 564, 566, 29),
    (69, "الحاقة", "Al-Haqqah", 52, "meccan", 566, 568, 29),
    (70, "المعارج", "Al-Ma'arij", 44, "meccan", 568, 570, 29),
    (71, "نوح", "Nuh", 28, "meccan", 570, 571, 29),
    (72, "الجن", "Al-Jinn", 28, "meccan", 572, 573, 29),
    (73, "المزمل", "Al-Muzzammil", 20, "meccan", 574, 575, 29),
    (74, "المدثر", "Al-Muddaththir", 56, "meccan", 575, 577, 29),
    (75, "القيامة", "Al-Qiyamah", 40, "meccan", 577, 578, 29),
    (76, "الإنسان", "Al-Insan", 31, "medinan", 578, 580, 29),
    (77, "المرسلات", "Al-Mursalat", 50, "meccan", 580, 581, 29),
    (78, "النبأ", "An-Naba", 40, "meccan", 582, 583, 30),
    (79, "النازعات", "An-Nazi'at", 46, "meccan", 583, 584, 30),
    (80, "عبس", "Abasa", 42, "meccan", 585, 585, 30),
    (81, "التكوير", "At-Takwir", 29, "meccan", 586, 586, 30),
    (82, "الانفطار", "Al-Infitar", 19, "meccan", 587, 587, 30),
    (83, "المطففين", "Al-Mutaffifin", 36, "meccan", 587, 589, 30),
    (84, "الانشقاق", "Al-Inshiqaq", 25, "meccan", 589, 589, 30),
    (85, "البروج", "Al-Buruj", 22, "meccan", 590, 590, 30),
    (86, "الطارق", "At-Tariq", 17, "meccan", 591, 591, 30),
    (87, "الأعلى", "Al-A'la", 19, "meccan", 591, 592, 30),
    (88, "الغاشية", "Al-Ghashiyah", 26, "meccan", 592, 592, 30),
    (89, "الفجر", "Al-Fajr", 30, "meccan", 593, 594, 30),
    (90, "البلد", "Al-Balad", 20, "meccan", 594, 594, 30),
    (91, "الشمس", "Ash-Shams", 15, "meccan", 595, 595, 30),
    (92, "الليل", "Al-Layl", 21, "meccan", 595, 596, 30),
    (93, "الضحى", "Ad-Duha", 11, "meccan", 596, 596, 30),
    (94, "الشرح", "Ash-Sharh", 8, "meccan", 596, 596, 30),
    (95, "التين", "At-Tin", 8, "meccan", 597, 597, 30),
    (96, "العلق", "Al-Alaq", 19, "meccan", 597, 597, 30),
    (97, "القدر", "Al-Qadr", 5, "meccan", 598, 598, 30),
    (98, "البينة", "Al-Bayyinah", 8, "medinan", 598, 599, 30),
    (99, "الزلزلة", "Az-Zalzalah", 8, "medinan", 599, 599, 30),
    (100, "العاديات", "Al-Adiyat", 11, "meccan", 599, 600, 30),
    (101, "القارعة", "Al-Qari'ah", 11, "meccan", 600, 600, 30),
    (102, "التكاثر", "At-Takathur", 8, "meccan", 600, 600, 30),
    (103, "العصر", "Al-Asr", 3, "meccan", 601, 601, 30),
    (104, "الهمزة", "Al-Humazah", 9, "meccan", 601, 601, 30),
    (105, "الفيل", "Al-Fil", 5, "meccan", 601, 601, 30),
    (106, "قريش", "Quraysh", 4, "meccan", 602, 602, 30),
    (107, "الماعون", "Al-Ma'un", 7, "meccan", 602, 602, 30),
    (108, "الكوثر", "Al-Kawthar", 3, "meccan", 602, 602, 30),
    (109, "الكافرون", "Al-Kafirun", 6, "meccan", 603, 603, 30),
    (110, "النصر", "An-Nasr", 3, "medinan", 603, 603, 30),
    (111, "المسد", "Al-Masad", 5, "meccan", 603, 603, 30),
    (112, "الإخلاص", "Al-Ikhlas", 4, "meccan", 604, 604, 30),
    (113, "الفلق", "Al-Falaq", 5, "meccan", 604, 604, 30),
    (114, "الناس", "An-Nas", 6, "meccan", 604, 604, 30),
]


class Command(BaseCommand):
    help = 'تحميل بيانات القرآن الكريم'

    def handle(self, *args, **options):
        self.stdout.write('جاري تحميل بيانات القرآن الكريم...')

        # تحميل السور
        self.stdout.write('تحميل السور...')
        for data in SURAHS_DATA:
            surah, created = Surah.objects.update_or_create(
                number=data[0],
                defaults={
                    'name_arabic': data[1],
                    'name_english': data[2],
                    'total_ayat': data[3],
                    'revelation_type': data[4],
                    'page_start': data[5],
                    'page_end': data[6],
                    'juz_start': data[7],
                }
            )
            if created:
                self.stdout.write(f'  تم إنشاء سورة: {surah.name_arabic}')

        # إنشاء صفحات المصحف (604 صفحة)
        self.stdout.write('إنشاء صفحات المصحف...')
        for page_num in range(1, 605):
            juz = ((page_num - 1) // 20) + 1
            hizb = ((page_num - 1) // 10) + 1
            QuranPage.objects.update_or_create(
                number=page_num,
                defaults={'juz': juz, 'hizb': hizb}
            )

        # إنشاء الأجزاء
        self.stdout.write('إنشاء الأجزاء...')
        juz_data = [
            (1, 1, 1, 2, 141),  # الجزء الأول
            (2, 2, 142, 2, 252),
            (3, 2, 253, 3, 92),
            (4, 3, 93, 4, 23),
            (5, 4, 24, 4, 147),
            (6, 4, 148, 5, 81),
            (7, 5, 82, 6, 110),
            (8, 6, 111, 7, 87),
            (9, 7, 88, 8, 40),
            (10, 8, 41, 9, 92),
            (11, 9, 93, 11, 5),
            (12, 11, 6, 12, 52),
            (13, 12, 53, 14, 52),
            (14, 15, 1, 16, 128),
            (15, 17, 1, 18, 74),
            (16, 18, 75, 20, 135),
            (17, 21, 1, 22, 78),
            (18, 23, 1, 25, 20),
            (19, 25, 21, 27, 55),
            (20, 27, 56, 29, 45),
            (21, 29, 46, 33, 30),
            (22, 33, 31, 36, 27),
            (23, 36, 28, 39, 31),
            (24, 39, 32, 41, 46),
            (25, 41, 47, 45, 37),
            (26, 46, 1, 51, 30),
            (27, 51, 31, 57, 29),
            (28, 58, 1, 66, 12),
            (29, 67, 1, 77, 50),
            (30, 78, 1, 114, 6),
        ]

        for juz_num, start_surah, start_ayah, end_surah, end_ayah in juz_data:
            start_surah_obj = Surah.objects.get(number=start_surah)
            end_surah_obj = Surah.objects.get(number=end_surah)
            Juz.objects.update_or_create(
                number=juz_num,
                defaults={
                    'start_surah': start_surah_obj,
                    'start_ayah': start_ayah,
                    'end_surah': end_surah_obj,
                    'end_ayah': end_ayah,
                }
            )

        self.stdout.write(self.style.SUCCESS('تم تحميل بيانات القرآن بنجاح!'))
        self.stdout.write(f'  - عدد السور: {Surah.objects.count()}')
        self.stdout.write(f'  - عدد الصفحات: {QuranPage.objects.count()}')
        self.stdout.write(f'  - عدد الأجزاء: {Juz.objects.count()}')
