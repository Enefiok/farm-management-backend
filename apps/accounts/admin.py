from django.contrib import admin
from .models import Account, Membership, Invitation

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'role', 'joined_at')

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'farm', 'role', 'status', 'expires_at')
    list_filter = ('status', 'role')