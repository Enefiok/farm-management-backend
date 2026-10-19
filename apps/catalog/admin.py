from django.contrib import admin
from .models import Item, Party

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'category', 'base_unit', 'is_stock_tracked')
    list_filter = ('category', 'farm')

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'party_type', 'phone')
    list_filter = ('party_type', 'farm')