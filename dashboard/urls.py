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
    
    # الإعدادات
    path('settings/', views.SystemSettingsView.as_view(), name='settings'),
    
    # API Endpoints
    path('api/stats/', views.GetStatsAPIView.as_view(), name='api_stats'),
    path('api/chart-data/', views.ChartDataAPIView.as_view(), name='api_chart_data'),
    path('api/bulk-action/', views.BulkActionView.as_view(), name='api_bulk_action'),
]
