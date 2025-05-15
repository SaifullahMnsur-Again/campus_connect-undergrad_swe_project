from django.contrib import admin
from .models import BloodGroup, Donor

@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 25

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'last_donated', 'consent')
    search_fields = ('user__name', 'user__email')
    list_filter = ('consent', 'last_donated')
    readonly_fields = ('created_at',)
    list_per_page = 25

    def blood_group(self, obj):
        return obj.user.blood_group.name if obj.user.blood_group else None
    blood_group.short_description = 'Blood Group'