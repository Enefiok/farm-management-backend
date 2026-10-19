import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Account(models.Model):
    """
    The top-level tenant. A user belongs to an Account, 
    and an Account can contain multiple Farms.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts'

    def __str__(self):
        return self.name

class Membership(models.Model):
    """
    Links a User to an Account with a specific role.
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
        related_name='memberships'
    )
    account = models.ForeignKey(
        Account, 
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
        db_table = 'memberships'
        unique_together = ('user', 'account')

    def __str__(self):
        return f"{self.user.email} - {self.account.name} ({self.role})"

class Invitation(models.Model):
    """
    Tracks invitations sent to users to join a farm.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        EXPIRED = 'EXPIRED', 'Expired'

    email = models.EmailField()
    farm = models.ForeignKey(
        'farms.Farm', 
        on_delete=models.CASCADE, 
        related_name='invitations'
    )
    role = models.CharField(
        max_length=20, 
        choices=Membership.RoleChoices.choices, 
        default=Membership.RoleChoices.STAFF
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    status = models.CharField(
        max_length=10, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'invitations'

    def __str__(self):
        return f"Invite for {self.email} to {self.farm.name}"