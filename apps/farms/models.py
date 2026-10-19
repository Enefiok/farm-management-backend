from django.db import models
from django.conf import settings
from apps.accounts.models import Account

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