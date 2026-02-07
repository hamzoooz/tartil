"""
Views for Advanced Admin Dashboard
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView, View
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

from accounts.models import CustomUser, StudentProfile, SheikhProfile, ActivityLog
from halaqat.models import Halaqa, Session, Attendance, HalaqaEnrollment
from recitation.models import RecitationRecord, RecitationError, MemorizationProgress
from courses.models import Curriculum, StudentCurriculum, ScheduledNotification
from gamification.models import Badge, PointsLog, Streak, Achievement
from reports.models import Certificate, StudentReport
from quran.models import Surah

from .models import DashboardSettings, DashboardWidget, AdminActionLog

User = get_user_model()


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
        
        return {
            'total': recitations.count(),
            'by_surah': by_surah,
            'by_grade': by_grade,
            'errors_count': RecitationError.objects.filter(
                record__created_at__date__range=[start_date, end_date]
            ).count(),
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
