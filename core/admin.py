from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('actor', 'farm', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('actor', 'farm', 'action', 'details', 'timestamp')