from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        """Configure Celery Beat schedule when the app starts."""
        from django.conf import settings
        from celery import current_app

        current_app.conf.beat_schedule = {
            # Scan the blockchain every 15 seconds
            'scan-usdc-every-15s': {
                'task': 'monitor.tasks.scan_usdc_transfers',
                'schedule': 15.0,
            },
        }
