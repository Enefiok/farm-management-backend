from django.db import models
from apps.farms.models import Farm
from apps.catalog.models import Item, Party
from core.models import BaseModel

class Purchase(BaseModel):
    """Buying items (Feed, Chicks, Equipment) from a Supplier."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='purchases')
    party = models.ForeignKey(
        Party, 
        on_delete=models.PROTECT, 
        related_name='purchases', 
        limit_choices_to={'party_type': 'SUPPLIER'}
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # NEW: Receipt Status
    receipt_status = models.CharField(
        max_length=20, 
        choices=[('ORDERED', 'Ordered'), ('RECEIVED', 'Received')], 
        default='RECEIVED'
    )
    
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
    
    # NEW: Unit field to match SaleLine
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Bag, Crate, Bottle") 
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'transactions_purchase_lines'

class Sale(BaseModel):
    """Selling items (Eggs, Spent Hens) to a Customer."""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sales')
    party = models.ForeignKey(
        Party, 
        on_delete=models.PROTECT, 
        related_name='sales', 
        limit_choices_to={'party_type': 'CUSTOMER'}
    )
    
    # Discount and Payment Tracking Fields
    discount_type = models.CharField(
        max_length=10, 
        choices=[('PERCENT', 'Percentage'), ('FIXED', 'Fixed Amount')], 
        default='FIXED'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
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
    
    # NEW: Link this line to a specific flock (Optional - used for selling birds)
    flock = models.ForeignKey('operations.Flock', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Crate, Tray, Bag")
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
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_expenses'
        ordering = ['-event_date']

    def __str__(self):
        return f"Expense: {self.category} - {self.amount}"

class Payment(BaseModel):
    """
    Shared payment record linked to a Sale, Purchase, or Expense.
    Allows for partial payments and payment history tracking.
    """
    TRANSACTION_TYPES = [
        ('SALE', 'Sale'),
        ('PURCHASE', 'Purchase'),
        ('EXPENSE', 'Expense'),
    ]
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CARD', 'Card/POS'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='payments')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_id = models.PositiveIntegerField(help_text="ID of the Sale, Purchase, or Expense")
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    
    reference = models.CharField(max_length=100, blank=True, null=True, help_text="Receipt number, bank ref, etc.")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'transactions_payments'
        ordering = ['-event_date']

    def __str__(self):
        return f"Payment of {self.amount} for {self.transaction_type} #{self.transaction_id}"