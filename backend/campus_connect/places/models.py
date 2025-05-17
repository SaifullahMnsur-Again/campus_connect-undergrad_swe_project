from django.db import models, transaction
from django.conf import settings
from django.core.validators import FileExtensionValidator
from universities.models import University, AcademicUnit
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

class PlaceType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

class Place(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='places',
        help_text="The university this place belongs to"
    )
    academic_unit = models.ForeignKey(
        AcademicUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='places',
        help_text="The academic unit this place is associated with, if applicable"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent place in the hierarchy"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    history = models.TextField(blank=True, help_text="Historical background of the place")
    establishment_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Year the place was established"
    )
    place_type = models.ForeignKey(
        PlaceType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='places',
        help_text="Type of place (e.g., Library, Classroom)"
    )
    relative_location = models.CharField(max_length=255, blank=True, help_text="Relative location description")
    latitude = models.FloatField(null=True, blank=True, help_text="Geographical latitude")
    longitude = models.FloatField(null=True, blank=True, help_text="Geographical longitude")
    maps_link = models.URLField(max_length=500, blank=True, help_text="Link to Google Maps or similar")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_places',
        help_text="User who created this place"
    )
    approval_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending',
        help_text="Approval status of the place"
    )
    university_root = models.BooleanField(
        default=False,
        help_text="Indicates if this place is the root of the university tree"
    )
    academic_unit_root = models.BooleanField(
        default=False,
        help_text="Indicates if this place is the root of an academic unit subtree"
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['university', 'name']),
            models.Index(fields=['place_type']),
            models.Index(fields=['parent']),
            models.Index(fields=['approval_status']),
            models.Index(fields=['academic_unit']),
            models.Index(fields=['university_root']),
            models.Index(fields=['academic_unit_root']),
        ]

    def __str__(self):
        return f"{self.name} ({self.university.name})"

    def clean(self):
        # Validate establishment year
        if self.establishment_year and self.establishment_year > timezone.now().year:
            raise ValidationError("Establishment year cannot be in the future.")

        # Validate academic unit
        if self.academic_unit and self.academic_unit.university != self.university:
            raise ValidationError("Academic unit must belong to the selected university.")

        # Prevent self-referential parent
        if self.parent and self.parent == self:
            raise ValidationError("A place cannot be its own parent.")

        # Validate parent university
        if self.parent and self.parent.university != self.university:
            raise ValidationError("Parent place must belong to the same university.")

        # Validate university_root
        if self.university_root:
            if self.parent:
                raise ValidationError({
                    'university_root': "A university root place cannot have a parent."
                })
            if self.academic_unit:
                raise ValidationError({
                    'university_root': "A university root place cannot have an academic unit."
                })
            existing_root = Place.objects.filter(
                university=self.university, university_root=True
            ).exclude(pk=self.pk).first()
            if existing_root:
                raise ValidationError({
                    'university_root': f"A university root is already set for {self.university.name}. "
                                      f"Existing root: ID={existing_root.id}, Name={existing_root.name}. "
                                      "Cannot register a new root place."
                })

        # Validate academic_unit_root
        if self.academic_unit_root:
            if not self.academic_unit:
                raise ValidationError({
                    'academic_unit_root': "An academic unit root place must have an academic unit."
                })
            if self.parent and self.parent.university != self.university:
                raise ValidationError({
                    'academic_unit_root': "An academic unit root place must have a parent in the same university."
                })
            existing_academic_root = Place.objects.filter(
                academic_unit=self.academic_unit, academic_unit_root=True
            ).exclude(pk=self.pk).first()
            if existing_academic_root:
                raise ValidationError({
                    'academic_unit_root': f"An academic unit root is already set for {self.academic_unit.name}. "
                                         f"Existing root: ID={existing_academic_root.id}, Name={existing_academic_root.name}. "
                                         "Cannot register a new root place."
                })

        # Ensure non-root places have a parent if a university root exists
        if not self.university_root and not self.parent:
            existing_root = Place.objects.filter(
                university=self.university, university_root=True
            ).first()
            if existing_root:
                raise ValidationError({
                    'parent': f"All non-root places must have a parent. University root exists: "
                              f"ID={existing_root.id}, Name={existing_root.name}."
                })

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.clean()
            super().save(*args, **kwargs)

class PlaceMedia(models.Model):
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='media',
        null=True,
        blank=True
    )
    place_update = models.ForeignKey(
        'PlaceUpdate',
        on_delete=models.CASCADE,
        related_name='media',
        null=True,
        blank=True
    )
    file = models.FileField(
        upload_to='places/media/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_place_media'
    )

    class Meta:
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['place']),
            models.Index(fields=['place_update']),
        ]

    def __str__(self):
        if self.place:
            return f"Media for {self.place.name}"
        return f"Media for Place Update"

class PlaceUpdate(models.Model):
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='updates'
    )
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE
    )
    academic_unit = models.ForeignKey(
        AcademicUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_children'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    history = models.TextField(blank=True)
    establishment_year = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    place_type = models.ForeignKey(
        PlaceType,
        on_delete=models.SET_NULL,
        null=True
    )
    relative_location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    maps_link = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='place_updates'
    )
    approval_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )
    university_root = models.BooleanField(
        default=False,
        help_text="Indicates if this place is the root of the university tree"
    )
    academic_unit_root = models.BooleanField(
        default=False,
        help_text="Indicates if this place is the root of an academic unit subtree"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['place', 'approval_status']),
            models.Index(fields=['updated_by']),
            models.Index(fields=['university_root']),
            models.Index(fields=['academic_unit_root']),
        ]

    def __str__(self):
        return f"Update for {self.place.name} by {self.updated_by.email if self.updated_by else 'Unknown'}"

    def clean(self):
        if self.establishment_year and self.establishment_year > timezone.now().year:
            raise ValidationError("Establishment year cannot be in the future.")

        if self.academic_unit and self.academic_unit.university != self.university:
            raise ValidationError("Academic unit must belong to the selected university.")

        if self.parent and self.parent.university != self.university:
            raise ValidationError("Parent place must belong to the same university.")

        if self.university_root:
            if self.parent:
                raise ValidationError({
                    'university_root': "A university root place cannot have a parent."
                })
            if self.academic_unit:
                raise ValidationError({
                    'university_root': "A university root place cannot have an academic unit."
                })
            existing_root = Place.objects.filter(
                university=self.university, university_root=True
            ).exclude(pk=self.place.pk).first()
            if existing_root:
                raise ValidationError({
                    'university_root': f"A university root is already set for {self.university.name}. "
                                      f"Existing root: ID={existing_root.id}, Name={existing_root.name}. "
                                      "Cannot register a new root place."
                })

        if self.academic_unit_root:
            if not self.academic_unit:
                raise ValidationError({
                    'academic_unit_root': "An academic unit root place must have an academic unit."
                })
            if self.parent and self.parent.university != self.university:
                raise ValidationError({
                    'academic_unit_root': "An academic unit root place must have a parent in the same university."
                })
            existing_academic_root = Place.objects.filter(
                academic_unit=self.academic_unit, academic_unit_root=True
            ).exclude(pk=self.place.pk).first()
            if existing_academic_root:
                raise ValidationError({
                    'academic_unit_root': f"An academic unit root is already set for {self.academic_unit.name}. "
                                         f"Existing root: ID={existing_academic_root.id}, Name={existing_academic_root.name}. "
                                         "Cannot register a new root place."
                })

        if not self.university_root and not self.parent:
            existing_root = Place.objects.filter(
                university=self.university, university_root=True
            ).first()
            if existing_root:
                raise ValidationError({
                    'parent': f"All non-root places must have a parent. University root exists: "
                              f"ID={existing_root.id}, Name={existing_root.name}."
                })

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.clean()
            super().save(*args, **kwargs)