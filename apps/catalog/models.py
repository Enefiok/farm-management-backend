from django.db import models
from apps.farms.models import Farm

class Unit(models.Model):
    """
    Standard units of measurement (e.g., kg, bag, crate, egg, litre).
    """
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'catalog_units'
        ordering = ['name']

    def __str__(self):
        return self.name

class Item(models.Model):
    """
    Tracked material/product (Feed, Medicine, Eggs, Supplies).
    """
    class CategoryChoices(models.TextChoices):
        FEED = 'FEED', 'Feed'
        MEDICINE = 'MEDICINE', 'Medicine/Vaccine'
        EGG = 'EGG', 'Egg Product'
        SUPPLY = 'SUPPLY', 'General Supply'
        EQUIPMENT = 'EQUIPMENT', 'Equipment'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    base_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='base_items')
    is_stock_tracked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalog_items'
        unique_together = ('farm', 'name')

    def __str__(self):
        return f"{self.name} ({self.base_unit})"

class UnitConversion(models.Model):
    """
    Defines how a specific Item converts between units.
    Example: Item='Eggs', Unit='Crate', Factor=30.0 (1 Crate = 30 Eggs).
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='conversions')
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    factor = models.DecimalField(max_digits=10, decimal_places=4, help_text="How many base units equal 1 of this unit?")
    is_base = models.BooleanField(default=False, help_text="Check if this is the item's base unit (factor should be 1).")

    class Meta:
        db_table = 'catalog_unit_conversions'
        unique_together = ('item', 'unit')

    def __str__(self):
        return f"1 {self.unit} = {self.factor} {self.item.base_unit}"

class Party(models.Model):
    """
    Customers and Suppliers.
    """
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