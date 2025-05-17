from rest_framework import serializers
from django.core.validators import MinLengthValidator
from .models import User
from django.urls import reverse
from bloodbank.models import BloodGroup
from universities.models import University, AcademicUnit, TeacherDesignation
from django.core.exceptions import ValidationError as DjangoValidationError

class SimpleUserSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'detail_url']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        try:
            return request.build_absolute_uri(reverse('accounts:user-detail', kwargs={'pk': obj.pk}))
        except:
            return None

class UserListSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'role', 'admin_level', 'university', 'academic_unit', 'detail_url']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(reverse('accounts:user-detail', args=[obj.id]))
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.role not in ['student', 'teacher']:
            ret.pop('university', None)
            ret.pop('academic_unit', None)
        else:
            if instance.university:
                ret['university'] = {
                    'name': instance.university.name,
                    'short_name': instance.university.short_name or None
                }
            else:
                ret.pop('university', None)
            if instance.academic_unit:
                ret['academic_unit'] = {
                    'name': str(instance.academic_unit),
                    'short_name': instance.academic_unit.short_name or None,
                    'unit_type': instance.academic_unit.unit_type
                }
            else:
                ret.pop('academic_unit', None)
        return ret

class UserSerializer(serializers.ModelSerializer):
    blood_group = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'phone', 'blood_group', 'contact_visibility',
            'role', 'admin_level', 'university', 'academic_unit', 'teacher_designation', 'designation', 'workplace'
        ]

    def validate_blood_group(self, value):
        if not value:
            return None
        try:
            blood_group = BloodGroup.objects.get(name=value)
            return blood_group
        except BloodGroup.DoesNotExist:
            raise serializers.ValidationError(f"Blood group '{value}' does not exist.")

    def validate(self, data):
        try:
            instance = self.instance or User()
            for key, value in data.items():
                setattr(instance, key, value)
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})
        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        role = instance.role

        if role == 'student':
            allowed_fields = [
                'id', 'name', 'email', 'phone', 'blood_group',
                'contact_visibility', 'role', 'admin_level', 'university', 'academic_unit'
            ]
        elif role == 'teacher':
            allowed_fields = [
                'id', 'name', 'email', 'phone', 'blood_group',
                'contact_visibility', 'role', 'admin_level', 'university', 'academic_unit', 'teacher_designation'
            ]
        else:
            allowed_fields = [
                'id', 'name', 'email', 'phone', 'blood_group',
                'contact_visibility', 'role', 'admin_level', 'designation', 'workplace'
            ]

        ret = {k: v for k, v in ret.items() if k in allowed_fields}

        if role in ['student', 'teacher']:
            if instance.university:
                ret['university'] = {
                    'name': instance.university.name,
                    'short_name': instance.university.short_name or None
                }
            else:
                ret.pop('university', None)
            if instance.academic_unit:
                ret['academic_unit'] = {
                    'name': str(instance.academic_unit),
                    'short_name': instance.academic_unit.short_name or None,
                    'unit_type': instance.academic_unit.unit_type
                }
            else:
                ret.pop('academic_unit', None)
            if role == 'teacher' and instance.teacher_designation:
                ret['teacher_designation'] = instance.teacher_designation.name
            else:
                ret.pop('teacher_designation', None)
        if role in ['officer', 'staff']:
            if not ret.get('designation'):
                ret.pop('designation', None)
            if not ret.get('workplace'):
                ret.pop('workplace', None)

        if not ret.get('phone'):
            ret.pop('phone', None)
        if instance.blood_group:
            ret['blood_group'] = instance.blood_group.name
        else:
            ret.pop('blood_group', None)

        if request and (request.user == instance or request.user.is_superuser):
            return ret
        visibility = instance.contact_visibility
        if visibility == 'none':
            ret.pop('email', None)
            ret.pop('phone', None)
        elif visibility == 'email':
            ret.pop('phone', None)
        elif visibility == 'phone':
            ret.pop('email', None)
        return ret

class UserProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            'id', 'name', 'email', 'phone', 'blood_group', 'contact_visibility',
            'role', 'admin_level', 'university', 'academic_unit', 'teacher_designation', 'designation', 'workplace'
        ]
        read_only_fields = ['email']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[MinLengthValidator(8, "Password must be at least 8 characters long")]
    )
    confirm_password = serializers.CharField(write_only=True)
    blood_group = serializers.CharField(allow_blank=True, required=False)
    designation = serializers.CharField(allow_blank=True, required=False, allow_null=False)
    workplace = serializers.CharField(allow_blank=True, required=False, allow_null=False)
    phone = serializers.CharField(allow_blank=True, required=False, allow_null=False)
    admin_level = serializers.ChoiceField(choices=User.ADMIN_LEVELS, default='none')

    class Meta:
        model = User
        fields = [
            'name', 'email', 'password', 'confirm_password', 'blood_group', 'phone', 'contact_visibility',
            'role', 'admin_level', 'university', 'academic_unit', 'teacher_designation', 'designation', 'workplace'
        ]

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
            raise serializers.ValidationError(f"Blood group '{value}' does not exist.")

    def validate_designation(self, value):
        if value == '':
            return None
        return value

    def validate_workplace(self, value):
        if value == '':
            return None
        return value

    def validate_phone(self, value):
        if value == '':
            return None
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        try:
            user = User(**data)
            user.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)