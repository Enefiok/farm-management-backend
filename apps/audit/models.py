from django.db import models
from apps.farms.models import Farm
from core.models import BaseModel

class Adjustment(BaseModel):
    """
    Records a correction or real-world loss against an existing record.
    Per SRS Section 10: One shared workflow, reason-dependent, fully auditable.
    """
    class ReasonChoices(models.TextChoices):
        MISTAKE = 'MISTAKE', 'Data-entry mistake'
        LOSS = 'LOSS', 'Damage/Spoilage/Disaster'
        DISCREPANCY = 'DISCREPANCY', 'Count/Stock discrepancy'
        THEFT = 'THEFT', 'Theft/Loss'
        OTHER = 'OTHER', 'Other'

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='adjustments')
    
    # Generic link to the record being adjusted
    target_model = models.CharField(max_length=50, help_text="e.g., 'Purchase', 'Sale', 'Flock'")
    target_id = models.PositiveIntegerField(help_text="The ID of the target record")
    
    reason = models.CharField(max_length=20, choices=ReasonChoices.choices)
    notes = models.TextField(blank=True, null=True)
    
    # Stores the before/after state. Example: 
    # [{"field": "quantity", "old_value": 100, "new_value": 90}]
    changes = models.JSONField(default=list) 

    class Meta:
        db_table = 'audit_adjustments'
        ordering = ['-entry_timestamp']  # Uses the BaseModel timestamp

    def __str__(self):
        return f"Adjustment on {self.target_model} #{self.target_id} by {self.created_by}"