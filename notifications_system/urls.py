"""
مسارات URL لنظام النشر
URL Routes for Notification System
"""
from django.urls import path
from . import views

app_name = 'notifications_system'

urlpatterns = [
    # التقويم
    path('', views.NotificationCalendarView.as_view(), name='calendar'),
    path('calendar/', views.NotificationCalendarView.as_view(), name='calendar_view'),
    path('calendar/data/', views.NotificationCalendarDataView.as_view(), name='calendar_data'),
    
    # قائمة الإشعارات
    path('list/', views.ScheduledNotificationListView.as_view(), name='list'),
    
    # CRUD
    path('create/', views.ScheduledNotificationCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.ScheduledNotificationDetailView.as_view(), name='detail'),
    path('<uuid:pk>/update/', views.ScheduledNotificationUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.ScheduledNotificationDeleteView.as_view(), name='delete'),
    
    # Actions
    path('<uuid:pk>/send-now/', views.SendNowView.as_view(), name='send_now'),
    path('<uuid:pk>/toggle/', views.ToggleStatusView.as_view(), name='toggle'),
    path('<uuid:pk>/cancel/', views.CancelNotificationView.as_view(), name='cancel'),
    path('<uuid:pk>/duplicate/', views.DuplicateNotificationView.as_view(), name='duplicate'),
    
    # API
    path('<uuid:pk>/preview-payload/', views.PreviewPayloadView.as_view(), name='preview_payload'),
    path('api/template-content/', views.GetTemplateContentView.as_view(), name='template_content'),
    
    # Templates
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/update/', views.TemplateUpdateView.as_view(), name='template_update'),
]
