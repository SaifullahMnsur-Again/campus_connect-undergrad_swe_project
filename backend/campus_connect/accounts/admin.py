from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VerificationCode

class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with additional fields."""
    model = User
    list_display = ['email', 'name', 'role', 'university', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['role', 'university', 'is_active', 'is_verified']
    search_fields = ['email', 'name']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'blood_group', 'contact_visibility')}),
        ('University Info', {'fields': ('role', 'university', 'academic_unit', 'teacher_designation')}),
        ('Officer/Staff Info', {'fields': ('designation', 'workplace')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'name', 'password1', 'password2', 'role',
                'university', 'academic_unit', 'teacher_designation',
                'designation', 'workplace',
                'phone', 'blood_group', 'contact_visibility',
                'is_active', 'is_verified', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
    )
    readonly_fields = ['date_joined']
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(User, CustomUserAdmin)

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    """Admin for VerificationCode model."""
    list_display = ['user', 'code', 'purpose', 'expires_at', 'created_at']
    list_filter = ['purpose']
    search_fields = ['user__email', 'code']
    ordering = ['-created_at']
    readonly_fields = ['created_at']