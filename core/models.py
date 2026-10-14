from django.db import models
from django.conf import settings

class BaseModel(models.Model):
    """
    Abstract base model for all transactional records.
    Enforces SRS 7.3 (Event date vs Entry timestamp) and SRS 11 (Classification).
    """
    
    class ClassificationChoices(models.TextChoices):
        OPENING = 'OPENING', 'Opening'
        HISTORICAL = 'HISTORICAL', 'Historical'
        LIVE = 'LIVE', 'Live'

    # SRS 7.3: When the farm activity actually happened (chosen by user)
    event_date = models.DateField(
        help_text="The date the farm activity actually occurred."
    )
    
    # SRS 7.3: When the system received the record (auto-generated)
    entry_timestamp = models.DateTimeField(
        auto_now_add=True, 
        help_text="System timestamp when this record was created."
    )
    
    # SRS 11: Distinguishes opening, historical, and live records
    classification = models.CharField(
        max_length=10,
        choices=ClassificationChoices.choices,
        default=ClassificationChoices.LIVE,
        help_text="Record classification: Opening, Historical, or Live."
    )

    # SRS 7.3: Automatic attribution
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True, # Null allowed for initial setup scripts
        help_text="The user who created this record."
    )

    class Meta:
        abstract = True # This ensures no database table is created for BaseModel itself