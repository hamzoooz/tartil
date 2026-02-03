"""
إدارة نماذج القرآن
"""
from django.contrib import admin
from .models import Surah, Ayah, Juz, Hizb, QuranPage


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    """إدارة السور"""
    list_display = ['number', 'name_arabic', 'name_english', 'total_ayat',
                   'revelation_type', 'page_start', 'page_end']
    list_filter = ['revelation_type', 'juz_start']
    search_fields = ['name_arabic', 'name_english']
    ordering = ['number']


@admin.register(Ayah)
class AyahAdmin(admin.ModelAdmin):
    """إدارة الآيات"""
    list_display = ['surah', 'number', 'page', 'juz', 'hizb']
    list_filter = ['surah', 'juz', 'hizb']
    search_fields = ['text_uthmani', 'text_simple']
    raw_id_fields = ['surah']
    ordering = ['surah', 'number']


@admin.register(Juz)
class JuzAdmin(admin.ModelAdmin):
    """إدارة الأجزاء"""
    list_display = ['number', 'name', 'start_surah', 'start_ayah', 'end_surah', 'end_ayah']
    search_fields = ['name']
    ordering = ['number']


@admin.register(Hizb)
class HizbAdmin(admin.ModelAdmin):
    """إدارة الأحزاب"""
    list_display = ['number', 'juz', 'start_surah', 'start_ayah']
    list_filter = ['juz']
    ordering = ['number']


@admin.register(QuranPage)
class QuranPageAdmin(admin.ModelAdmin):
    """إدارة صفحات المصحف"""
    list_display = ['number', 'juz', 'hizb']
    list_filter = ['juz', 'hizb']
    ordering = ['number']
