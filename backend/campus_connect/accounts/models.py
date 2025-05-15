from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from universities.models import University, AcademicUnit, TeacherDesignation
from bloodbank.models import BloodGroup

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    CONTACT_VISIBILITY = (
        ('none', 'None'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Both'),
    )
    ROLES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('officer', 'Officer'),
        ('staff', 'Staff'),
    )
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.SET_NULL, null=True, blank=True)
    contact_visibility = models.CharField(max_length=20, choices=CONTACT_VISIBILITY, default='none')
    role = models.CharField(max_length=20, choices=ROLES, default='student')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    academic_unit = models.ForeignKey(AcademicUnit, on_delete=models.SET_NULL, null=True, blank=True)
    teacher_designation = models.ForeignKey(TeacherDesignation, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=255, blank=True)
    workplace = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        ordering = ['email']

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if self.academic_unit and self.university:
            if self.academic_unit.university != self.university:
                raise ValidationError({
                    'academic_unit': 'Academic unit must belong to the selected university.'
                })
        if self.role in ['student', 'teacher']:
            if self.university and not self.academic_unit:
                raise ValidationError({
                    'academic_unit': 'Must select an academic unit if a university is chosen.'
                })
        else:
            if self.university or self.academic_unit:
                raise ValidationError({
                    'university': 'University and academic unit should only be set for students and teachers.',
                    'academic_unit': 'University and academic unit should only be set for students and teachers.'
                })
        if self.role == 'teacher':
            if not self.teacher_designation:
                raise ValidationError({
                    'teacher_designation': 'Designation is required for teachers.'
                })
        else:
            if self.teacher_designation:
                raise ValidationError({
                    'teacher_designation': 'Designation should only be set for teachers.'
                })
        if self.role in ['officer', 'staff']:
            if not self.designation:
                raise ValidationError({
                    'designation': 'Designation is required for officers and staff.'
                })
            if not self.workplace:
                raise ValidationError({
                    'workplace': 'Workplace is required for officers and staff.'
                })
        else:
            if self.designation:
                raise ValidationError({
                    'designation': 'Designation should only be set for officers and staff.'
                })
            if self.workplace:
                raise ValidationError({
                    'workplace': 'Workplace should only be set for officers and staff.'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
        PASSWORD_RESET = 'password_reset', 'Password Reset'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.code} ({self.purpose})"

    def is_expired(self):
        return self.expires_at < timezone.now()