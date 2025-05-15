from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import User
from django.urls import reverse
from bloodbank.models import BloodGroup

class UserListSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'detail_url']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(reverse('user-detail', args=[obj.id]))
        return None

class UserSerializer(serializers.ModelSerializer):
    blood_group = serializers.CharField(allow_blank=True, required=False)
    blood_group_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'blood_group', 'blood_group_name', 'contact_visibility']
        read_only_fields = ['blood_group_name']

    def validate_blood_group(self, value):
        if not value:
            return None
        try:
            blood_group = BloodGroup.objects.get(name=value)
            return blood_group
        except BloodGroup.DoesNotExist:
            raise serializers.ValidationError(f"Blood group '{value}' does not exist.")

    def get_blood_group_name(self, obj):
        return obj.blood_group.name if obj.blood_group else None

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        # Skip visibility restrictions for the profile owner or superuser
        if request and (request.user == instance or request.user.is_superuser):
            rep['blood_group'] = instance.blood_group.name if instance.blood_group else None
            return rep

        # Apply visibility restrictions for other users
        visibility = instance.contact_visibility
        if visibility == 'none':
            rep.pop('email', None)
            rep.pop('phone', None)
        elif visibility == 'email':
            rep.pop('phone', None)
        elif visibility == 'phone':
            rep.pop('email', None)
        rep['blood_group'] = instance.blood_group.name if instance.blood_group else None
        return rep

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(8, "Password must be at least 8 characters long")]
    )
    confirm_password = serializers.CharField(write_only=True)
    blood_group = serializers.CharField(allow_blank=True, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_blood_group(self, value):
        if not value:
            return None
        try:
            blood_group = BloodGroup.objects.get(name=value)
            return blood_group
        except BloodGroup.DoesNotExist:
            raise serializers.ValidationError(f"B Booking group '{value}' does not exist.")

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)