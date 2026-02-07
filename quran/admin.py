"""
إدارة نماذج القرآن
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Surah, Ayah, Juz, Hizb, QuranPage


class AyahInline(admin.TabularInline):
    """آيات السورة"""
    model = Ayah
    extra = 0
    fields = ['number', 'text_uthmani', 'page', 'juz']
    readonly_fields = ['number', 'page', 'juz']
    can_delete = False
    max_num = 0
    verbose_name = _('آية')
    verbose_name_plural = _('الآيات')


class HizbInline(admin.TabularInline):
    """أحزاب الجزء"""
    model = Hizb
    extra = 0
    fields = ['number', 'start_surah', 'start_ayah']
    raw_id_fields = ['start_surah']
    autocomplete_fields = ['start_surah']
    verbose_name = _('حزب')
    verbose_name_plural = _('الأحزاب')


@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    """إدارة السور"""
    list_display = ['number', 'name_arabic', 'name_english', 'total_ayat',
                   'revelation_type', 'page_start', 'page_end', 'juz_start']
    list_filter = ['revelation_type', 'juz_start']
    search_fields = ['name_arabic', 'name_english', 'name_transliteration']
    ordering = ['number']
    inlines = [AyahInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('number', 'name_arabic', 'name_english', 'name_transliteration')
        }),
        ('معلومات القرآنية', {
            'fields': ('total_ayat', 'revelation_type', 'revelation_order')
        }),
        ('الموقع في المصحف', {
            'fields': ('page_start', 'page_end', 'juz_start')
        }),
    )


@admin.register(Ayah)
class AyahAdmin(admin.ModelAdmin):
    """إدارة الآيات"""
    list_display = ['surah', 'number', 'number_in_quran', 'page', 'juz', 'hizb', 'quarter']
    list_filter = ['surah', 'juz', 'hizb']
    search_fields = ['text_uthmani', 'text_simple']
    raw_id_fields = ['surah']
    autocomplete_fields = ['surah']
    ordering = ['surah', 'number']
    
    fieldsets = (
        ('الموقع', {
            'fields': ('surah', 'number', 'number_in_quran')
        }),
        ('النص', {
            'fields': ('text_uthmani', 'text_simple')
        }),
        ('التقسيم القرآني', {
            'fields': ('page', 'juz', 'hizb', 'quarter')
        }),
    )


@admin.register(Juz)
class JuzAdmin(admin.ModelAdmin):
    """إدارة الأجزاء"""
    list_display = ['number', 'name', 'start_surah', 'start_ayah', 'end_surah', 'end_ayah']
    search_fields = ['name']
    ordering = ['number']
    inlines = [HizbInline]
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('number', 'name')
        }),
        ('بداية الجزء', {
            'fields': ('start_surah', 'start_ayah')
        }),
        ('نهاية الجزء', {
            'fields': ('end_surah', 'end_ayah')
        }),
    )


@admin.register(Hizb)
class HizbAdmin(admin.ModelAdmin):
    """إدارة الأحزاب"""
    list_display = ['number', 'juz', 'start_surah', 'start_ayah']
    list_filter = ['juz']
    ordering = ['number']
    raw_id_fields = ['juz', 'start_surah']
    autocomplete_fields = ['juz', 'start_surah']


@admin.register(QuranPage)
class QuranPageAdmin(admin.ModelAdmin):
    """إدارة صفحات المصحف"""
    list_display = ['number', 'juz', 'hizb', 'ayah_count']
    list_filter = ['juz', 'hizb']
    ordering = ['number']
    
    def ayah_count(self, obj):
        return obj.get_ayat().count()
    ayah_count.short_description = 'عدد الآيات'
