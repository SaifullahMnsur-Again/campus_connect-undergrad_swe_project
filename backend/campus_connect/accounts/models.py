from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator
from bloodbank.models import BloodGroup

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email field must be set")
        if not password:
            raise ValueError("Password field must be set")
        
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
    class ContactVisibility(models.TextChoices):
        NONE = 'none', 'None'
        EMAIL = 'email', 'Email only'
        PHONE = 'phone', 'Phone only'
        BOTH = 'both', 'Email and Phone'

    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Phone number must be in international format (e.g., +1234567890).")]
    )
    blood_group = models.ForeignKey(BloodGroup, on_delete=models.SET_NULL, null=True, blank=True)
    contact_visibility = models.CharField(
        max_length=10,
        choices=ContactVisibility.choices,
        default=ContactVisibility.NONE
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['name']),
        ]

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