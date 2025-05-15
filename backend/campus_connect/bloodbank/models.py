from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class BloodGroup(models.Model):
    name = models.CharField(max_length=3, unique=True)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

class Donor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='donor_profile', 
        related_query_name='donor'
    )
    last_donated = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Phone number must be in international format (e.g., +1234567890).")]
    )
    preferred_location = models.CharField(max_length=100)
    consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donor: {self.user.name} ({self.user.blood_group or 'No blood group'})"

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['last_donated']),
        ]