"""
URLs for Advanced Admin Dashboard
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.DashboardHomeView.as_view(), name='index'),
    
    # إدارة المستخدمين
    path('users/', views.UserManagementView.as_view(), name='users_list'),
    
    # إدارة الحلقات
    path('halaqat/', views.HalaqatManagementView.as_view(), name='halaqat_list'),
    
    # إدارة التسميعات
    path('recitations/', views.RecitationsManagementView.as_view(), name='recitations_list'),
    
    # إدارة الحضور
    path('attendance/', views.AttendanceManagementView.as_view(), name='attendance_list'),
    
    # التقارير
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/export/', views.ReportExportView.as_view(), name='reports_export'),
    
    # الإعدادات
    path('settings/', views.SystemSettingsView.as_view(), name='settings'),
    
    # الرسائل
    path('messages/', views.MessagesInboxView.as_view(), name='messages_inbox'),
    path('messages/sent/', views.MessagesSentView.as_view(), name='messages_sent'),
    path('messages/compose/', views.MessageCreateView.as_view(), name='messages_compose'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='messages_detail'),
    
    # الإشعارات
    path('notifications/', views.NotificationsListView.as_view(), name='notifications_list'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification_mark_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='notifications_mark_all_read'),
    
    # التنبيهات
    path('alerts/', views.AlertsListView.as_view(), name='alerts_list'),
    path('alerts/<int:pk>/dismiss/', views.DismissAlertView.as_view(), name='alert_dismiss'),
    
    # استيراد Excel
    path('import/', views.ExcelImportView.as_view(), name='excel_import'),
    path('import/process/', views.ProcessExcelImportView.as_view(), name='excel_import_process'),
    path('import/template/<str:import_type>/', views.DownloadImportTemplateView.as_view(), name='excel_import_template'),
    path('import/job/<int:pk>/', views.ImportJobDetailView.as_view(), name='import_job_detail'),
    path('import/job/<int:job_id>/export-accounts/', views.ExportCreatedAccountsView.as_view(), name='export_created_accounts'),
    
    # API Endpoints
    path('api/stats/', views.GetStatsAPIView.as_view(), name='api_stats'),
    path('api/chart-data/', views.ChartDataAPIView.as_view(), name='api_chart_data'),
    path('api/bulk-action/', views.BulkActionView.as_view(), name='api_bulk_action'),
]
