from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'  # This tells Django it's inside the apps folder
    label = 'audit'      # This is the short name used for migrations