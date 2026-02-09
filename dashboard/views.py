"""
Views for Advanced Admin Dashboard
"""
import json
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView, ListView, DetailView, View, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import (
    Count, Sum, Avg, Q, F, Case, When, IntegerField, 
    Value, CharField, DateField, DateTimeField
)
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.urls import reverse_lazy
from django.db import transaction

from accounts.models import CustomUser, StudentProfile, SheikhProfile, ActivityLog
from halaqat.models import Halaqa, Session, Attendance, HalaqaEnrollment
from recitation.models import RecitationRecord, RecitationError, MemorizationProgress
from courses.models import Curriculum, StudentCurriculum, ScheduledNotification
from gamification.models import Badge, PointsLog, Streak, Achievement
from reports.models import Certificate, StudentReport
from quran.models import Surah

from .models import (
    DashboardSettings, DashboardWidget, AdminActionLog,
    Message, Notification, Alert, ExcelImportJob
)

User = get_user_model()

# أسماء العشرة المبشرين بالجنة + 20 صحابي إضافي للحلقات
SAHABA_NAMES = [
    # العشرة المبشرون بالجنة
    ('أبو بكر الصديق', 'male'),
    ('عمر بن الخطاب', 'male'),
    ('عثمان بن عفان', 'male'),
    ('علي بن أبي طالب', 'male'),
    ('طلحة بن عبيد الله', 'male'),
    ('الزبير بن العوام', 'male'),
    ('عبد الرحمن بن عوف', 'male'),
    ('سعد بن أبي وقاص', 'male'),
    ('سعيد بن زيد', 'male'),
    ('أبو عبيدة بن الجراح', 'male'),
    # 20 صحابي إضافي
    ('خالد بن الوليد', 'male'),
    ('عمار بن ياسر', 'male'),
    ('بلال بن رباح', 'male'),
    ('سلمان الفارسي', 'male'),
    ('البراء بن مالك', 'male'),
    ('عبد الله بن مسعود', 'male'),
    ('أبو هريرة', 'male'),
    ('عبد الله بن عباس', 'male'),
    ('جابر بن عبد الله', 'male'),
    ('أنس بن مالك', 'male'),
    ('عبد الله بن الزبير', 'male'),
    ('القعقاع بن عمرو', 'male'),
    ('زيد بن ثابت', 'male'),
    ('أبو سعيد الخدري', 'male'),
    ('عبد الله بن عمر', 'male'),
    ('مصعب بن عمير', 'male'),
    ('حذيفة بن اليمان', 'male'),
    ('المقداد بن عمرو', 'male'),
    ('عمرو بن العاص', 'male'),
    ('أبو أيوب الأنصاري', 'male'),
]


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم مشرف"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.is_superuser or
            self.request.user.user_type == 'admin'
        )


class DashboardHomeView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """الصفحة الرئيسية للوحة التحكم"""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الإحصائيات الرئيسية
        context['stats'] = self.get_main_stats()
        
        # بيانات الرسوم البيانية
        context['charts_data'] = self.get_charts_data()
        
        # آخر الأنشطة
        context['recent_activities'] = self.get_recent_activities()
        
        # البيانات السريعة
        context['quick_stats'] = self.get_quick_stats()
        
        # إعدادات المستخدم
        context['settings'], _ = DashboardSettings.objects.get_or_create(
            user=self.request.user
        )
        
        return context
    
    def get_main_stats(self):
        """الحصول على الإحصائيات الرئيسية"""
        cache_key = 'dashboard_main_stats'
        stats = cache.get(cache_key)
        
        if stats is None:
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            stats = {
                'total_users': User.objects.count(),
                'total_students': User.objects.filter(user_type='student').count(),
                'total_sheikhs': User.objects.filter(user_type='sheikh').count(),
                'total_halaqat': Halaqa.objects.count(),
                'total_sessions': Session.objects.count(),
                'total_recitations': RecitationRecord.objects.count(),
                'total_certificates': Certificate.objects.count(),
                'total_points_distributed': PointsLog.objects.aggregate(
                    total=Sum('points')
                )['total'] or 0,
                
                # إحصائيات جديدة
                'new_users_today': User.objects.filter(date_joined__date=today).count(),
                'new_users_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
                'active_sessions_today': Session.objects.filter(date=today).count(),
                
                # متوسطات
                'avg_attendance': self.get_avg_attendance(),
                'avg_grade': RecitationRecord.objects.aggregate(
                    avg=Avg('grade')
                )['avg'] or 0,
            }
            cache.set(cache_key, stats, 300)  # كاش لمدة 5 دقائق
        
        return stats
    
    def get_avg_attendance(self):
        """حساب متوسط نسبة الحضور"""
        total = Attendance.objects.count()
        if total == 0:
            return 0
        present = Attendance.objects.filter(status='present').count()
        return round((present / total) * 100, 1)
    
    def get_charts_data(self):
        """بيانات الرسوم البيانية"""
        cache_key = 'dashboard_charts_data'
        data = cache.get(cache_key)
        
        if data is None:
            # بيانات التسجيل الشهري
            last_6_months = timezone.now() - timedelta(days=180)
            
            monthly_users = User.objects.filter(
                date_joined__gte=last_6_months
            ).annotate(
                month=TruncMonth('date_joined')
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
            
            # بيانات التسميع حسب النوع
            recitation_by_type = RecitationRecord.objects.values(
                'recitation_type'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # بيانات الحضور حسب الحالة
            attendance_by_status = Attendance.objects.values(
                'status'
            ).annotate(
                count=Count('id')
            ).order_by('-count')
            
            # توزيع الطلاب حسب المستوى
            students_by_level = StudentProfile.objects.annotate(
                level=Case(
                    When(total_memorized_juz__gte=30, then=Value('حافظ كامل')),
                    When(total_memorized_juz__gte=20, then=Value('متقدم')),
                    When(total_memorized_juz__gte=10, then=Value('متوسط')),
                    When(total_memorized_juz__gte=1, then=Value('مبتدئ')),
                    default=Value('جديد'),
                    output_field=CharField()
                )
            ).values('level').annotate(count=Count('id')).order_by('-count')
            
            data = {
                'monthly_users': list(monthly_users),
                'recitation_by_type': list(recitation_by_type),
                'attendance_by_status': list(attendance_by_status),
                'students_by_level': list(students_by_level),
            }
            cache.set(cache_key, data, 300)
        
        return data
    
    def get_recent_activities(self):
        """آخر الأنشطة"""
        return ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    def get_quick_stats(self):
        """إحصائيات سريعة"""
        today = timezone.now().date()
        
        return {
            'sessions_today': Session.objects.filter(date=today).count(),
            'pending_enrollments': HalaqaEnrollment.objects.filter(status='pending').count(),
            'new_recitations': RecitationRecord.objects.filter(created_at__date=today).count(),
            'pending_reports': StudentReport.objects.filter(
                created_at__date__gte=today - timedelta(days=7)
            ).count(),
        }


class UserManagementView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """إدارة المستخدمين"""
    template_name = 'dashboard/users/list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = User.objects.select_related(
            'student_profile', 'sheikh_profile'
        ).annotate(
            halaqat_count=Count('halaqa_enrollments', distinct=True),
            sessions_count=Count('attendances', distinct=True),
            recitations_count=Count('recitation_records', distinct=True)
        )
        
        # التصفية حسب نوع المستخدم
        user_type = self.request.GET.get('type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # التصفية حسب الحالة
        is_active = self.request.GET.get('active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # الترتيب
        ordering = self.request.GET.get('ordering', '-date_joined')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_types'] = User.UserType.choices
        context['current_filters'] = {
            'type': self.request.GET.get('type', ''),
            'active': self.request.GET.get('active', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        # إحصائيات
        context['stats'] = {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'students': User.objects.filter(user_type='student').count(),
            'sheikhs': User.objects.filter(user_type='sheikh').count(),
            'admins': User.objects.filter(user_type='admin').count(),
            'parents': User.objects.filter(user_type='parent').count(),
        }
        
        return context


class HalaqatManagementView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """إدارة الحلقات"""
    template_name = 'dashboard/halaqat/list.html'
    context_object_name = 'halaqat'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Halaqa.objects.select_related('sheikh', 'course').annotate(
            students_count=Count('enrollments', filter=Q(enrollments__status='active'), distinct=True),
            sessions_count=Count('sessions', distinct=True)
        )
        
        # التصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # التصفية حسب الشيخ
        sheikh_id = self.request.GET.get('sheikh')
        if sheikh_id:
            queryset = queryset.filter(sheikh_id=sheikh_id)
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sheikh__first_name__icontains=search) |
                Q(sheikh__last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sheikhs'] = User.objects.filter(user_type='sheikh', is_active=True)
        context['status_choices'] = Halaqa.HalaqaStatus.choices
        context['current_filters'] = self.request.GET.dict()
        
        # إحصائيات
        context['stats'] = {
            'total': Halaqa.objects.count(),
            'active': Halaqa.objects.filter(status='active').count(),
            'paused': Halaqa.objects.filter(status='paused').count(),
            'completed': Halaqa.objects.filter(status='completed').count(),
        }
        
        return context


class RecitationsManagementView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """إدارة التسميعات"""
    template_name = 'dashboard/recitations/list.html'
    context_object_name = 'recitations'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = RecitationRecord.objects.select_related(
            'student', 'session', 'session__halaqa', 'surah_start', 'surah_end'
        ).prefetch_related('errors')
        
        # التصفية حسب نوع التسميع
        rec_type = self.request.GET.get('type')
        if rec_type:
            queryset = queryset.filter(recitation_type=rec_type)
        
        # التصفية حسب الطالب
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # التصفية حسب الشيخ (عبر الجلسة)
        sheikh_id = self.request.GET.get('sheikh')
        if sheikh_id:
            queryset = queryset.filter(session__halaqa__sheikh_id=sheikh_id)
        
        # التصفية حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recitation_types'] = RecitationRecord.RecitationType.choices
        context['students'] = User.objects.filter(user_type='student', is_active=True)
        context['sheikhs'] = User.objects.filter(user_type='sheikh', is_active=True)
        context['current_filters'] = self.request.GET.dict()
        
        # إحصائيات
        today = timezone.now().date()
        context['stats'] = {
            'total': RecitationRecord.objects.count(),
            'today': RecitationRecord.objects.filter(created_at__date=today).count(),
            'new_memorization': RecitationRecord.objects.filter(recitation_type='new').count(),
            'review': RecitationRecord.objects.filter(recitation_type='review').count(),
            'avg_grade': RecitationRecord.objects.aggregate(avg=Avg('grade'))['avg'] or 0,
        }
        
        return context


class AttendanceManagementView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """إدارة الحضور"""
    template_name = 'dashboard/attendance/list.html'
    context_object_name = 'attendances'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related(
            'student', 'session', 'session__halaqa'
        )
        
        # التصفية حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # التصفية حسب الطالب
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # التصفية حسب الحلقة
        halaqa_id = self.request.GET.get('halaqa')
        if halaqa_id:
            queryset = queryset.filter(session__halaqa_id=halaqa_id)
        
        # التصفية حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(session__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(session__date__lte=date_to)
        
        return queryset.order_by('-session__date', '-session__start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Attendance.AttendanceStatus.choices
        context['students'] = User.objects.filter(user_type='student', is_active=True)
        context['halaqat'] = Halaqa.objects.filter(status='active')
        context['current_filters'] = self.request.GET.dict()
        
        # إحصائيات
        total = Attendance.objects.count()
        present = Attendance.objects.filter(status='present').count()
        context['stats'] = {
            'total': total,
            'present': present,
            'absent': Attendance.objects.filter(status='absent').count(),
            'late': Attendance.objects.filter(status='late').count(),
            'excused': Attendance.objects.filter(status='excused').count(),
            'attendance_rate': round((present / total * 100), 1) if total > 0 else 0,
        }
        
        return context


class ReportsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """التقارير الشاملة"""
    template_name = 'dashboard/reports/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # نوع التقرير
        report_type = self.request.GET.get('type', 'overview')
        context['report_type'] = report_type
        
        # نطاق التاريخ
        date_range = self.request.GET.get('range', 'month')
        start_date, end_date = self.get_date_range(date_range)
        
        context['date_range'] = date_range
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # جلب بيانات التقرير
        if report_type == 'overview':
            context['report_data'] = self.get_overview_report(start_date, end_date)
        elif report_type == 'students':
            context['report_data'] = self.get_students_report(start_date, end_date)
        elif report_type == 'halaqat':
            context['report_data'] = self.get_halaqat_report(start_date, end_date)
        elif report_type == 'recitations':
            context['report_data'] = self.get_recitations_report(start_date, end_date)
        
        return context
    
    def get_date_range(self, range_type):
        """حساب نطاق التاريخ"""
        today = timezone.now().date()
        
        if range_type == 'today':
            return today, today
        elif range_type == 'week':
            return today - timedelta(days=7), today
        elif range_type == 'month':
            return today - timedelta(days=30), today
        elif range_type == 'quarter':
            return today - timedelta(days=90), today
        elif range_type == 'year':
            return today - timedelta(days=365), today
        else:
            # تاريخ مخصص
            start = self.request.GET.get('start_date')
            end = self.request.GET.get('end_date')
            if start and end:
                return datetime.strptime(start, '%Y-%m-%d').date(), datetime.strptime(end, '%Y-%m-%d').date()
            return today - timedelta(days=30), today
    
    def get_overview_report(self, start_date, end_date):
        """تقرير عام"""
        # User growth by month (last 6 months)
        from django.db.models.functions import TruncMonth
        user_growth = User.objects.filter(
            date_joined__date__range=[start_date, end_date]
        ).annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Activity by day of week
        activity_by_day = Session.objects.filter(
            date__range=[start_date, end_date]
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')[:30]
        
        return {
            'new_users': User.objects.filter(date_joined__date__range=[start_date, end_date]).count(),
            'new_students': User.objects.filter(
                user_type='student', date_joined__date__range=[start_date, end_date]
            ).count(),
            'sessions_count': Session.objects.filter(date__range=[start_date, end_date]).count(),
            'recitations_count': RecitationRecord.objects.filter(
                created_at__date__range=[start_date, end_date]
            ).count(),
            'avg_grade': RecitationRecord.objects.filter(
                created_at__date__range=[start_date, end_date]
            ).aggregate(avg=Avg('grade'))['avg'] or 0,
            'total_attendance': Attendance.objects.filter(
                session__date__range=[start_date, end_date]
            ).count(),
            # Chart data
            'user_growth_labels': [u['month'].strftime('%Y-%m') for u in user_growth] if user_growth else [],
            'user_growth_data': [u['count'] for u in user_growth] if user_growth else [],
            'activity_labels': [a['date'].strftime('%m-%d') for a in activity_by_day] if activity_by_day else [],
            'activity_data': [a['count'] for a in activity_by_day] if activity_by_day else [],
        }
    
    def get_students_report(self, start_date, end_date):
        """تقرير الطلاب"""
        students = User.objects.filter(user_type='student').annotate(
            sessions_count=Count('attendances', filter=Q(attendances__session__date__range=[start_date, end_date])),
            recitations_count=Count('recitation_records', filter=Q(recitation_records__created_at__date__range=[start_date, end_date])),
            avg_grade=Avg('recitation_records__grade', filter=Q(recitation_records__created_at__date__range=[start_date, end_date])),
            total_pages=Sum('recitation_records__pages_count', filter=Q(recitation_records__created_at__date__range=[start_date, end_date]))
        ).order_by('-recitations_count')[:50]
        
        return {
            'students': students,
            'top_performers': students[:10],
        }
    
    def get_halaqat_report(self, start_date, end_date):
        """تقرير الحلقات"""
        halaqat = Halaqa.objects.annotate(
            sessions_count=Count('sessions', filter=Q(sessions__date__range=[start_date, end_date])),
            students_count=Count('enrollments', filter=Q(enrollments__status='active')),
            avg_attendance=Avg('sessions__attendances__status', 
                filter=Q(sessions__date__range=[start_date, end_date])),
        ).order_by('-sessions_count')
        
        return {
            'halaqat': halaqat,
        }
    
    def get_recitations_report(self, start_date, end_date):
        """تقرير التسميعات"""
        recitations = RecitationRecord.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).select_related('student', 'surah_start')
        
        by_surah = recitations.values('surah_start__name_arabic').annotate(
            count=Count('id'),
            avg_grade=Avg('grade')
        ).order_by('-count')
        
        by_grade = recitations.values('grade_level').annotate(
            count=Count('id')
        ).order_by('-count')
        
        errors_count = RecitationError.objects.filter(
            record__created_at__date__range=[start_date, end_date]
        ).count()
        
        total = recitations.count()
        error_percentage = (errors_count / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'by_surah': by_surah,
            'by_grade': by_grade,
            'errors_count': errors_count,
            'error_percentage': error_percentage,
        }


class SystemSettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """إعدادات النظام"""
    template_name = 'dashboard/settings/index.html'


# ==================== AJAX API Views ====================

class GetStatsAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API للحصول على الإحصائيات"""
    def get(self, request):
        stat_type = request.GET.get('type', 'all')
        
        if stat_type == 'users':
            data = self.get_users_stats()
        elif stat_type == 'halaqat':
            data = self.get_halaqat_stats()
        elif stat_type == 'recitations':
            data = self.get_recitations_stats()
        else:
            data = {
                'users': self.get_users_stats(),
                'halaqat': self.get_halaqat_stats(),
                'recitations': self.get_recitations_stats(),
            }
        
        return JsonResponse(data, safe=False)
    
    def get_users_stats(self):
        return {
            'total': User.objects.count(),
            'by_type': list(User.objects.values('user_type').annotate(count=Count('id'))),
            'recent': list(User.objects.order_by('-date_joined')[:5].values('first_name', 'last_name', 'date_joined')),
        }
    
    def get_halaqat_stats(self):
        return {
            'total': Halaqa.objects.count(),
            'by_status': list(Halaqa.objects.values('status').annotate(count=Count('id'))),
        }
    
    def get_recitations_stats(self):
        today = timezone.now().date()
        return {
            'total': RecitationRecord.objects.count(),
            'today': RecitationRecord.objects.filter(created_at__date=today).count(),
            'avg_grade': RecitationRecord.objects.aggregate(avg=Avg('grade'))['avg'] or 0,
        }


class BulkActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    """إجراء جماعي على الكائنات"""
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            model_name = data.get('model')
            action = data.get('action')
            ids = data.get('ids', [])
            params = data.get('params', {})
            
            # تنفيذ الإجراء
            result = self.execute_action(model_name, action, ids, params)
            
            # تسجيل الإجراء
            AdminActionLog.objects.create(
                user=request.user,
                action_type='bulk_' + action,
                model_name=model_name,
                changes={'ids': ids, 'params': params}
            )
            
            return JsonResponse({'success': True, 'result': result})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def execute_action(self, model_name, action, ids, params):
        """تنفيذ الإجراء الجماعي"""
        model_map = {
            'user': User,
            'halaqa': Halaqa,
            'session': Session,
            'recitation': RecitationRecord,
            'attendance': Attendance,
        }
        
        model = model_map.get(model_name)
        if not model:
            raise ValueError(f'Unknown model: {model_name}')
        
        queryset = model.objects.filter(id__in=ids)
        
        if action == 'delete':
            count = queryset.count()
            queryset.delete()
            return {'deleted': count}
        
        elif action == 'update':
            fields = params.get('fields', {})
            queryset.update(**fields)
            return {'updated': queryset.count()}
        
        elif action == 'change_status':
            new_status = params.get('status')
            queryset.update(status=new_status)
            return {'updated': queryset.count()}
        
        return {'message': 'Action completed'}


class ChartDataAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API لبيانات الرسوم البيانية"""
    def get(self, request):
        chart_type = request.GET.get('chart')
        period = request.GET.get('period', 'month')
        
        if chart_type == 'user_growth':
            data = self.get_user_growth_data(period)
        elif chart_type == 'recitation_progress':
            data = self.get_recitation_progress_data(period)
        elif chart_type == 'attendance_trend':
            data = self.get_attendance_trend_data(period)
        elif chart_type == 'grade_distribution':
            data = self.get_grade_distribution_data()
        else:
            data = {}
        
        return JsonResponse(data, safe=False)
    
    def get_user_growth_data(self, period):
        """بيانات نمو المستخدمين"""
        if period == 'week':
            days = 7
            trunc = TruncDate
        elif period == 'month':
            days = 30
            trunc = TruncDate
        else:
            days = 365
            trunc = TruncMonth
        
        start_date = timezone.now() - timedelta(days=days)
        
        data = User.objects.filter(
            date_joined__gte=start_date
        ).annotate(
            date=trunc('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return {
            'labels': [d['date'].strftime('%Y-%m-%d') for d in data],
            'data': [d['count'] for d in data],
        }
    
    def get_recitation_progress_data(self, period):
        """بيانات تقدم التسميع"""
        days = {'week': 7, 'month': 30, 'year': 365}.get(period, 30)
        start_date = timezone.now() - timedelta(days=days)
        
        data = RecitationRecord.objects.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            avg_grade=Avg('grade')
        ).order_by('date')
        
        return {
            'labels': [d['date'].strftime('%Y-%m-%d') for d in data],
            'count': [d['count'] for d in data],
            'grades': [round(d['avg_grade'] or 0, 1) for d in data],
        }
    
    def get_attendance_trend_data(self, period):
        """بيانات trend الحضور"""
        days = {'week': 7, 'month': 30, 'year': 365}.get(period, 30)
        start_date = timezone.now() - timedelta(days=days)
        
        data = Attendance.objects.filter(
            session__date__gte=start_date
        ).values('session__date', 'status').annotate(
            count=Count('id')
        ).order_by('session__date')
        
        return {
            'raw_data': list(data),
        }
    
    def get_grade_distribution_data(self):
        """توزيع الدرجات"""
        data = RecitationRecord.objects.values('grade_level').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'labels': [d['grade_level'] for d in data],
            'data': [d['count'] for d in data],
        }


# ==================== Messages Views ====================

class MessagesInboxView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """صندوق الوارد"""
    template_name = 'dashboard/messages/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        return Message.objects.filter(
            recipients=self.request.user,
            is_archived=False
        ).exclude(
            message_type=Message.MessageType.BROADCAST
        ).select_related('sender').prefetch_related('read_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Message.objects.filter(
            recipients=self.request.user
        ).exclude(read_by=self.request.user).count()
        context['sent_count'] = Message.objects.filter(sender=self.request.user).count()
        context['archived_count'] = Message.objects.filter(
            recipients=self.request.user, is_archived=True
        ).count()
        return context


class MessagesSentView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """الرسائل المرسلة"""
    template_name = 'dashboard/messages/sent.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        return Message.objects.filter(
            sender=self.request.user
        ).select_related('sender').prefetch_related('recipients', 'read_by')


class MessageDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """عرض رسالة"""
    model = Message
    template_name = 'dashboard/messages/detail.html'
    context_object_name = 'message'
    pk_url_kwarg = 'pk'
    
    def get_queryset(self):
        return Message.objects.filter(
            Q(recipients=self.request.user) | Q(sender=self.request.user)
        ).distinct()
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # تحديد كمقروءة
        if self.object.sender != request.user:
            self.object.mark_as_read(request.user)
        return response


class MessageCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """إنشاء رسالة جديدة"""
    model = Message
    template_name = 'dashboard/messages/compose.html'
    fields = ['recipients', 'subject', 'content', 'priority']
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        form.instance.message_type = Message.MessageType.DIRECT
        messages.success(self.request, _('تم إرسال الرسالة بنجاح'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('dashboard:messages_sent')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True).exclude(id=self.request.user.id)
        return context


# ==================== Notifications Views ====================

class NotificationsListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """قائمة الإشعارات"""
    template_name = 'dashboard/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # تصفية حسب النوع
        notif_type = self.request.GET.get('type')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)
        
        # تصفية حسب القراءة
        is_read = self.request.GET.get('read')
        if is_read == 'true':
            queryset = queryset.filter(is_read=True)
        elif is_read == 'false':
            queryset = queryset.filter(is_read=False)
        
        return queryset.select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        ).count()
        context['important_count'] = Notification.objects.filter(
            user=self.request.user, is_important=True
        ).count()
        context['notification_types'] = Notification.NotificationType.choices
        return context


class MarkNotificationReadView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تحديد إشعار كمقروء"""
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})


class MarkAllNotificationsReadView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تحديد كل الإشعارات كمقروءة"""
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return JsonResponse({'success': True, 'message': _('تم تحديد جميع الإشعارات كمقروءة')})


# ==================== Alerts Views ====================

class AlertsListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """قائمة التنبيهات"""
    template_name = 'dashboard/alerts/list.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return Alert.objects.filter(
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_count'] = Alert.objects.filter(is_active=True).count()
        return context


class DismissAlertView(LoginRequiredMixin, AdminRequiredMixin, View):
    """إغلاق تنبيه"""
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        alert.dismiss(request.user)
        return JsonResponse({'success': True})


# ==================== Excel Import Views ====================

class ExcelImportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """صفحة استيراد Excel"""
    template_name = 'dashboard/import/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_jobs'] = ExcelImportJob.objects.filter(
            created_by=self.request.user
        ).order_by('-created_at')[:10]
        context['sheikhs'] = User.objects.filter(user_type='sheikh', is_active=True)
        return context


class ProcessExcelImportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """معالجة استيراد Excel"""
    
    @method_decorator(require_POST)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            import pandas as pd
            import openpyxl
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': _('مكتبات pandas و openpyxl غير مثبتة')
            })
        
        if 'excel_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': _('لم يتم تحديد ملف')
            })
        
        excel_file = request.FILES['excel_file']
        import_type = request.POST.get('import_type', 'students')
        create_accounts = request.POST.get('create_accounts') == 'on'
        auto_distribute = request.POST.get('auto_distribute') == 'on'
        distribution_count = int(request.POST.get('distribution_count', 10))
        
        # إنشاء مهمة الاستيراد
        job = ExcelImportJob.objects.create(
            import_type=import_type,
            file_name=excel_file.name,
            file_path=excel_file,
            create_accounts=create_accounts,
            auto_distribute=auto_distribute,
            distribution_count=distribution_count,
            created_by=request.user,
            status=ExcelImportJob.Status.PROCESSING,
            started_at=timezone.now()
        )
        
        try:
            # قراءة ملف Excel
            df = pd.read_excel(job.file_path.path)
            job.total_rows = len(df)
            job.save()
            
            # معالجة حسب النوع
            if import_type == 'students':
                result = self.process_students_import(job, df, request)
            elif import_type == 'sheikhs':
                result = self.process_sheikhs_import(job, df, request)
            else:
                result = {'success': False, 'error': _('نوع استيراد غير معروف')}
            
            # تحديث حالة المهمة
            if result['success']:
                job.status = ExcelImportJob.Status.COMPLETED if result['failed'] == 0 else ExcelImportJob.Status.PARTIAL
                job.success_count = result['success_count']
                job.failed_count = result['failed']
                job.skipped_count = result['skipped']
                job.errors_log = result.get('errors', [])
                job.created_users = result.get('created_users', [])
                job.created_halaqat = result.get('created_halaqat', [])
            else:
                job.status = ExcelImportJob.Status.FAILED
                job.errors_log = [result['error']]
            
            job.completed_at = timezone.now()
            job.save()
            
            return JsonResponse({
                'success': True,
                'job_id': job.id,
                'message': _('تم الاستيراد بنجاح'),
                'result': {
                    'total': job.total_rows,
                    'success': job.success_count,
                    'failed': job.failed_count,
                    'skipped': job.skipped_count
                }
            })
            
        except Exception as e:
            job.status = ExcelImportJob.Status.FAILED
            job.errors_log = [str(e)]
            job.completed_at = timezone.now()
            job.save()
            
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def process_students_import(self, job, df, request):
        """معالجة استيراد الطلاب"""
        errors = []
        created_users = []
        created_halaqat = []
        success_count = 0
        failed = 0
        skipped = 0
        
        # التحقق من الأعمدة المطلوبة
        required_columns = ['name', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'success': False,
                'error': _('الأعمدة المفقودة: {}').format(', '.join(missing_columns))
            }
        
        # إنشاء الحلقات والمشايخ إذا كان التوزيع التلقائي مفعّل
        halaqat = []
        sheikhs = []
        
        if job.auto_distribute:
            halaqat = self.create_halaqat_for_distribution(job.distribution_count, request.user)
            created_halaqat = [{'id': h.id, 'name': h.name} for h in halaqat]
            sheikhs = list(User.objects.filter(user_type='sheikh', is_active=True))
            
            if len(sheikhs) == 0:
                return {
                    'success': False,
                    'error': _('لا يوجد مشايخ نشطون للتوزيع')
                }
        
        # معالجة كل صف
        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    name = str(row.get('name', '')).strip()
                    email = str(row.get('email', '')).strip().lower()
                    phone = str(row.get('phone', '')).strip()
                    
                    if not name or not email:
                        skipped += 1
                        continue
                    
                    # تقسيم الاسم
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # التحقق من وجود المستخدم
                    if User.objects.filter(email=email).exists():
                        user = User.objects.get(email=email)
                        created = False
                    elif User.objects.filter(username=email).exists():
                        user = User.objects.get(username=email)
                        created = False
                    else:
                        if not job.create_accounts:
                            skipped += 1
                            continue
                        
                        # إنشاء مستخدم جديد
                        username = self.generate_username(first_name, last_name)
                        password = self.generate_password()
                        
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                            phone=phone,
                            user_type='student'
                        )
                        
                        # إنشاء ملف الطالب
                        StudentProfile.objects.create(user=user)
                        
                        created = True
                        created_users.append({
                            'id': user.id,
                            'name': name,
                            'username': username,
                            'password': password,
                            'email': email
                        })
                    
                    # التوزيع التلقائي على الحلقات
                    if job.auto_distribute and halaqat:
                        halaqa_index = (success_count + failed) % len(halaqat)
                        halaqa = halaqat[halaqa_index]
                        
                        # التحقق من عدم وجود تسجيل سابق
                        if not HalaqaEnrollment.objects.filter(student=user, halaqa=halaqa).exists():
                            HalaqaEnrollment.objects.create(
                                student=user,
                                halaqa=halaqa,
                                status='active'
                            )
                    
                    success_count += 1
                    
            except Exception as e:
                failed += 1
                errors.append({
                    'row': index + 2,
                    'name': name if 'name' in locals() else 'Unknown',
                    'error': str(e)
                })
        
        return {
            'success': True,
            'success_count': success_count,
            'failed': failed,
            'skipped': skipped,
            'errors': errors[:50],  # أول 50 خطأ فقط
            'created_users': created_users,
            'created_halaqat': created_halaqat
        }
    
    def process_sheikhs_import(self, job, df, request):
        """معالجة استيراد المشايخ"""
        errors = []
        created_users = []
        success_count = 0
        failed = 0
        skipped = 0
        
        # التحقق من الأعمدة المطلوبة
        required_columns = ['name', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'success': False,
                'error': _('الأعمدة المفقودة: {}').format(', '.join(missing_columns))
            }
        
        # معالجة كل صف
        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    name = str(row.get('name', '')).strip()
                    email = str(row.get('email', '')).strip().lower()
                    phone = str(row.get('phone', '')).strip()
                    specialization = str(row.get('specialization', 'hifz')).strip()
                    experience = int(row.get('experience', 0)) if pd.notna(row.get('experience')) else 0
                    
                    if not name or not email:
                        skipped += 1
                        continue
                    
                    # تقسيم الاسم
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    # التحقق من وجود المستخدم
                    if User.objects.filter(email=email).exists():
                        skipped += 1
                        continue
                    
                    if not job.create_accounts:
                        skipped += 1
                        continue
                    
                    # إنشاء مستخدم جديد
                    username = self.generate_username(first_name, last_name)
                    password = self.generate_password()
                    
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        user_type='sheikh'
                    )
                    
                    # إنشاء ملف الشيخ
                    SheikhProfile.objects.create(
                        user=user,
                        specialization=specialization if specialization in ['hifz', 'tajweed', 'qiraat', 'ijazah'] else 'hifz',
                        years_of_experience=experience
                    )
                    
                    created_users.append({
                        'id': user.id,
                        'name': name,
                        'username': username,
                        'password': password,
                        'email': email
                    })
                    
                    success_count += 1
                    
            except Exception as e:
                failed += 1
                errors.append({
                    'row': index + 2,
                    'name': name if 'name' in locals() else 'Unknown',
                    'error': str(e)
                })
        
        return {
            'success': True,
            'success_count': success_count,
            'failed': failed,
            'skipped': skipped,
            'errors': errors[:50],
            'created_users': created_users
        }
    
    def create_halaqat_for_distribution(self, count, created_by):
        """إنشاء حلقات للتوزيع"""
        halaqat = []
        
        # الحصول على المشايخ النشطين
        sheikhs = list(User.objects.filter(user_type='sheikh', is_active=True))
        
        if not sheikhs:
            raise ValueError(_('لا يوجد مشايخ نشطون'))
        
        # التأكد من عدم تجاوز عدد الحلقات المتاح
        count = min(count, len(SAHABA_NAMES))
        
        for i in range(count):
            sahaba_name, gender = SAHABA_NAMES[i]
            sheikh = sheikhs[i % len(sheikhs)]
            
            # إنشاء اسم الحلقة
            halaqa_name = f"حلقة {sahaba_name}"
            
            # التحقق من عدم وجود حلقة بنفس الاسم
            if Halaqa.objects.filter(name=halaqa_name).exists():
                halaqa = Halaqa.objects.get(name=halaqa_name)
            else:
                halaqa = Halaqa.objects.create(
                    name=halaqa_name,
                    sheikh=sheikh,
                    max_students=10,
                    description=f"حلقة تسمية باسم الصحابي الجليل {sahaba_name} - من العشرة المبشرين بالجنة أو من الصحابة المبجلون"
                )
            
            halaqat.append(halaqa)
        
        return halaqat
    
    def generate_username(self, first_name, last_name):
        """توليد اسم مستخدم فريد"""
        base = f"{first_name.lower()}{last_name.lower()}".replace(' ', '')[:15]
        username = base
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        
        return username
    
    def generate_password(self):
        """توليد كلمة مرور عشوائية"""
        # كلمة مرور من 8 أحرف تتضمن أرقام وحروف
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(10))


class DownloadImportTemplateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تحميل قالب Excel للاستيراد"""
    
    def get(self, request, import_type):
        try:
            import pandas as pd
            from io import BytesIO
        except ImportError:
            return HttpResponse(_('مكتبة pandas غير مثبتة'), status=500)
        
        if import_type == 'students':
            # إنشاء قالب للطلاب
            data = {
                'name': ['محمد أحمد', 'عبد الله خالد', 'أحمد علي'],
                'email': ['student1@example.com', 'student2@example.com', 'student3@example.com'],
                'phone': ['0500000001', '0500000002', '0500000003']
            }
            filename = 'students_import_template.xlsx'
        elif import_type == 'sheikhs':
            # إنشاء قالب للمشايخ
            data = {
                'name': ['الشيخ محمد', 'الشيخ عبد الله'],
                'email': ['sheikh1@example.com', 'sheikh2@example.com'],
                'phone': ['0500000001', '0500000002'],
                'specialization': ['hifz', 'tajweed'],
                'experience': [5, 10]
            }
            filename = 'sheikhs_import_template.xlsx'
        else:
            return HttpResponse(_('نوع غير معروف'), status=400)
        
        df = pd.DataFrame(data)
        
        # إنشاء ملف Excel في الذاكرة
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # إضافة تعليمات في ورقة منفصلة
            instructions = pd.DataFrame({
                'field': ['name', 'email', 'phone', 'specialization', 'experience'],
                'description': [
                    'الاسم الكامل (مطلوب)',
                    'البريد الإلكتروني (مطلوب)',
                    'رقم الهاتف (اختياري)',
                    'التخصص: hifz, tajweed, qiraat, ijazah (للمشايخ)',
                    'سنوات الخبرة (للمشايخ)'
                ],
                'required': ['نعم', 'نعم', 'لا', 'لا', 'لا']
            })
            instructions.to_excel(writer, index=False, sheet_name='Instructions')
        
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ImportJobDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """عرض تفاصيل مهمة الاستيراد"""
    model = ExcelImportJob
    template_name = 'dashboard/import/detail.html'
    context_object_name = 'job'
    pk_url_kwarg = 'pk'
    
    def get_queryset(self):
        return ExcelImportJob.objects.filter(created_by=self.request.user)


class ExportCreatedAccountsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تصدير الحسابات المنشأة"""
    
    def get(self, request, job_id):
        try:
            import pandas as pd
            from io import BytesIO
        except ImportError:
            return HttpResponse(_('مكتبة pandas غير مثبتة'), status=500)
        
        job = get_object_or_404(ExcelImportJob, id=job_id, created_by=request.user)
        
        if not job.created_users:
            return HttpResponse(_('لا توجد حسابات منشأة'), status=404)
        
        df = pd.DataFrame(job.created_users)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Accounts')
        
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="created_accounts_{job_id}.xlsx"'
        return response



class ReportExportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تصدير التقارير بصيغة Excel"""
    
    def get(self, request):
        try:
            import pandas as pd
            from io import BytesIO
        except ImportError:
            return HttpResponse(_('مكتبة pandas غير مثبتة'), status=500)
        
        report_type = request.GET.get('type', 'overview')
        date_range = request.GET.get('range', 'month')
        
        # حساب نطاق التاريخ
        today = timezone.now().date()
        if date_range == 'today':
            start_date, end_date = today, today
        elif date_range == 'week':
            start_date, end_date = today - timedelta(days=7), today
        elif date_range == 'month':
            start_date, end_date = today - timedelta(days=30), today
        elif date_range == 'quarter':
            start_date, end_date = today - timedelta(days=90), today
        elif date_range == 'year':
            start_date, end_date = today - timedelta(days=365), today
        else:
            start = request.GET.get('start_date')
            end = request.GET.get('end_date')
            if start and end:
                start_date = datetime.strptime(start, '%Y-%m-%d').date()
                end_date = datetime.strptime(end, '%Y-%m-%d').date()
            else:
                start_date, end_date = today - timedelta(days=30), today
        
        # إنشاء ملف Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            if report_type == 'overview':
                self._export_overview(writer, start_date, end_date)
            elif report_type == 'students':
                self._export_students(writer, start_date, end_date)
            elif report_type == 'halaqat':
                self._export_halaqat(writer, start_date, end_date)
            elif report_type == 'recitations':
                self._export_recitations(writer, start_date, end_date)
            else:
                self._export_overview(writer, start_date, end_date)
        
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{start_date}.xlsx"'
        return response
    
    def _export_overview(self, writer, start_date, end_date):
        """تصدير نظرة عامة"""
        import pandas as pd
        
        data = {
            'المعيار': [
                'مستخدمين جدد',
                'طلاب جدد',
                'جلسات منعقدة',
                'تسميعات',
                'متوسط الدرجات',
                'سجلات حضور'
            ],
            'القيمة': [
                User.objects.filter(date_joined__date__range=[start_date, end_date]).count(),
                User.objects.filter(user_type='student', date_joined__date__range=[start_date, end_date]).count(),
                Session.objects.filter(date__range=[start_date, end_date]).count(),
                RecitationRecord.objects.filter(created_at__date__range=[start_date, end_date]).count(),
                round(RecitationRecord.objects.filter(created_at__date__range=[start_date, end_date]).aggregate(avg=Avg('grade'))['avg'] or 0, 2),
                Attendance.objects.filter(session__date__range=[start_date, end_date]).count()
            ]
        }
        
        df = pd.DataFrame(data)
        df.to_excel(writer, index=False, sheet_name='Overview')
    
    def _export_students(self, writer, start_date, end_date):
        """تصدير بيانات الطلاب"""
        import pandas as pd
        
        students = User.objects.filter(user_type='student').annotate(
            sessions_count=Count('attendances', filter=Q(attendances__session__date__range=[start_date, end_date])),
            recitations_count=Count('recitation_records', filter=Q(recitation_records__created_at__date__range=[start_date, end_date])),
            avg_grade=Avg('recitation_records__grade', filter=Q(recitation_records__created_at__date__range=[start_date, end_date])),
            total_pages=Sum('recitation_records__pages_count', filter=Q(recitation_records__created_at__date__range=[start_date, end_date]))
        ).order_by('-recitations_count')
        
        data = []
        for student in students:
            data.append({
                'الاسم': student.get_full_name() or student.username,
                'اسم المستخدم': student.username,
                'البريد': student.email,
                'الجلسات': student.sessions_count,
                'التسميعات': student.recitations_count,
                'متوسط الدرجة': round(student.avg_grade or 0, 2),
                'الصفحات': student.total_pages or 0
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, index=False, sheet_name='Students')
    
    def _export_halaqat(self, writer, start_date, end_date):
        """تصدير بيانات الحلقات"""
        import pandas as pd
        
        halaqat = Halaqa.objects.annotate(
            sessions_count=Count('sessions', filter=Q(sessions__date__range=[start_date, end_date])),
            students_count=Count('enrollments', filter=Q(enrollments__status='active'))
        ).order_by('-sessions_count')
        
        data = []
        for halaqa in halaqat:
            data.append({
                'اسم الحلقة': halaqa.name,
                'الشيخ': halaqa.sheikh.get_full_name() if halaqa.sheikh else '-',
                'عدد الطلاب': halaqa.students_count,
                'الجلسات': halaqa.sessions_count,
                'الحالة': halaqa.get_status_display()
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, index=False, sheet_name='Halaqat')
    
    def _export_recitations(self, writer, start_date, end_date):
        """تصدير بيانات التسميعات"""
        import pandas as pd
        
        recitations = RecitationRecord.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).select_related('student', 'surah_start')
        
        data = []
        for rec in recitations:
            data.append({
                'الطالب': rec.student.get_full_name() if rec.student else '-',
                'السورة': rec.surah_start.name_arabic if rec.surah_start else '-',
                'النوع': rec.get_recitation_type_display(),
                'الدرجة': rec.grade,
                'التاريخ': rec.created_at.strftime('%Y-%m-%d')
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, index=False, sheet_name='Recitations')
