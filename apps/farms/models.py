from django.db import models
from django.conf import settings
from apps.accounts.models import Account
from core.models import BaseModel

class Farm(models.Model):
    """
    A specific farm workspace. Belongs to an Account.
    """
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='farms'
    )
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'farms'

    def __str__(self):
        return self.name

class FarmMembership(models.Model):
    """
    Links a User to a specific Farm with a role.
    This allows an Owner to give a user access to only Farm A, but not Farm B.
    """
    class RoleChoices(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMINISTRATOR = 'ADMINISTRATOR', 'Administrator'
        FARM_MANAGER = 'FARM_MANAGER', 'Farm Manager'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
        STAFF = 'STAFF', 'Staff'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='farm_memberships'
    )
    farm = models.ForeignKey(
        Farm, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20, 
        choices=RoleChoices.choices, 
        default=RoleChoices.STAFF
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'farm_memberships'
        unique_together = ('user', 'farm')

    def __str__(self):
        return f"{self.user.email} - {self.farm.name} ({self.role})"

class FarmSetting(models.Model):
    """
    Stores farm-specific preferences (Currency, Timezone, Units).
    Created automatically when a Farm is created.
    """
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name='settings')
    currency = models.CharField(max_length=3, default='NGN', help_text="ISO currency code (e.g., NGN, USD)")
    timezone = models.CharField(max_length=50, default='Africa/Lagos')
    unit_system = models.CharField(max_length=10, default='metric')

    class Meta:
        db_table = 'farm_settings'

    def __str__(self):
        return f"Settings for {self.farm.name}"

# --- SPRINT 3 MODELS: OPENING POSITION ---

class OpeningPosition(BaseModel):
    """
    The starting snapshot of a farm (birds, stock, balances).
    Inherits from BaseModel to capture event_date (opening date), 
    entry_timestamp, and created_by automatically.
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='opening_positions')
    status = models.CharField(max_length=20, choices=[('DRAFT', 'Draft'), ('CONFIRMED', 'Confirmed')], default='DRAFT')

    class Meta:
        db_table = 'farms_opening_positions'

    def __str__(self):
        return f"Opening Position for {self.farm.name} on {self.event_date}"

class OpeningFlockLine(models.Model):
    """Starting bird count for a specific flock."""
    position = models.ForeignKey(OpeningPosition, on_delete=models.CASCADE, related_name='flock_lines')
    identifier = models.CharField(max_length=50, help_text="e.g., 'Flock A'")
    initial_count = models.PositiveIntegerField()

    class Meta:
        db_table = 'farms_opening_flock_lines'

class OpeningStockLine(models.Model):
    """Starting stock quantity for a specific item."""
    position = models.ForeignKey(OpeningPosition, on_delete=models.CASCADE, related_name='stock_lines')
    # String reference prevents circular import with apps.catalog.models
    item = models.ForeignKey('catalog.Item', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'farms_opening_stock_lines'