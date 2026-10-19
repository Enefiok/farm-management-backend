from django.contrib import admin
from .models import Purchase, Sale, Expense

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('farm', 'supplier', 'item', 'quantity', 'total_cost', 'event_date', 'classification')
    list_filter = ('classification', 'farm')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('farm', 'customer', 'item', 'quantity', 'total_amount', 'event_date', 'classification')
    list_filter = ('classification', 'farm')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('farm', 'category', 'amount', 'event_date', 'classification')
    list_filter = ('category', 'classification', 'farm')