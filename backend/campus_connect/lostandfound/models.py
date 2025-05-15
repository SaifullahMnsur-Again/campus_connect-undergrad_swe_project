import secrets
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from universities.models import University
from django.utils.translation import gettext_lazy as _

def generate_random_id():
    return secrets.token_urlsafe(12)  # Generates a 16-char URL-safe random string

class LostItem(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('claimed', 'Claimed'),
        ('found', 'Found'),
        ('externally_found', 'Externally Found'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lost_items'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='lost_items'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    lost_date = models.DateField()
    approximate_time = models.TimeField(null=True, blank=True, help_text="Approximate time the item was lost (e.g., 14:30)")
    location = models.CharField(max_length=255, help_text="Specific location within the university")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_lost_items'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['university', 'status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Lost: {self.title} by {self.user.email}"

class FoundItem(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('claimed', 'Claimed'),
        ('returned', 'Returned'),
        ('externally_returned', 'Externally Returned'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='found_items'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='found_items'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    found_date = models.DateField()
    approximate_time = models.TimeField(null=True, blank=True, help_text="Approximate time the item was found (e.g., 14:30)")
    location = models.CharField(max_length=255, help_text="Specific location within the university")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_found_items'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['university', 'status']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Found: {self.title} by {self.user.email}"

class ItemMedia(models.Model):
    id = models.CharField(
        max_length=16,
        primary_key=True,
        default=generate_random_id,
        editable=False
    )
    lost_item = models.ForeignKey(
        LostItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    found_item = models.ForeignKey(
        FoundItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    lost_item_claim = models.ForeignKey(
        'LostItemClaim',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    found_item_claim = models.ForeignKey(
        'FoundItemClaim',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media'
    )
    file = models.FileField(
        upload_to='lostandfound/media/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        if self.lost_item:
            return f"Media for Lost: {self.lost_item.title}"
        elif self.found_item:
            return f"Media for Found: {self.found_item.title}"
        elif self.lost_item_claim:
            return f"Media for Lost Claim: {self.lost_item_claim.lost_item.title}"
        elif self.found_item_claim:
            return f"Media for Found Claim: {self.found_item_claim.found_item.title}"
        return "Media"

class LostItemClaim(models.Model):
    lost_item = models.ForeignKey(
        LostItem,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lost_item_claims'
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['lost_item', 'claimant']

    def __str__(self):
        return f"Claim by {self.claimant.email} for {self.lost_item.title}"

class FoundItemClaim(models.Model):
    found_item = models.ForeignKey(
        FoundItem,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='found_item_claims'
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['found_item', 'claimant']

    def __str__(self):
        return f"Claim by {self.claimant.email} for {self.found_item.title}"