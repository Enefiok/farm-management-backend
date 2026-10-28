from django.db import models
from apps.farms.models import Farm
from apps.catalog.models import Item, Party
from core.models import BaseModel

class Purchase(BaseModel):
    """Buying items (Feed, Chicks, Equipment) from a Supplier."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='purchases')
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name='purchases', limit_choices_to={'type': 'SUPPLIER'})
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_purchases'
        ordering = ['-event_date']

    def __str__(self):
        return f"Purchase from {self.party.name} on {self.event_date}"

class PurchaseLine(models.Model):
    """Individual items within a Purchase."""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'transactions_purchase_lines'

class Sale(BaseModel):
    """Selling items (Eggs, Spent Hens) to a Customer."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sales')
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name='sales', limit_choices_to={'type': 'CUSTOMER'})
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_sales'
        ordering = ['-event_date']

    def __str__(self):
        return f"Sale to {self.party.name} on {self.event_date}"

class SaleLine(models.Model):
    """Individual items within a Sale."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'transactions_sale_lines'

class Expense(BaseModel):
    """Operational costs (Labor, Utilities, Transport)."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='expenses')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    category = models.CharField(max_length=100, help_text="e.g., Labor, Utilities, Transport")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_expenses'
        ordering = ['-event_date']

    def __str__(self):
        return f"Expense: {self.category} - {self.amount}"