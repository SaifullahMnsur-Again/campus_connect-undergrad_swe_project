from django.db import models

class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, blank=True, help_text="Short name or abbreviation (e.g., NSU)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "universities"
        ordering = ['name']

    def __str__(self):
        return self.name

class AcademicUnit(models.Model):
    UNIT_TYPES = (
        ('department', 'Department'),
        ('institute', 'Institute'),
    )
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, blank=True, help_text="Short name or abbreviation (e.g., CS)")
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='academic_units')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'university', 'unit_type']
        ordering = ['name']

    def __str__(self):
        if self.unit_type == 'department':
            return f"Department of {self.name}"
        return f"Institute of {self.name}"

class TeacherDesignation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name