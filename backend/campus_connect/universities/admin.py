from django.contrib import admin
from .models import University, AcademicUnit, TeacherDesignation

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'created_at']
    search_fields = ['name', 'short_name']
    ordering = ['name']

@admin.register(AcademicUnit)
class AcademicUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'unit_type', 'university', 'created_at']
    list_filter = ['unit_type', 'university']
    search_fields = ['name', 'short_name']
    ordering = ['name']

@admin.register(TeacherDesignation)
class TeacherDesignationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']