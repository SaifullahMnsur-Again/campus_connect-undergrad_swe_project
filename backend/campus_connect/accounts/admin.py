from django.contrib import admin
from .models import User, VerificationCode

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'is_verified', 'date_joined')
    search_fields = ('name', 'email')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'date_joined')
    ordering = ('name',)
    readonly_fields = ('password', 'date_joined', 'last_login')
    list_per_page = 25

    fieldsets = (
        (None, {'fields': ('name', 'email', 'password')}),
        ('Contact Information', {
            'fields': ('phone', 'contact_visibility', 'blood_group'),
            'classes': ('collapse',),
        }),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing user
            return self.readonly_fields + ('email',)
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'blood_group':
            kwargs['required'] = False
            kwargs['empty_label'] = 'None'
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'created_at', 'expires_at')
    search_fields = ('user__email', 'code', 'purpose')
    list_filter = ('purpose', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at')
    list_per_page = 25