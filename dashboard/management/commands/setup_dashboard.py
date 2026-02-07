"""
Management command to set up default dashboard widgets and layouts
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dashboard.models import DashboardWidget, DashboardLayout, DashboardLayoutWidget

User = get_user_model()


class Command(BaseCommand):
    help = 'Create default dashboard widgets and layouts'

    def handle(self, *args, **options):
        self.stdout.write('Creating default dashboard widgets...')
        
        # Create default widgets
        widgets = [
            {
                'name': 'total_users',
                'widget_type': 'stats_card',
                'data_source': 'users',
                'title': 'إجمالي المستخدمين',
                'icon': 'fa-users',
                'color': 'primary',
                'width': 3,
                'order': 1,
                'is_default': True
            },
            {
                'name': 'total_students',
                'widget_type': 'stats_card',
                'data_source': 'students',
                'title': 'الطلاب',
                'icon': 'fa-user-graduate',
                'color': 'success',
                'width': 3,
                'order': 2,
                'is_default': True
            },
            {
                'name': 'total_sheikhs',
                'widget_type': 'stats_card',
                'data_source': 'sheikhs',
                'title': 'المشايخ',
                'icon': 'fa-chalkboard-teacher',
                'color': 'warning',
                'width': 3,
                'order': 3,
                'is_default': True
            },
            {
                'name': 'total_recitations',
                'widget_type': 'stats_card',
                'data_source': 'recitations',
                'title': 'التسميعات',
                'icon': 'fa-microphone-alt',
                'color': 'info',
                'width': 3,
                'order': 4,
                'is_default': True
            },
            {
                'name': 'user_growth_chart',
                'widget_type': 'chart_line',
                'data_source': 'users',
                'title': 'نمو المستخدمين',
                'subtitle': 'آخر 6 أشهر',
                'icon': 'fa-chart-line',
                'color': 'primary',
                'width': 8,
                'order': 5,
                'is_default': True
            },
            {
                'name': 'recitation_types',
                'widget_type': 'chart_doughnut',
                'data_source': 'recitations',
                'title': 'توزيع التسميع',
                'icon': 'fa-chart-pie',
                'color': 'warning',
                'width': 4,
                'order': 6,
                'is_default': True
            },
            {
                'name': 'recent_activity',
                'widget_type': 'recent_activity',
                'data_source': 'users',
                'title': 'آخر النشاطات',
                'icon': 'fa-history',
                'color': 'secondary',
                'width': 6,
                'order': 7,
                'is_default': True
            },
            {
                'name': 'attendance_status',
                'widget_type': 'chart_bar',
                'data_source': 'attendance',
                'title': 'حالة الحضور',
                'icon': 'fa-clipboard-check',
                'color': 'success',
                'width': 6,
                'order': 8,
                'is_default': True
            },
        ]
        
        for widget_data in widgets:
            widget, created = DashboardWidget.objects.get_or_create(
                name=widget_data['name'],
                defaults=widget_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created widget: {widget.name}'))
            else:
                self.stdout.write(f'Widget already exists: {widget.name}')
        
        # Create default system layout
        layout, created = DashboardLayout.objects.get_or_create(
            name='التخطيط الافتراضي',
            is_system=True,
            defaults={
                'description': 'التخطيط الافتراضي للوحة التحكم',
                'is_default': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created layout: {layout.name}'))
            # Add widgets to layout
            for widget in DashboardWidget.objects.filter(is_default=True):
                DashboardLayoutWidget.objects.create(
                    layout=layout,
                    widget=widget,
                    custom_order=widget.order
                )
        
        self.stdout.write(self.style.SUCCESS('Dashboard setup completed successfully!'))
