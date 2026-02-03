"""
نماذج القرآن الكريم
Quran Models for Tartil
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Surah(models.Model):
    """نموذج السورة"""

    class RevelationType(models.TextChoices):
        MECCAN = 'meccan', _('مكية')
        MEDINAN = 'medinan', _('مدنية')

    number = models.PositiveIntegerField(_('رقم السورة'), unique=True)
    name_arabic = models.CharField(_('اسم السورة بالعربية'), max_length=50)
    name_english = models.CharField(_('اسم السورة بالإنجليزية'), max_length=50)
    name_transliteration = models.CharField(_('اسم السورة بالحروف اللاتينية'), max_length=50, blank=True)
    total_ayat = models.PositiveIntegerField(_('عدد الآيات'))
    revelation_type = models.CharField(
        _('نوع النزول'),
        max_length=10,
        choices=RevelationType.choices
    )
    revelation_order = models.PositiveIntegerField(_('ترتيب النزول'), default=0)
    page_start = models.PositiveIntegerField(_('صفحة البداية'))
    page_end = models.PositiveIntegerField(_('صفحة النهاية'))
    juz_start = models.PositiveIntegerField(_('الجزء'), default=1)

    class Meta:
        verbose_name = _('سورة')
        verbose_name_plural = _('السور')
        ordering = ['number']

    def __str__(self):
        return f"{self.number}. {self.name_arabic}"

    @property
    def total_pages(self):
        return self.page_end - self.page_start + 1


class Ayah(models.Model):
    """نموذج الآية"""

    surah = models.ForeignKey(
        Surah,
        on_delete=models.CASCADE,
        related_name='ayat',
        verbose_name=_('السورة')
    )
    number = models.PositiveIntegerField(_('رقم الآية'))
    number_in_quran = models.PositiveIntegerField(_('الرقم في القرآن'), default=0)
    text_uthmani = models.TextField(_('النص بالرسم العثماني'))
    text_simple = models.TextField(_('النص المبسط'), blank=True)
    page = models.PositiveIntegerField(_('الصفحة'))
    juz = models.PositiveIntegerField(_('الجزء'))
    hizb = models.PositiveIntegerField(_('الحزب'))
    quarter = models.PositiveIntegerField(_('الربع'), default=1)

    class Meta:
        verbose_name = _('آية')
        verbose_name_plural = _('الآيات')
        ordering = ['surah', 'number']
        unique_together = ['surah', 'number']

    def __str__(self):
        return f"{self.surah.name_arabic} - الآية {self.number}"


class Juz(models.Model):
    """نموذج الجزء"""

    number = models.PositiveIntegerField(_('رقم الجزء'), unique=True)
    name = models.CharField(_('اسم الجزء'), max_length=100, blank=True)
    start_surah = models.ForeignKey(
        Surah,
        on_delete=models.CASCADE,
        related_name='juz_starts',
        verbose_name=_('سورة البداية')
    )
    start_ayah = models.PositiveIntegerField(_('آية البداية'))
    end_surah = models.ForeignKey(
        Surah,
        on_delete=models.CASCADE,
        related_name='juz_ends',
        verbose_name=_('سورة النهاية')
    )
    end_ayah = models.PositiveIntegerField(_('آية النهاية'))

    class Meta:
        verbose_name = _('جزء')
        verbose_name_plural = _('الأجزاء')
        ordering = ['number']

    def __str__(self):
        return f"الجزء {self.number}"


class Hizb(models.Model):
    """نموذج الحزب"""

    number = models.PositiveIntegerField(_('رقم الحزب'), unique=True)
    juz = models.ForeignKey(
        Juz,
        on_delete=models.CASCADE,
        related_name='ahzab',
        verbose_name=_('الجزء')
    )
    start_surah = models.ForeignKey(
        Surah,
        on_delete=models.CASCADE,
        related_name='hizb_starts',
        verbose_name=_('سورة البداية')
    )
    start_ayah = models.PositiveIntegerField(_('آية البداية'))

    class Meta:
        verbose_name = _('حزب')
        verbose_name_plural = _('الأحزاب')
        ordering = ['number']

    def __str__(self):
        return f"الحزب {self.number}"


class QuranPage(models.Model):
    """نموذج صفحة المصحف"""

    number = models.PositiveIntegerField(_('رقم الصفحة'), unique=True)
    juz = models.PositiveIntegerField(_('الجزء'))
    hizb = models.PositiveIntegerField(_('الحزب'))

    class Meta:
        verbose_name = _('صفحة')
        verbose_name_plural = _('الصفحات')
        ordering = ['number']

    def __str__(self):
        return f"الصفحة {self.number}"

    def get_ayat(self):
        """الحصول على آيات الصفحة"""
        return Ayah.objects.filter(page=self.number).order_by('surah__number', 'number')
