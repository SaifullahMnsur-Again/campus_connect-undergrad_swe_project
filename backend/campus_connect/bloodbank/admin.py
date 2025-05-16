from django.contrib import admin
from .models import BloodGroup, Donor, BloodRequest, BloodRequestDonor


@admin.register(BloodGroup)
class BloodGroupAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_blood_group', 'preferred_location', 'last_donated', 'consent']
    search_fields = ['user__name', 'user__email', 'preferred_location']
    autocomplete_fields = ['user']
    readonly_fields = ['created_at']

    def get_blood_group(self, obj):
        return obj.user.blood_group.name if obj.user.blood_group else '-'
    get_blood_group.short_description = 'Blood Group'

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'blood_group', 'request_date', 'location', 'status']
    list_filter = ['status', 'blood_group', 'request_date']
    search_fields = ['title', 'description', 'user__email']
    autocomplete_fields = ['user', 'university']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BloodRequestDonor)
class BloodRequestDonorAdmin(admin.ModelAdmin):
    list_display = ['blood_request', 'donor', 'contact_info', 'created_at']
    search_fields = ['blood_request__title', 'donor__user__name', 'contact_info']
    autocomplete_fields = ['blood_request', 'donor']
    readonly_fields = ['created_at']
