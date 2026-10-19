from django.db import models
from apps.farms.models import Farm
from apps.catalog.models import Item
from core.models import BaseModel

class Flock(models.Model):
    """A distinct group of birds (SRS 5, 8.2)"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='flocks')
    identifier = models.CharField(max_length=50, help_text="e.g., 'Flock A', 'Batch 2026-1'")
    breed = models.CharField(max_length=100, blank=True, null=True)
    arrival_date = models.DateField()
    initial_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'operations_flocks'
        unique_together = ('farm', 'identifier')

    def __str__(self):
        return self.identifier

class ProductionRecord(BaseModel):
    """Egg collection (SRS 5, 8.6)"""
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='production_records')
    flock = models.ForeignKey(Flock, on_delete=models.SET_NULL, null=True, blank=True, related_name='production_records')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, limit_choices_to={'category': 'EGG'})
    quantity_collected = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_damaged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_saleable = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'operations_production'

class FarmActivity(BaseModel):
    """Feed consumption, mortality, vaccination, loss (SRS 5, 8.7)"""
    class ActivityTypeChoices(models.TextChoices):
        FEED_CONSUMPTION = 'FEED_CONSUMPTION', 'Feed Consumption'
        MORTALITY = 'MORTALITY', 'Mortality'
        VACCINATION = 'VACCINATION', 'Vaccination/Medication'
        FLOCK_CHANGE = 'FLOCK_CHANGE', 'Flock Change'
        LOSS = 'LOSS', 'Loss/Spoilage'
        OTHER = 'OTHER', 'Other'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='activities')
    flock = models.ForeignKey(Flock, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ActivityTypeChoices.choices)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'operations_activities'