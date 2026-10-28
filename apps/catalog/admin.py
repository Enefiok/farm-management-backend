from django.contrib import admin
from .models import Unit, Item, UnitConversion, Party

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'category', 'base_unit', 'is_stock_tracked')
    list_filter = ('category', 'farm')

@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ('item', 'unit', 'factor', 'is_base')
    list_filter = ('item',)

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'farm', 'party_type', 'phone')
    list_filter = ('party_type', 'farm')