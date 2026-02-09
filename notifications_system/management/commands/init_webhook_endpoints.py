"""
أمر إدارة: تهيئة نقاط نهاية Webhook
Management Command: Initialize Webhook Endpoints

Usage:
    python manage.py init_webhook_endpoints
"""
from django.core.management.base import BaseCommand
from notifications_system.models import WebhookEndpoint


class Command(BaseCommand):
    help = 'تهيئة نقاط نهاية Webhook الافتراضية'
    
    def handle(self, *args, **options):
        endpoints = [
            {
                'name': 'Aivo Production',
                'url': 'https://aivo.fun/webhook/qurancourses',
                'endpoint_type': WebhookEndpoint.EndpointType.PRIMARY,
                'is_active': True,
            },
            {
                'name': 'Aivo Test',
                'url': 'https://aivo.fun/webhook-test/qurancourses',
                'endpoint_type': WebhookEndpoint.EndpointType.TEST,
                'is_active': True,
            },
        ]
        
        created_count = 0
        
        for endpoint_data in endpoints:
            endpoint, created = WebhookEndpoint.objects.get_or_create(
                url=endpoint_data['url'],
                defaults=endpoint_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'تم إنشاء: {endpoint.name}')
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(f'موجود مسبقاً: {endpoint.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nتم إنشاء {created_count} نقطة نهاية جديدة')
        )
