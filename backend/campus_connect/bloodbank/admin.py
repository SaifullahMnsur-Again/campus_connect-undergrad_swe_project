from django.contrib import admin
from .models import BloodGroup, Donor

@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    """Admin for BloodGroup model."""
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    """Admin for Donor model."""
    list_display = ['user']
    search_fields = ['user__email', 'user__name']
    ordering = ['user__email']