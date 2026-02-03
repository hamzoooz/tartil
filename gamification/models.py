"""
نماذج التلعيب (Gamification)
Gamification Models for Tartil
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Badge(models.Model):
    """نموذج الوسام/الشارة"""

    class BadgeType(models.TextChoices):
        MEMORIZATION = 'memorization', _('حفظ')
        ATTENDANCE = 'attendance', _('حضور')
        ACHIEVEMENT = 'achievement', _('إنجاز')
        SPECIAL = 'special', _('خاص')
        STREAK = 'streak', _('مواظبة')

    class BadgeLevel(models.TextChoices):
        BRONZE = 'bronze', _('برونزي')
        SILVER = 'silver', _('فضي')
        GOLD = 'gold', _('ذهبي')
        PLATINUM = 'platinum', _('بلاتيني')
        DIAMOND = 'diamond', _('ماسي')

    name = models.CharField(_('اسم الوسام'), max_length=100)
    name_english = models.CharField(_('الاسم بالإنجليزية'), max_length=100, blank=True)
    description = models.TextField(_('الوصف'))
    icon = models.CharField(_('أيقونة'), max_length=50, default='fa-medal')
    image = models.ImageField(_('صورة الوسام'), upload_to='badges/', blank=True, null=True)
    badge_type = models.CharField(
        _('نوع الوسام'),
        max_length=20,
        choices=BadgeType.choices,
        default=BadgeType.ACHIEVEMENT
    )
    level = models.CharField(
        _('مستوى الوسام'),
        max_length=20,
        choices=BadgeLevel.choices,
        default=BadgeLevel.BRONZE
    )
    points_reward = models.PositiveIntegerField(_('النقاط المكافأة'), default=0)
    criteria_type = models.CharField(_('نوع المعيار'), max_length=50, blank=True)
    criteria_value = models.PositiveIntegerField(_('قيمة المعيار'), default=0)
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        verbose_name = _('وسام')
        verbose_name_plural = _('الأوسمة')
        ordering = ['badge_type', 'level']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class StudentBadge(models.Model):
    """نموذج أوسمة الطالب"""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name=_('الطالب')
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='awarded_to',
        verbose_name=_('الوسام')
    )
    earned_date = models.DateTimeField(_('تاريخ الحصول'), auto_now_add=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('وسام طالب')
        verbose_name_plural = _('أوسمة الطلاب')
        unique_together = ['student', 'badge']
        ordering = ['-earned_date']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.badge.name}"


class PointsLog(models.Model):
    """سجل النقاط"""

    class PointsType(models.TextChoices):
        RECITATION = 'recitation', _('تسميع')
        ATTENDANCE = 'attendance', _('حضور')
        BADGE = 'badge', _('وسام')
        ACHIEVEMENT = 'achievement', _('إنجاز')
        BONUS = 'bonus', _('مكافأة')
        DEDUCTION = 'deduction', _('خصم')
        STREAK = 'streak', _('مواظبة')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_logs',
        verbose_name=_('الطالب')
    )
    points = models.IntegerField(_('النقاط'))
    points_type = models.CharField(
        _('نوع النقاط'),
        max_length=20,
        choices=PointsType.choices,
        default=PointsType.RECITATION
    )
    reason = models.CharField(_('السبب'), max_length=200)
    details = models.TextField(_('التفاصيل'), blank=True)
    created_at = models.DateTimeField(_('التاريخ'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل نقاط')
        verbose_name_plural = _('سجلات النقاط')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.points} نقطة"


class Streak(models.Model):
    """نموذج المواظبة المتتالية"""

    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='streak',
        verbose_name=_('الطالب')
    )
    current_streak = models.PositiveIntegerField(_('المواظبة الحالية'), default=0)
    longest_streak = models.PositiveIntegerField(_('أطول مواظبة'), default=0)
    last_activity_date = models.DateField(_('تاريخ آخر نشاط'), null=True, blank=True)
    total_active_days = models.PositiveIntegerField(_('إجمالي أيام النشاط'), default=0)

    class Meta:
        verbose_name = _('مواظبة')
        verbose_name_plural = _('سجلات المواظبة')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.current_streak} يوم"

    def update_streak(self, activity_date):
        """تحديث المواظبة"""
        from datetime import timedelta

        if self.last_activity_date:
            days_diff = (activity_date - self.last_activity_date).days

            if days_diff == 1:
                # استمرار المواظبة
                self.current_streak += 1
            elif days_diff > 1:
                # انقطاع المواظبة
                self.current_streak = 1
            # إذا كان نفس اليوم، لا نغير شيئاً
        else:
            self.current_streak = 1

        # تحديث أطول مواظبة
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = activity_date
        self.total_active_days += 1
        self.save()


class Achievement(models.Model):
    """نموذج الإنجازات"""

    class AchievementType(models.TextChoices):
        SURAH_COMPLETE = 'surah_complete', _('إتمام سورة')
        JUZ_COMPLETE = 'juz_complete', _('إتمام جزء')
        HIFZ_COMPLETE = 'hifz_complete', _('ختم القرآن')
        SESSIONS_COUNT = 'sessions_count', _('عدد الجلسات')
        PERFECT_GRADE = 'perfect_grade', _('درجة كاملة')
        STREAK_DAYS = 'streak_days', _('أيام مواظبة')

    name = models.CharField(_('اسم الإنجاز'), max_length=100)
    description = models.TextField(_('الوصف'))
    achievement_type = models.CharField(
        _('نوع الإنجاز'),
        max_length=30,
        choices=AchievementType.choices
    )
    icon = models.CharField(_('أيقونة'), max_length=50, default='fa-trophy')
    points_reward = models.PositiveIntegerField(_('النقاط المكافأة'), default=0)
    target_value = models.PositiveIntegerField(_('القيمة المستهدفة'), default=1)
    is_active = models.BooleanField(_('نشط'), default=True)

    class Meta:
        verbose_name = _('إنجاز')
        verbose_name_plural = _('الإنجازات')

    def __str__(self):
        return self.name


class StudentAchievement(models.Model):
    """نموذج إنجازات الطالب"""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements',
        verbose_name=_('الطالب')
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='achieved_by',
        verbose_name=_('الإنجاز')
    )
    progress = models.PositiveIntegerField(_('التقدم'), default=0)
    is_completed = models.BooleanField(_('مكتمل'), default=False)
    completed_date = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)

    class Meta:
        verbose_name = _('إنجاز طالب')
        verbose_name_plural = _('إنجازات الطلاب')
        unique_together = ['student', 'achievement']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.achievement.name}"

    @property
    def progress_percentage(self):
        if self.achievement.target_value > 0:
            return min(100, round((self.progress / self.achievement.target_value) * 100))
        return 0


class Leaderboard(models.Model):
    """نموذج لوحة المتصدرين"""

    class PeriodType(models.TextChoices):
        DAILY = 'daily', _('يومي')
        WEEKLY = 'weekly', _('أسبوعي')
        MONTHLY = 'monthly', _('شهري')
        ALL_TIME = 'all_time', _('الكل')

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name=_('الطالب')
    )
    period_type = models.CharField(
        _('نوع الفترة'),
        max_length=20,
        choices=PeriodType.choices
    )
    period_start = models.DateField(_('بداية الفترة'))
    period_end = models.DateField(_('نهاية الفترة'))
    total_points = models.PositiveIntegerField(_('إجمالي النقاط'), default=0)
    rank = models.PositiveIntegerField(_('الترتيب'), default=0)

    class Meta:
        verbose_name = _('متصدر')
        verbose_name_plural = _('لوحة المتصدرين')
        ordering = ['-period_start', 'rank']

    def __str__(self):
        return f"{self.student.get_full_name()} - المركز {self.rank}"
