"""
واجهات العرض (Views) لنظام النشر
Dashboard Views for Notification System
"""
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView, View, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from .models import (
    ScheduledNotification,
    NotificationTemplate,
    NotificationDispatchLog,
    NotificationAuditLog,
)
from .forms import (
    ScheduledNotificationForm,
    NotificationTemplateForm,
    QuickSendForm,
    NotificationFilterForm,
)
from .services import SchedulingService, NotificationDispatchService
from .tasks import send_scheduled_notification


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin للتحقق من أن المستخدم مشرف"""
    def test_func(self):
        return (
            self.request.user.is_authenticated and 
            (self.request.user.is_staff or 
             self.request.user.is_superuser or
             self.request.user.user_type == 'admin')
        )


# ==================== Calendar & Dashboard Views ====================

class NotificationCalendarView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """عرض التقويم"""
    template_name = 'notifications_system/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات
        context['stats'] = {
            'total': ScheduledNotification.objects.count(),
            'scheduled': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.SCHEDULED
            ).count(),
            'sent': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.SENT
            ).count(),
            'failed': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.FAILED
            ).count(),
        }
        
        # الإشعارات القادمة
        context['upcoming'] = ScheduledNotification.objects.filter(
            status=ScheduledNotification.Status.SCHEDULED,
            scheduled_datetime__gte=timezone.now()
        ).order_by('scheduled_datetime')[:5]
        
        return context


class NotificationCalendarDataView(LoginRequiredMixin, AdminRequiredMixin, View):
    """بيانات التقويم (JSON)"""
    
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        queryset = ScheduledNotification.objects.all()
        
        if start and end:
            queryset = queryset.filter(
                scheduled_datetime__date__range=[start, end]
            )
        
        events = []
        for notification in queryset:
            # تحديد اللون حسب الحالة
            color = self._get_event_color(notification)
            
            events.append({
                'id': str(notification.id),
                'title': notification.title,
                'start': notification.scheduled_datetime.isoformat(),
                'end': (notification.scheduled_datetime + timedelta(minutes=30)).isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'textColor': '#fff',
                'extendedProps': {
                    'type': notification.get_content_type_display(),
                    'status': notification.get_status_display(),
                    'target': notification.get_target_type_display(),
                },
                'url': reverse('notifications_system:detail', kwargs={'pk': notification.pk}),
            })
        
        return JsonResponse(events, safe=False)
    
    def _get_event_color(self, notification):
        colors = {
            ScheduledNotification.Status.DRAFT: '#6c757d',
            ScheduledNotification.Status.SCHEDULED: '#2563eb',
            ScheduledNotification.Status.SENDING: '#f59e0b',
            ScheduledNotification.Status.SENT: '#10b981',
            ScheduledNotification.Status.FAILED: '#ef4444',
            ScheduledNotification.Status.CANCELLED: '#94a3b8',
        }
        return colors.get(notification.status, '#6c757d')


# ==================== List Views ====================

class ScheduledNotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """قائمة الإشعارات المجدولة"""
    model = ScheduledNotification
    template_name = 'notifications_system/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # التصفية
        form = NotificationFilterForm(self.request.GET)
        if form.is_valid():
            data = form.cleaned_data
            
            if data.get('status'):
                queryset = queryset.filter(status=data['status'])
            
            if data.get('content_type'):
                queryset = queryset.filter(content_type=data['content_type'])
            
            if data.get('target_type'):
                queryset = queryset.filter(target_type=data['target_type'])
            
            if data.get('date_from'):
                queryset = queryset.filter(scheduled_datetime__date__gte=data['date_from'])
            
            if data.get('date_to'):
                queryset = queryset.filter(scheduled_datetime__date__lte=data['date_to'])
            
            if data.get('search'):
                queryset = queryset.filter(title__icontains=data['search'])
        
        return queryset.select_related(
            'template', 'target_halaqa', 'target_course', 'created_by'
        ).prefetch_related('target_users')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = NotificationFilterForm(self.request.GET or None)
        
        # إحصائيات
        context['stats'] = {
            'total': ScheduledNotification.objects.count(),
            'scheduled': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.SCHEDULED
            ).count(),
            'sent': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.SENT
            ).count(),
            'failed': ScheduledNotification.objects.filter(
                status=ScheduledNotification.Status.FAILED
            ).count(),
        }
        
        return context


# ==================== CRUD Views ====================

class ScheduledNotificationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """إنشاء إشعار جديد"""
    model = ScheduledNotification
    form_class = ScheduledNotificationForm
    template_name = 'notifications_system/form.html'
    success_url = reverse_lazy('notifications_system:list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # إنشاء سجل التدقيق
        NotificationAuditLog.objects.create(
            notification=self.object,
            user=self.request.user,
            action=NotificationAuditLog.ActionType.CREATED
        )
        
        # إذا كان متكرر، إنشاء النسخ الفرعية
        if self.object.recurrence_type != ScheduledNotification.RecurrenceType.ONE_TIME:
            from .tasks import generate_recurring_instances
            generate_recurring_instances.delay(str(self.object.id))
            messages.info(
                self.request,
                _('تم إنشاء الإشعار وسيتم إنشاء النسخ المتكررة')
            )
        else:
            messages.success(self.request, _('تم إنشاء الإشعار بنجاح'))
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إشعار جديد')
        context['action'] = _('إنشاء')
        return context


class ScheduledNotificationUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """تعديل إشعار"""
    model = ScheduledNotification
    form_class = ScheduledNotificationForm
    template_name = 'notifications_system/form.html'
    success_url = reverse_lazy('notifications_system:list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # تسجيل التغييرات
        old_instance = self.get_object()
        changes = {}
        
        for field in form.changed_data:
            old_value = getattr(old_instance, field)
            new_value = form.cleaned_data[field]
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
        
        response = super().form_valid(form)
        
        # إنشاء سجل التدقيق
        NotificationAuditLog.objects.create(
            notification=self.object,
            user=self.request.user,
            action=NotificationAuditLog.ActionType.UPDATED,
            changes=changes
        )
        
        messages.success(self.request, _('تم تحديث الإشعار بنجاح'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل إشعار')
        context['action'] = _('حفظ التغييرات')
        context['notification'] = self.get_object()
        return context


class ScheduledNotificationDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """عرض تفاصيل إشعار"""
    model = ScheduledNotification
    template_name = 'notifications_system/detail.html'
    context_object_name = 'notification'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notification = self.get_object()
        
        # سجلات الإرسال
        context['dispatch_logs'] = NotificationDispatchLog.objects.filter(
            notification=notification
        ).select_related('recipient').order_by('-created_at')[:50]
        
        # سجل التدقيق
        context['audit_logs'] = NotificationAuditLog.objects.filter(
            notification=notification
        ).select_related('user').order_by('-created_at')[:20]
        
        # النسخ الفرعية (للإشعارات المتكررة)
        if notification.recurrence_type != ScheduledNotification.RecurrenceType.ONE_TIME:
            context['child_notifications'] = notification.child_notifications.all().order_by(
                'scheduled_datetime'
            )
        
        return context


class ScheduledNotificationDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """حذف إشعار"""
    model = ScheduledNotification
    template_name = 'notifications_system/confirm_delete.html'
    success_url = reverse_lazy('notifications_system:list')
    
    def delete(self, request, *args, **kwargs):
        notification = self.get_object()
        
        # إنشاء سجل التدقيق قبل الحذف
        NotificationAuditLog.objects.create(
            notification=notification,
            user=request.user,
            action=NotificationAuditLog.ActionType.DELETED
        )
        
        messages.success(request, _('تم حذف الإشعار بنجاح'))
        return super().delete(request, *args, **kwargs)


# ==================== Action Views ====================

class SendNowView(LoginRequiredMixin, AdminRequiredMixin, View):
    """إرسال فوري"""
    
    def post(self, request, pk):
        notification = get_object_or_404(ScheduledNotification, pk=pk)
        
        if not notification.can_send_now:
            messages.error(request, _('لا يمكن إرسال هذا الإشعار حالياً'))
            return redirect('notifications_system:detail', pk=pk)
        
        # إرسال كمهمة Celery
        task = send_scheduled_notification.delay(str(notification.id), immediate=True)
        
        # إنشاء سجل التدقيق
        NotificationAuditLog.objects.create(
            notification=notification,
            user=request.user,
            action=NotificationAuditLog.ActionType.SENT
        )
        
        messages.success(
            request,
            _('تم بدء الإرسال الفوري. معرف المهمة: {task_id}').format(task_id=task.id)
        )
        return redirect('notifications_system:detail', pk=pk)


class ToggleStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تفعيل/تعطيل إشعار"""
    
    def post(self, request, pk):
        notification = get_object_or_404(ScheduledNotification, pk=pk)
        
        notification.is_enabled = not notification.is_enabled
        notification.save(update_fields=['is_enabled'])
        
        action = (
            NotificationAuditLog.ActionType.ENABLED 
            if notification.is_enabled 
            else NotificationAuditLog.ActionType.DISABLED
        )
        
        NotificationAuditLog.objects.create(
            notification=notification,
            user=request.user,
            action=action
        )
        
        status_text = _('مفعّل') if notification.is_enabled else _('معطّل')
        messages.success(request, _('تم {status} الإشعار').format(status=status_text))
        
        return redirect('notifications_system:list')


class CancelNotificationView(LoginRequiredMixin, AdminRequiredMixin, View):
    """إلغاء إشعار"""
    
    def post(self, request, pk):
        notification = get_object_or_404(ScheduledNotification, pk=pk)
        
        success = SchedulingService.cancel_notification(
            notification=notification,
            user=request.user,
            cancel_children=True
        )
        
        if success:
            messages.success(request, _('تم إلغاء الإشعار بنجاح'))
        else:
            messages.error(request, _('لا يمكن إلغاء هذا الإشعار'))
        
        return redirect('notifications_system:list')


class DuplicateNotificationView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تكرار إشعار"""
    
    def post(self, request, pk):
        notification = get_object_or_404(ScheduledNotification, pk=pk)
        
        new_notification = SchedulingService.duplicate_notification(
            notification=notification,
            user=request.user
        )
        
        messages.success(
            request,
            _('تم تكرار الإشعار. يمكنك تعديله الآن')
        )
        return redirect('notifications_system:update', pk=new_notification.pk)


# ==================== API Views ====================

class PreviewPayloadView(LoginRequiredMixin, AdminRequiredMixin, View):
    """معاينة حمولة البيانات"""
    
    def get(self, request, pk):
        notification = get_object_or_404(ScheduledNotification, pk=pk)
        
        from .services import PayloadBuilder
        from accounts.models import CustomUser
        
        # استخدام أول مستخدم كعينة
        sample_user = CustomUser.objects.filter(is_active=True).first()
        
        if not sample_user:
            return JsonResponse({'error': 'No active users found'}, status=400)
        
        payload = PayloadBuilder.build_payload(
            notification=notification,
            recipient=sample_user,
            lesson=notification.lesson,
            tafseer=notification.tafseer
        )
        
        return JsonResponse(payload, json_dumps_params={'ensure_ascii': False, 'indent': 2})


class GetTemplateContentView(LoginRequiredMixin, AdminRequiredMixin, View):
    """الحصول على محتوى قالب"""
    
    def get(self, request):
        template_id = request.GET.get('template_id')
        if not template_id:
            return JsonResponse({'error': 'Template ID required'}, status=400)
        
        try:
            template = NotificationTemplate.objects.get(id=template_id)
            return JsonResponse({
                'title_template': template.title_template,
                'message_template': template.message_template,
                'content_type': template.content_type,
                'available_variables': template.available_variables,
            })
        except NotificationTemplate.DoesNotExist:
            return JsonResponse({'error': 'Template not found'}, status=404)


# ==================== Template Management ====================

class TemplateListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """قائمة القوالب"""
    model = NotificationTemplate
    template_name = 'notifications_system/template_list.html'
    context_object_name = 'templates'


class TemplateCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """إنشاء قالب جديد"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications_system/template_form.html'
    success_url = reverse_lazy('notifications_system:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('تم إنشاء القالب بنجاح'))
        return super().form_valid(form)


class TemplateUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """تعديل قالب"""
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications_system/template_form.html'
    success_url = reverse_lazy('notifications_system:template_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('تم تحديث القالب بنجاح'))
        return super().form_valid(form)
