from django.contrib import admin
from .models import Purchase, PurchaseLine, Sale, SaleLine, Expense

# --- Purchase Admin ---
class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 1

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'party', 'event_date', 'total_amount', 'classification', 'created_by']
    list_filter = ['classification', 'event_date']
    inlines = [PurchaseLineInline]

# --- Sale Admin ---
class SaleLineInline(admin.TabularInline):
    model = SaleLine
    extra = 1

class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'party', 'event_date', 'total_amount', 'classification', 'created_by']
    list_filter = ['classification', 'event_date']
    inlines = [SaleLineInline]

# --- Expense Admin ---
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['id', 'farm', 'party', 'category', 'amount', 'event_date', 'classification', 'created_by']
    list_filter = ['category', 'classification', 'event_date']

# Register the models
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Expense, ExpenseAdmin)