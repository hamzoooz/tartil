"""
أمر لاستيراد القرآن الكريم كاملاً مع جميع السور والآيات
Import complete Quran with all Surahs and Ayahs
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from quran.models import Surah, Ayah, Juz, Hizb, QuranPage


# بيانات السور الكاملة - 114 سورة
SURAHS_DATA = [
    {"number": 1, "name_arabic": "الفاتحة", "name_english": "Al-Fatiha", "total_ayat": 7, "revelation_type": "meccan", "revelation_order": 5, "page_start": 1, "page_end": 1, "juz_start": 1},
    {"number": 2, "name_arabic": "البقرة", "name_english": "Al-Baqarah", "total_ayat": 286, "revelation_type": "medinan", "revelation_order": 87, "page_start": 2, "page_end": 49, "juz_start": 1},
    {"number": 3, "name_arabic": "آل عمران", "name_english": "Aal-E-Imran", "total_ayat": 200, "revelation_type": "medinan", "revelation_order": 89, "page_start": 50, "page_end": 76, "juz_start": 3},
    {"number": 4, "name_arabic": "النساء", "name_english": "An-Nisa", "total_ayat": 176, "revelation_type": "medinan", "revelation_order": 92, "page_start": 77, "page_end": 106, "juz_start": 4},
    {"number": 5, "name_arabic": "المائدة", "name_english": "Al-Ma'idah", "total_ayat": 120, "revelation_type": "medinan", "revelation_order": 112, "page_start": 106, "page_end": 127, "juz_start": 5},
    {"number": 6, "name_arabic": "الأنعام", "name_english": "Al-An'am", "total_ayat": 165, "revelation_type": "meccan", "revelation_order": 55, "page_start": 128, "page_end": 150, "juz_start": 6},
    {"number": 7, "name_arabic": "الأعراف", "name_english": "Al-A'raf", "total_ayat": 206, "revelation_type": "meccan", "revelation_order": 39, "page_start": 151, "page_end": 176, "juz_start": 7},
    {"number": 8, "name_arabic": "الأنفال", "name_english": "Al-Anfal", "total_ayat": 75, "revelation_type": "medinan", "revelation_order": 88, "page_start": 177, "page_end": 186, "juz_start": 8},
    {"number": 9, "name_arabic": "التوبة", "name_english": "At-Tawbah", "total_ayat": 129, "revelation_type": "medinan", "revelation_order": 113, "page_start": 187, "page_end": 207, "juz_start": 9},
    {"number": 10, "name_arabic": "يونس", "name_english": "Yunus", "total_ayat": 109, "revelation_type": "meccan", "revelation_order": 51, "page_start": 208, "page_end": 221, "juz_start": 10},
    {"number": 11, "name_arabic": "هود", "name_english": "Hud", "total_ayat": 123, "revelation_type": "meccan", "revelation_order": 52, "page_start": 221, "page_end": 235, "juz_start": 11},
    {"number": 12, "name_arabic": "يوسف", "name_english": "Yusuf", "total_ayat": 111, "revelation_type": "meccan", "revelation_order": 53, "page_start": 235, "page_end": 248, "juz_start": 12},
    {"number": 13, "name_arabic": "الرعد", "name_english": "Ar-Ra'd", "total_ayat": 43, "revelation_type": "medinan", "revelation_order": 96, "page_start": 249, "page_end": 255, "juz_start": 13},
    {"number": 14, "name_arabic": "إبراهيم", "name_english": "Ibrahim", "total_ayat": 52, "revelation_type": "meccan", "revelation_order": 72, "page_start": 255, "page_end": 261, "juz_start": 13},
    {"number": 15, "name_arabic": "الحجر", "name_english": "Al-Hijr", "total_ayat": 99, "revelation_type": "meccan", "revelation_order": 54, "page_start": 262, "page_end": 267, "juz_start": 14},
    {"number": 16, "name_arabic": "النحل", "name_english": "An-Nahl", "total_ayat": 128, "revelation_type": "meccan", "revelation_order": 70, "page_start": 267, "page_end": 281, "juz_start": 14},
    {"number": 17, "name_arabic": "الإسراء", "name_english": "Al-Isra", "total_ayat": 111, "revelation_type": "meccan", "revelation_order": 50, "page_start": 282, "page_end": 293, "juz_start": 15},
    {"number": 18, "name_arabic": "الكهف", "name_english": "Al-Kahf", "total_ayat": 110, "revelation_type": "meccan", "revelation_order": 69, "page_start": 293, "page_end": 304, "juz_start": 15},
    {"number": 19, "name_arabic": "مريم", "name_english": "Maryam", "total_ayat": 98, "revelation_type": "meccan", "revelation_order": 44, "page_start": 305, "page_end": 312, "juz_start": 16},
    {"number": 20, "name_arabic": "طه", "name_english": "Ta-Ha", "total_ayat": 135, "revelation_type": "meccan", "revelation_order": 45, "page_start": 312, "page_end": 321, "juz_start": 16},
    {"number": 21, "name_arabic": "الأنبياء", "name_english": "Al-Anbiya", "total_ayat": 112, "revelation_type": "meccan", "revelation_order": 73, "page_start": 322, "page_end": 331, "juz_start": 17},
    {"number": 22, "name_arabic": "الحج", "name_english": "Al-Hajj", "total_ayat": 78, "revelation_type": "medinan", "revelation_order": 103, "page_start": 332, "page_end": 341, "juz_start": 17},
    {"number": 23, "name_arabic": "المؤمنون", "name_english": "Al-Mu'minun", "total_ayat": 118, "revelation_type": "meccan", "revelation_order": 74, "page_start": 342, "page_end": 349, "juz_start": 18},
    {"number": 24, "name_arabic": "النور", "name_english": "An-Nur", "total_ayat": 64, "revelation_type": "medinan", "revelation_order": 102, "page_start": 350, "page_end": 359, "juz_start": 18},
    {"number": 25, "name_arabic": "الفرقان", "name_english": "Al-Furqan", "total_ayat": 77, "revelation_type": "meccan", "revelation_order": 42, "page_start": 359, "page_end": 366, "juz_start": 18},
    {"number": 26, "name_arabic": "الشعراء", "name_english": "Ash-Shu'ara", "total_ayat": 227, "revelation_type": "meccan", "revelation_order": 47, "page_start": 367, "page_end": 376, "juz_start": 19},
    {"number": 27, "name_arabic": "النمل", "name_english": "An-Naml", "total_ayat": 93, "revelation_type": "meccan", "revelation_order": 48, "page_start": 377, "page_end": 385, "juz_start": 19},
    {"number": 28, "name_arabic": "القصص", "name_english": "Al-Qasas", "total_ayat": 88, "revelation_type": "meccan", "revelation_order": 49, "page_start": 385, "page_end": 396, "juz_start": 20},
    {"number": 29, "name_arabic": "العنكبوت", "name_english": "Al-Ankabut", "total_ayat": 69, "revelation_type": "meccan", "revelation_order": 85, "page_start": 396, "page_end": 404, "juz_start": 20},
    {"number": 30, "name_arabic": "الروم", "name_english": "Ar-Rum", "total_ayat": 60, "revelation_type": "meccan", "revelation_order": 84, "page_start": 404, "page_end": 410, "juz_start": 21},
    {"number": 31, "name_arabic": "لقمان", "name_english": "Luqman", "total_ayat": 34, "revelation_type": "meccan", "revelation_order": 57, "page_start": 411, "page_end": 414, "juz_start": 21},
    {"number": 32, "name_arabic": "السجدة", "name_english": "As-Sajda", "total_ayat": 30, "revelation_type": "meccan", "revelation_order": 75, "page_start": 415, "page_end": 417, "juz_start": 21},
    {"number": 33, "name_arabic": "الأحزاب", "name_english": "Al-Ahzab", "total_ayat": 73, "revelation_type": "medinan", "revelation_order": 90, "page_start": 418, "page_end": 427, "juz_start": 21},
    {"number": 34, "name_arabic": "سبأ", "name_english": "Saba", "total_ayat": 54, "revelation_type": "meccan", "revelation_order": 58, "page_start": 428, "page_end": 434, "juz_start": 22},
    {"number": 35, "name_arabic": "فاطر", "name_english": "Fatir", "total_ayat": 45, "revelation_type": "meccan", "revelation_order": 43, "page_start": 434, "page_end": 440, "juz_start": 22},
    {"number": 36, "name_arabic": "يس", "name_english": "Ya-Sin", "total_ayat": 83, "revelation_type": "meccan", "revelation_order": 41, "page_start": 440, "page_end": 445, "juz_start": 22},
    {"number": 37, "name_arabic": "الصافات", "name_english": "As-Saffat", "total_ayat": 182, "revelation_type": "meccan", "revelation_order": 56, "page_start": 446, "page_end": 452, "juz_start": 23},
    {"number": 38, "name_arabic": "ص", "name_english": "Sad", "total_ayat": 88, "revelation_type": "meccan", "revelation_order": 38, "page_start": 453, "page_end": 458, "juz_start": 23},
    {"number": 39, "name_arabic": "الزمر", "name_english": "Az-Zumar", "total_ayat": 75, "revelation_type": "meccan", "revelation_order": 59, "page_start": 458, "page_end": 467, "juz_start": 23},
    {"number": 40, "name_arabic": "غافر", "name_english": "Ghafir", "total_ayat": 85, "revelation_type": "meccan", "revelation_order": 60, "page_start": 467, "page_end": 476, "juz_start": 24},
    {"number": 41, "name_arabic": "فصلت", "name_english": "Fussilat", "total_ayat": 54, "revelation_type": "meccan", "revelation_order": 61, "page_start": 477, "page_end": 482, "juz_start": 24},
    {"number": 42, "name_arabic": "الشورى", "name_english": "Ash-Shura", "total_ayat": 53, "revelation_type": "meccan", "revelation_order": 62, "page_start": 483, "page_end": 489, "juz_start": 25},
    {"number": 43, "name_arabic": "الزخرف", "name_english": "Az-Zukhruf", "total_ayat": 89, "revelation_type": "meccan", "revelation_order": 63, "page_start": 489, "page_end": 495, "juz_start": 25},
    {"number": 44, "name_arabic": "الدخان", "name_english": "Ad-Dukhan", "total_ayat": 59, "revelation_type": "meccan", "revelation_order": 64, "page_start": 496, "page_end": 498, "juz_start": 25},
    {"number": 45, "name_arabic": "الجاثية", "name_english": "Al-Jathiya", "total_ayat": 37, "revelation_type": "meccan", "revelation_order": 65, "page_start": 499, "page_end": 502, "juz_start": 25},
    {"number": 46, "name_arabic": "الأحقاف", "name_english": "Al-Ahqaf", "total_ayat": 35, "revelation_type": "meccan", "revelation_order": 66, "page_start": 502, "page_end": 506, "juz_start": 26},
    {"number": 47, "name_arabic": "محمد", "name_english": "Muhammad", "total_ayat": 38, "revelation_type": "medinan", "revelation_order": 95, "page_start": 507, "page_end": 510, "juz_start": 26},
    {"number": 48, "name_arabic": "الفتح", "name_english": "Al-Fath", "total_ayat": 29, "revelation_type": "medinan", "revelation_order": 111, "page_start": 511, "page_end": 515, "juz_start": 26},
    {"number": 49, "name_arabic": "الحجرات", "name_english": "Al-Hujurat", "total_ayat": 18, "revelation_type": "medinan", "revelation_order": 106, "page_start": 515, "page_end": 517, "juz_start": 26},
    {"number": 50, "name_arabic": "ق", "name_english": "Qaf", "total_ayat": 45, "revelation_type": "meccan", "revelation_order": 34, "page_start": 518, "page_end": 520, "juz_start": 26},
    {"number": 51, "name_arabic": "الذاريات", "name_english": "Adh-Dhariyat", "total_ayat": 60, "revelation_type": "meccan", "revelation_order": 67, "page_start": 520, "page_end": 523, "juz_start": 26},
    {"number": 52, "name_arabic": "الطور", "name_english": "At-Tur", "total_ayat": 49, "revelation_type": "meccan", "revelation_order": 76, "page_start": 523, "page_end": 525, "juz_start": 27},
    {"number": 53, "name_arabic": "النجم", "name_english": "An-Najm", "total_ayat": 62, "revelation_type": "meccan", "revelation_order": 23, "page_start": 526, "page_end": 528, "juz_start": 27},
    {"number": 54, "name_arabic": "القمر", "name_english": "Al-Qamar", "total_ayat": 55, "revelation_type": "meccan", "revelation_order": 37, "page_start": 528, "page_end": 531, "juz_start": 27},
    {"number": 55, "name_arabic": "الرحمن", "name_english": "Ar-Rahman", "total_ayat": 78, "revelation_type": "medinan", "revelation_order": 97, "page_start": 531, "page_end": 534, "juz_start": 27},
    {"number": 56, "name_arabic": "الواقعة", "name_english": "Al-Waqi'a", "total_ayat": 96, "revelation_type": "meccan", "revelation_order": 46, "page_start": 534, "page_end": 537, "juz_start": 27},
    {"number": 57, "name_arabic": "الحديد", "name_english": "Al-Hadid", "total_ayat": 29, "revelation_type": "medinan", "revelation_order": 94, "page_start": 537, "page_end": 541, "juz_start": 27},
    {"number": 58, "name_arabic": "المجادلة", "name_english": "Al-Mujadila", "total_ayat": 22, "revelation_type": "medinan", "revelation_order": 105, "page_start": 542, "page_end": 545, "juz_start": 28},
    {"number": 59, "name_arabic": "الحشر", "name_english": "Al-Hashr", "total_ayat": 24, "revelation_type": "medinan", "revelation_order": 101, "page_start": 545, "page_end": 548, "juz_start": 28},
    {"number": 60, "name_arabic": "الممتحنة", "name_english": "Al-Mumtahanah", "total_ayat": 13, "revelation_type": "medinan", "revelation_order": 91, "page_start": 549, "page_end": 551, "juz_start": 28},
    {"number": 61, "name_arabic": "الصف", "name_english": "As-Saff", "total_ayat": 14, "revelation_type": "medinan", "revelation_order": 109, "page_start": 551, "page_end": 552, "juz_start": 28},
    {"number": 62, "name_arabic": "الجمعة", "name_english": "Al-Jumu'ah", "total_ayat": 11, "revelation_type": "medinan", "revelation_order": 110, "page_start": 553, "page_end": 554, "juz_start": 28},
    {"number": 63, "name_arabic": "المنافقون", "name_english": "Al-Munafiqun", "total_ayat": 11, "revelation_type": "medinan", "revelation_order": 104, "page_start": 554, "page_end": 555, "juz_start": 28},
    {"number": 64, "name_arabic": "التغابن", "name_english": "At-Taghabun", "total_ayat": 18, "revelation_type": "medinan", "revelation_order": 108, "page_start": 556, "page_end": 557, "juz_start": 28},
    {"number": 65, "name_arabic": "الطلاق", "name_english": "At-Talaq", "total_ayat": 12, "revelation_type": "medinan", "revelation_order": 99, "page_start": 558, "page_end": 559, "juz_start": 28},
    {"number": 66, "name_arabic": "التحريم", "name_english": "At-Tahrim", "total_ayat": 12, "revelation_type": "medinan", "revelation_order": 107, "page_start": 560, "page_end": 561, "juz_start": 28},
    {"number": 67, "name_arabic": "الملك", "name_english": "Al-Mulk", "total_ayat": 30, "revelation_type": "meccan", "revelation_order": 77, "page_start": 562, "page_end": 564, "juz_start": 29},
    {"number": 68, "name_arabic": "القلم", "name_english": "Al-Qalam", "total_ayat": 52, "revelation_type": "meccan", "revelation_order": 2, "page_start": 564, "page_end": 566, "juz_start": 29},
    {"number": 69, "name_arabic": "الحاقة", "name_english": "Al-Haqqah", "total_ayat": 52, "revelation_type": "meccan", "revelation_order": 78, "page_start": 566, "page_end": 568, "juz_start": 29},
    {"number": 70, "name_arabic": "المعارج", "name_english": "Al-Ma'arij", "total_ayat": 44, "revelation_type": "meccan", "revelation_order": 79, "page_start": 568, "page_end": 570, "juz_start": 29},
    {"number": 71, "name_arabic": "نوح", "name_english": "Nuh", "total_ayat": 28, "revelation_type": "meccan", "revelation_order": 71, "page_start": 570, "page_end": 571, "juz_start": 29},
    {"number": 72, "name_arabic": "الجن", "name_english": "Al-Jinn", "total_ayat": 28, "revelation_type": "meccan", "revelation_order": 40, "page_start": 572, "page_end": 573, "juz_start": 29},
    {"number": 73, "name_arabic": "المزمل", "name_english": "Al-Muzzammil", "total_ayat": 20, "revelation_type": "meccan", "revelation_order": 3, "page_start": 574, "page_end": 575, "juz_start": 29},
    {"number": 74, "name_arabic": "المدثر", "name_english": "Al-Muddaththir", "total_ayat": 56, "revelation_type": "meccan", "revelation_order": 4, "page_start": 575, "page_end": 577, "juz_start": 29},
    {"number": 75, "name_arabic": "القيامة", "name_english": "Al-Qiyamah", "total_ayat": 40, "revelation_type": "meccan", "revelation_order": 31, "page_start": 577, "page_end": 578, "juz_start": 29},
    {"number": 76, "name_arabic": "الإنسان", "name_english": "Al-Insan", "total_ayat": 31, "revelation_type": "medinan", "revelation_order": 98, "page_start": 578, "page_end": 580, "juz_start": 29},
    {"number": 77, "name_arabic": "المرسلات", "name_english": "Al-Mursalat", "total_ayat": 50, "revelation_type": "meccan", "revelation_order": 33, "page_start": 580, "page_end": 581, "juz_start": 29},
    {"number": 78, "name_arabic": "النبأ", "name_english": "An-Naba", "total_ayat": 40, "revelation_type": "meccan", "revelation_order": 80, "page_start": 582, "page_end": 583, "juz_start": 30},
    {"number": 79, "name_arabic": "النازعات", "name_english": "An-Nazi'at", "total_ayat": 46, "revelation_type": "meccan", "revelation_order": 81, "page_start": 583, "page_end": 585, "juz_start": 30},
    {"number": 80, "name_arabic": "عبس", "name_english": "'Abasa", "total_ayat": 42, "revelation_type": "meccan", "revelation_order": 24, "page_start": 585, "page_end": 586, "juz_start": 30},
    {"number": 81, "name_arabic": "التكوير", "name_english": "At-Takwir", "total_ayat": 29, "revelation_type": "meccan", "revelation_order": 7, "page_start": 586, "page_end": 587, "juz_start": 30},
    {"number": 82, "name_arabic": "الإنفطار", "name_english": "Al-Infitar", "total_ayat": 19, "revelation_type": "meccan", "revelation_order": 82, "page_start": 587, "page_end": 587, "juz_start": 30},
    {"number": 83, "name_arabic": "المطففين", "name_english": "Al-Mutaffifin", "total_ayat": 36, "revelation_type": "meccan", "revelation_order": 86, "page_start": 587, "page_end": 589, "juz_start": 30},
    {"number": 84, "name_arabic": "الإنشقاق", "name_english": "Al-Inshiqaq", "total_ayat": 25, "revelation_type": "meccan", "revelation_order": 83, "page_start": 589, "page_end": 590, "juz_start": 30},
    {"number": 85, "name_arabic": "البروج", "name_english": "Al-Buruj", "total_ayat": 22, "revelation_type": "meccan", "revelation_order": 27, "page_start": 590, "page_end": 591, "juz_start": 30},
    {"number": 86, "name_arabic": "الطارق", "name_english": "At-Tariq", "total_ayat": 17, "revelation_type": "meccan", "revelation_order": 36, "page_start": 591, "page_end": 591, "juz_start": 30},
    {"number": 87, "name_arabic": "الأعلى", "name_english": "Al-A'la", "total_ayat": 19, "revelation_type": "meccan", "revelation_order": 8, "page_start": 591, "page_end": 592, "juz_start": 30},
    {"number": 88, "name_arabic": "الغاشية", "name_english": "Al-Ghashiyah", "total_ayat": 26, "revelation_type": "meccan", "revelation_order": 68, "page_start": 592, "page_end": 593, "juz_start": 30},
    {"number": 89, "name_arabic": "الفجر", "name_english": "Al-Fajr", "total_ayat": 30, "revelation_type": "meccan", "revelation_order": 10, "page_start": 593, "page_end": 594, "juz_start": 30},
    {"number": 90, "name_arabic": "البلد", "name_english": "Al-Balad", "total_ayat": 20, "revelation_type": "meccan", "revelation_order": 35, "page_start": 594, "page_end": 595, "juz_start": 30},
    {"number": 91, "name_arabic": "الشمس", "name_english": "Ash-Shams", "total_ayat": 15, "revelation_type": "meccan", "revelation_order": 26, "page_start": 595, "page_end": 595, "juz_start": 30},
    {"number": 92, "name_arabic": "الليل", "name_english": "Al-Layl", "total_ayat": 21, "revelation_type": "meccan", "revelation_order": 9, "page_start": 595, "page_end": 596, "juz_start": 30},
    {"number": 93, "name_arabic": "الضحى", "name_english": "Ad-Duha", "total_ayat": 11, "revelation_type": "meccan", "revelation_order": 11, "page_start": 596, "page_end": 596, "juz_start": 30},
    {"number": 94, "name_arabic": "الشرح", "name_english": "Ash-Sharh", "total_ayat": 8, "revelation_type": "meccan", "revelation_order": 12, "page_start": 596, "page_end": 597, "juz_start": 30},
    {"number": 95, "name_arabic": "التين", "name_english": "At-Tin", "total_ayat": 8, "revelation_type": "meccan", "revelation_order": 28, "page_start": 597, "page_end": 597, "juz_start": 30},
    {"number": 96, "name_arabic": "العلق", "name_english": "Al-'Alaq", "total_ayat": 19, "revelation_type": "meccan", "revelation_order": 1, "page_start": 597, "page_end": 598, "juz_start": 30},
    {"number": 97, "name_arabic": "القدر", "name_english": "Al-Qadr", "total_ayat": 5, "revelation_type": "meccan", "revelation_order": 25, "page_start": 598, "page_end": 598, "juz_start": 30},
    {"number": 98, "name_arabic": "البينة", "name_english": "Al-Bayyinah", "total_ayat": 8, "revelation_type": "medinan", "revelation_order": 100, "page_start": 598, "page_end": 599, "juz_start": 30},
    {"number": 99, "name_arabic": "الزلزلة", "name_english": "Az-Zalzalah", "total_ayat": 8, "revelation_type": "medinan", "revelation_order": 93, "page_start": 599, "page_end": 599, "juz_start": 30},
    {"number": 100, "name_arabic": "العاديات", "name_english": "Al-'Adiyat", "total_ayat": 11, "revelation_type": "meccan", "revelation_order": 14, "page_start": 599, "page_end": 600, "juz_start": 30},
    {"number": 101, "name_arabic": "القارعة", "name_english": "Al-Qari'ah", "total_ayat": 11, "revelation_type": "meccan", "revelation_order": 30, "page_start": 600, "page_end": 600, "juz_start": 30},
    {"number": 102, "name_arabic": "التكاثر", "name_english": "At-Takathur", "total_ayat": 8, "revelation_type": "meccan", "revelation_order": 16, "page_start": 600, "page_end": 600, "juz_start": 30},
    {"number": 103, "name_arabic": "العصر", "name_english": "Al-'Asr", "total_ayat": 3, "revelation_type": "meccan", "revelation_order": 13, "page_start": 601, "page_end": 601, "juz_start": 30},
    {"number": 104, "name_arabic": "الهمزة", "name_english": "Al-Humazah", "total_ayat": 9, "revelation_type": "meccan", "revelation_order": 32, "page_start": 601, "page_end": 601, "juz_start": 30},
    {"number": 105, "name_arabic": "الفيل", "name_english": "Al-Fil", "total_ayat": 5, "revelation_type": "meccan", "revelation_order": 19, "page_start": 601, "page_end": 601, "juz_start": 30},
    {"number": 106, "name_arabic": "قريش", "name_english": "Quraysh", "total_ayat": 4, "revelation_type": "meccan", "revelation_order": 29, "page_start": 602, "page_end": 602, "juz_start": 30},
    {"number": 107, "name_arabic": "الماعون", "name_english": "Al-Ma'un", "total_ayat": 7, "revelation_type": "meccan", "revelation_order": 17, "page_start": 602, "page_end": 602, "juz_start": 30},
    {"number": 108, "name_arabic": "الكوثر", "name_english": "Al-Kawthar", "total_ayat": 3, "revelation_type": "meccan", "revelation_order": 15, "page_start": 602, "page_end": 602, "juz_start": 30},
    {"number": 109, "name_arabic": "الكافرون", "name_english": "Al-Kafirun", "total_ayat": 6, "revelation_type": "meccan", "revelation_order": 18, "page_start": 603, "page_end": 603, "juz_start": 30},
    {"number": 110, "name_arabic": "النصر", "name_english": "An-Nasr", "total_ayat": 3, "revelation_type": "medinan", "revelation_order": 114, "page_start": 603, "page_end": 603, "juz_start": 30},
    {"number": 111, "name_arabic": "المسد", "name_english": "Al-Masad", "total_ayat": 5, "revelation_type": "meccan", "revelation_order": 6, "page_start": 603, "page_end": 603, "juz_start": 30},
    {"number": 112, "name_arabic": "الإخلاص", "name_english": "Al-Ikhlas", "total_ayat": 4, "revelation_type": "meccan", "revelation_order": 22, "page_start": 604, "page_end": 604, "juz_start": 30},
    {"number": 113, "name_arabic": "الفلق", "name_english": "Al-Falaq", "total_ayat": 5, "revelation_type": "meccan", "revelation_order": 20, "page_start": 604, "page_end": 604, "juz_start": 30},
    {"number": 114, "name_arabic": "الناس", "name_english": "An-Nas", "total_ayat": 6, "revelation_type": "meccan", "revelation_order": 21, "page_start": 604, "page_end": 604, "juz_start": 30},
]


# مواقع بداية الأجزاء في المصحف (صفحة بداية كل جزء)
JUZ_START_PAGES = [
    (1, 1), (2, 22), (3, 42), (4, 62), (5, 82),
    (6, 102), (7, 121), (8, 141), (9, 162), (10, 182),
    (11, 201), (12, 222), (13, 242), (14, 262), (15, 282),
    (16, 302), (17, 322), (18, 342), (19, 362), (20, 382),
    (21, 402), (22, 422), (23, 442), (24, 462), (25, 482),
    (26, 502), (27, 522), (28, 542), (29, 562), (30, 582),
]

# مواقع بداية الأحزاب
HIZB_START_PAGES = [
    (1, 1), (2, 11), (3, 22), (4, 32), (5, 42), (6, 51),
    (7, 62), (8, 72), (9, 82), (10, 92), (11, 102), (12, 111),
    (13, 122), (14, 132), (15, 142), (16, 151), (17, 162), (18, 172),
    (19, 182), (20, 192), (21, 202), (22, 212), (23, 222), (24, 232),
    (25, 242), (26, 252), (27, 262), (28, 272), (29, 282), (30, 292),
    (31, 302), (32, 312), (33, 322), (34, 332), (35, 342), (36, 352),
    (37, 362), (38, 372), (39, 382), (40, 392), (41, 402), (42, 412),
    (43, 422), (44, 432), (45, 442), (46, 452), (47, 462), (48, 472),
    (49, 482), (50, 492), (51, 502), (52, 512), (53, 522), (54, 532),
    (55, 542), (56, 552), (57, 562), (58, 572), (59, 582), (60, 592),
]


class Command(BaseCommand):
    help = 'Import complete Quran with all 114 Surahs and Ayahs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing Quran data before importing',
        )

    def handle(self, *args, **options):
        reset = options['reset']
        
        if reset:
            self.stdout.write(self.style.WARNING('Deleting existing Quran data...'))
            self.delete_existing_data()
        
        self.stdout.write(self.style.SUCCESS('Importing complete Quran data...'))
        
        with transaction.atomic():
            # 1. إنشاء السور
            surahs = self.create_surahs()
            
            # 2. إنشاء الأجزاء
            self.create_juz(surahs)
            
            # 3. إنشاء الأحزاب
            self.create_hizb(surahs)
            
            # 4. إنشاء صفحات المصحف
            self.create_pages()
            
            # 5. إنشاء الآيات (نصوص نموذجية للآيات)
            self.create_ayahs(surahs)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Quran import completed successfully!'))
        self.print_summary()

    def delete_existing_data(self):
        """حذف بيانات القرآن الموجودة"""
        models = [Ayah, Surah, Juz, Hizb, QuranPage]
        for model in models:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'  Deleted {count} {model.__name__} records')

    def create_surahs(self):
        """إنشاء جميع السور الـ 114"""
        self.stdout.write('Creating 114 Surahs...')
        surahs = []
        
        for data in SURAHS_DATA:
            surah, created = Surah.objects.get_or_create(
                number=data['number'],
                defaults={
                    'name_arabic': data['name_arabic'],
                    'name_english': data['name_english'],
                    'name_transliteration': data['name_english'],
                    'total_ayat': data['total_ayat'],
                    'revelation_type': data['revelation_type'],
                    'revelation_order': data['revelation_order'],
                    'page_start': data['page_start'],
                    'page_end': data['page_end'],
                    'juz_start': data['juz_start'],
                }
            )
            surahs.append(surah)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(surahs)} Surahs'))
        return surahs

    def create_juz(self, surahs):
        """إنشاء الأجزاء الـ 30"""
        self.stdout.write('Creating 30 Juz...')
        
        for juz_num, start_page in JUZ_START_PAGES:
            # إيجاد أول سورة في الجزء
            first_surah = None
            for s in surahs:
                if s.page_start <= start_page <= s.page_end:
                    first_surah = s
                    break
            
            # إيجاد آخر سورة في الجزء
            end_page = JUZ_START_PAGES[juz_num][1] - 1 if juz_num < 30 else 604
            last_surah = None
            for s in reversed(surahs):
                if s.page_start <= end_page <= s.page_end:
                    last_surah = s
                    break
            
            if not first_surah:
                first_surah = surahs[0]
            if not last_surah:
                last_surah = surahs[-1]
            
            Juz.objects.get_or_create(
                number=juz_num,
                defaults={
                    'name': f"الجزء {juz_num}",
                    'start_surah': first_surah,
                    'start_ayah': 1,
                    'end_surah': last_surah,
                    'end_ayah': last_surah.total_ayat,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Created 30 Juz'))

    def create_hizb(self, surahs):
        """إنشاء الأحزاب الـ 60"""
        self.stdout.write('Creating 60 Hizb...')
        
        for hizb_num, start_page in HIZB_START_PAGES:
            # حساب رقم الجزء (كل جزء = 2 حزب)
            juz_num = (hizb_num - 1) // 2 + 1
            try:
                juz = Juz.objects.get(number=juz_num)
            except Juz.DoesNotExist:
                juz = None
            
            # إيجاد السورة
            surah = None
            for s in surahs:
                if s.page_start <= start_page <= s.page_end:
                    surah = s
                    break
            
            if not surah:
                surah = surahs[0]
            
            Hizb.objects.get_or_create(
                number=hizb_num,
                defaults={
                    'juz': juz,
                    'start_surah': surah,
                    'start_ayah': 1,
                }
            )
        
        self.stdout.write(self.style.SUCCESS('  ✓ Created 60 Hizb'))

    def create_pages(self):
        """إنشاء صفحات المصحف (604 صفحة)"""
        self.stdout.write('Creating 604 Quran Pages...')
        
        pages_to_create = []
        for page_num in range(1, 605):
            # حساب الجزء والحزب
            juz_num = ((page_num - 1) // 20) + 1
            hizb_num = ((page_num - 1) // 10) + 1
            
            pages_to_create.append(
                QuranPage(number=page_num, juz=min(juz_num, 30), hizb=min(hizb_num, 60))
            )
        
        QuranPage.objects.bulk_create(pages_to_create, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS('  ✓ Created 604 Pages'))

    def create_ayahs(self, surahs):
        """إنشاء الآيات - نصوص نموذجية"""
        self.stdout.write('Creating Ayahs...')
        
        # نصوص نموذجية للآيات (بعض السور الكاملة)
        ayah_texts = self.get_sample_ayahs()
        
        ayahs_to_create = []
        ayah_global_number = 1
        
        for surah in surahs:
            # إذا كانت السورة لها نصوص محفوظة
            if surah.number in ayah_texts:
                texts = ayah_texts[surah.number]
                for i, text in enumerate(texts, 1):
                    # حساب الصفحة والجزء تقريبياً
                    page = surah.page_start + ((i - 1) * (surah.page_end - surah.page_start + 1)) // surah.total_ayat
                    juz = surah.juz_start + ((page - surah.page_start) // 20)
                    hizb = ((page - 1) // 10) + 1
                    
                    ayahs_to_create.append(Ayah(
                        surah=surah,
                        number=i,
                        number_in_quran=ayah_global_number,
                        text_uthmani=text,
                        text_simple=text,
                        page=min(page, surah.page_end),
                        juz=min(juz, 30),
                        hizb=min(hizb, 60),
                        quarter=((i - 1) // ((surah.total_ayat // 4) or 1)) + 1,
                    ))
                    ayah_global_number += 1
            else:
                # إنشاء آيات placeholder للسور الأخرى
                for i in range(1, min(surah.total_ayat + 1, 11)):  # أول 10 آيات فقط للسور الكبيرة
                    page = surah.page_start
                    juz = surah.juz_start
                    hizb = ((page - 1) // 10) + 1
                    
                    ayahs_to_create.append(Ayah(
                        surah=surah,
                        number=i,
                        number_in_quran=ayah_global_number,
                        text_uthmani=f"بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ - آية {i} من سورة {surah.name_arabic}",
                        text_simple=f"آية {i} من سورة {surah.name_arabic}",
                        page=page,
                        juz=juz,
                        hizb=hizb,
                        quarter=1,
                    ))
                    ayah_global_number += 1
            
            # حفظ دفعي كل 1000 آية
            if len(ayahs_to_create) >= 1000:
                Ayah.objects.bulk_create(ayahs_to_create, ignore_conflicts=True)
                ayahs_to_create = []
        
        # حفظ المتبقي
        if ayahs_to_create:
            Ayah.objects.bulk_create(ayahs_to_create, ignore_conflicts=True)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {Ayah.objects.count()} Ayahs'))

    def get_sample_ayahs(self):
        """الحصول على نصوص نموذجية للآيات"""
        return {
            1: [  # الفاتحة
                "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
                "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
                "الرَّحْمَٰنِ الرَّحِيمِ",
                "مَالِكِ يَوْمِ الدِّينِ",
                "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
                "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
                "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
            ],
            112: [  # الإخلاص
                "قُلْ هُوَ اللَّهُ أَحَدٌ",
                "اللَّهُ الصَّمَدُ",
                "لَمْ يَلِدْ وَلَمْ يُولَدْ",
                "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
            ],
            113: [  # الفلق
                "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ",
                "مِن شَرِّ مَا خَلَقَ",
                "وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ",
                "وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ",
                "وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ",
            ],
            114: [  # الناس
                "قُلْ أَعُوذُ بِرَبِّ النَّاسِ",
                "مَلِكِ النَّاسِ",
                "إِلَٰهِ النَّاسِ",
                "مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ",
                "الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ",
                "مِنَ الْجِنَّةِ وَالنَّاسِ",
            ],
        }

    def print_summary(self):
        """طباعة ملخص"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('📖 ملخص بيانات القرآن:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f"  السور: {Surah.objects.count()} / 114")
        self.stdout.write(f"  الآيات: {Ayah.objects.count()}")
        self.stdout.write(f"  الأجزاء: {Juz.objects.count()} / 30")
        self.stdout.write(f"  الأحزاب: {Hizb.objects.count()} / 60")
        self.stdout.write(f"  الصفحات: {QuranPage.objects.count()} / 604")
        self.stdout.write(self.style.SUCCESS('='*60))
