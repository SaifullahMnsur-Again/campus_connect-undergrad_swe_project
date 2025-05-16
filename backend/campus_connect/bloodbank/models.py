from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

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

class BloodRequest(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    blood_group = models.ForeignKey(
        BloodGroup,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    university = models.ForeignKey(
        'universities.University',
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    request_date = models.DateField()
    urgent = models.BooleanField(default=False, help_text="Indicates if the request is urgent")
    location = models.CharField(max_length=255, help_text="Specific location (e.g., hospital name)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_blood_requests'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blood_group', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['university']),
        ]

    def __str__(self):
        return f"Blood Request: {self.title} by {self.user.email}"

class BloodRequestDonor(models.Model):
    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name='registered_donors'
    )
    donor = models.ForeignKey(
        Donor,
        on_delete=models.CASCADE,
        related_name='blood_request_registrations'
    )
    message = models.TextField(help_text="Message from the donor to the request owner")
    contact_info = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Phone number must be in international format (e.g., +1234567890).")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['blood_request', 'donor']
        indexes = [
            models.Index(fields=['blood_request', 'donor']),
        ]

    def __str__(self):
        return f"Donor {self.donor.user.name} for {self.blood_request.title}"