from django.contrib import admin
from .models import Flock, ProductionRecord, FarmActivity

@admin.register(Flock)
class FlockAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'farm', 'arrival_date', 'initial_count')
    list_filter = ('farm',)

@admin.register(ProductionRecord)
class ProductionRecordAdmin(admin.ModelAdmin):
    list_display = ('farm', 'flock', 'item', 'quantity_saleable', 'event_date', 'classification', 'created_by')
    list_filter = ('classification', 'farm')

@admin.register(FarmActivity)
class FarmActivityAdmin(admin.ModelAdmin):
    list_display = ('farm', 'activity_type', 'flock', 'quantity', 'event_date', 'classification', 'created_by')
    list_filter = ('activity_type', 'classification', 'farm')