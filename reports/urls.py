"""
Reports URLs
مسارات التقارير والشهادات
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # الصفحة الرئيسية للتقارير
    path('', views.student_report_list, name='index'),
    
    # تقاريري (للطالب)
    path('my-reports/', views.my_reports, name='my_reports'),
    
    # قوالب الشهادات
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/', views.template_preview, name='template_preview'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    
    # الشهادات
    path('certificates/', views.certificate_list, name='certificate_list'),
    path('certificates/create/', views.certificate_create, name='certificate_create'),
    path('certificates/<int:pk>/', views.certificate_view, name='certificate_view'),
    path('certificates/<int:pk>/download/', views.certificate_download, name='certificate_download'),
    path('certificates/<int:pk>/delete/', views.certificate_delete, name='certificate_delete'),
    
    # توليد شهادات بالجملة
    path('certificates/bulk-create/', views.bulk_certificate_create, name='bulk_certificate_create'),
    
    # تقارير الطلاب
    path('reports/', views.student_report_list, name='report_list'),
    path('reports/create/', views.student_report_create, name='report_create'),
    path('reports/<int:pk>/', views.student_report_view, name='report_view'),
    path('reports/<int:pk>/delete/', views.student_report_delete, name='report_delete'),
    
    # AJAX endpoints
    path('ajax/preview-certificate/', views.ajax_preview_certificate, name='ajax_preview_certificate'),
    path('ajax/get-student-stats/', views.ajax_get_student_stats, name='ajax_get_student_stats'),
]
