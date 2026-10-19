from django.contrib import admin
from .models import Farm, FarmMembership

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'location', 'created_at')

@admin.register(FarmMembership)
class FarmMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'farm', 'role', 'joined_at')