from django.db import models
from apps.farms.models import Farm
from apps.catalog.models import Item, Party
from core.models import BaseModel

class Purchase(BaseModel):
    """Buying feed, medicine, equipment (SRS 5, 8.4)"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='purchases')
    supplier = models.ForeignKey(Party, on_delete=models.PROTECT, limit_choices_to={'party_type__in': ['SUPPLIER', 'BOTH']})
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_purchases'

class Sale(BaseModel):
    """Selling eggs, manure, culled hens (SRS 5, 8.3)"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sales')
    customer = models.ForeignKey(Party, on_delete=models.PROTECT, null=True, blank=True, limit_choices_to={'party_type__in': ['CUSTOMER', 'BOTH']})
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_sales'

class Expense(BaseModel):
    """Labour, transport, utilities (SRS 5, 8.5)"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='expenses')
    payee = models.ForeignKey(Party, on_delete=models.PROTECT, null=True, blank=True)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_expenses'