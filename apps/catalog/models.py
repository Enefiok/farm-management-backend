from django.db import models
from apps.farms.models import Farm

class Item(models.Model):
    """Feed, medicine, eggs, supplies (SRS 5, 6, 8.4)"""
    class CategoryChoices(models.TextChoices):
        FEED = 'FEED', 'Feed'
        MEDICINE = 'MEDICINE', 'Medicine/Vaccine'
        EGG = 'EGG', 'Egg Product'
        SUPPLY = 'SUPPLY', 'General Supply'
        EQUIPMENT = 'EQUIPMENT', 'Equipment'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    base_unit = models.CharField(max_length=50, help_text="e.g., 'bag', 'crate', 'piece'")
    is_stock_tracked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalog_items'
        unique_together = ('farm', 'name')

    def __str__(self):
        return f"{self.name} ({self.base_unit})"

class Party(models.Model):
    """Customers and Suppliers (SRS 6, 8.3, 8.4)"""
    class TypeChoices(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        SUPPLIER = 'SUPPLIER', 'Supplier'
        BOTH = 'BOTH', 'Both'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='parties')
    name = models.CharField(max_length=255)
    party_type = models.CharField(max_length=10, choices=TypeChoices.choices)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalog_parties'

    def __str__(self):
        return self.name