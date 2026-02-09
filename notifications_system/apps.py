from django.apps import AppConfig


class NotificationsSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications_system'
    verbose_name = 'نظام النشر والتنبيهات'
    
    def ready(self):
        import notifications_system.signals
