from django.urls import NoReverseMatch, reverse
from rest_framework import serializers
from django.utils import timezone
from django.core.validators import RegexValidator
from .models import BloodGroup, Donor, BloodRequest, BloodRequestDonor
from universities.models import University
from accounts.serializers import SimpleUserSerializer
import logging
from django.db import models

logger = logging.getLogger(__name__)

class BloodGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodGroup
        fields = ['name']

class DonorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    blood_group = serializers.SerializerMethodField(read_only=True)
    detail_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Donor
        fields = [
            'emergency_contact',
            'preferred_location',
            'last_donated',
            'consent',
            'name',
            'blood_group',
            'user',
            'detail_url'
        ]
        read_only_fields = ['name', 'blood_group', 'user']

    def get_name(self, obj):
        return obj.user.name

    def get_blood_group(self, obj):
        return obj.user.blood_group.name if obj.user.blood_group else None

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            logger.warning("Request context missing in DonorSerializer.get_detail_url")
            return None
        try:
            return request.build_absolute_uri(reverse('donor-detail', kwargs={'pk': obj.pk}))
        except NoReverseMatch as e:
            logger.error(f"Failed to reverse 'donor-detail' for donor ID {obj.pk}: {e}")
            return None

    def validate_last_donated(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Last donated date cannot be in the future.")
        return value

class BloodRequestDonorSerializer(serializers.ModelSerializer):
    donor = serializers.SerializerMethodField(read_only=True)
    blood_request = serializers.PrimaryKeyRelatedField(
        queryset=BloodRequest.objects.filter(status='open')
    )
    message = serializers.CharField(min_length=10, max_length=1000)
    contact_info = serializers.CharField(max_length=20)

    class Meta: 
        model = BloodRequestDonor
        fields = ['id', 'blood_request', 'donor', 'message', 'contact_info', 'created_at']
        read_only_fields = ['donor', 'created_at']

    def get_donor(self, obj):
        request = self.context.get('request')
        return {
            'id': obj.donor.user.id,
            'name': obj.donor.user.name,
            'blood_group': obj.donor.user.blood_group.name if obj.donor.user.blood_group else None,
            'emergency_contact': obj.donor.emergency_contact,
            'preferred_location': obj.donor.preferred_location,
            'detail_url': request.build_absolute_uri(
                reverse('donor-detail', kwargs={'pk': obj.donor.pk})
                ) if request else None
        }

    def validate_contact_info(self, value):
        validator = RegexValidator(r'^\+?1?\d{9,15}$', "Phone number must be in international format (e.g., +1234567890).")
        validator(value)
        return value

    def validate(self, data):
        request = self.context.get('request')
        blood_request = data['blood_request']
        donor = Donor.objects.get(user=request.user)
        if blood_request.user == request.user:
            raise serializers.ValidationError("You cannot register to donate for your own blood request.")
        if BloodRequestDonor.objects.filter(blood_request=blood_request, donor=donor).exists():
            raise serializers.ValidationError("You have already registered to donate for this request.")
        return data

    def create(self, validated_data):
        donor = Donor.objects.get(user=self.context['request'].user)
        return BloodRequestDonor.objects.create(donor=donor, **validated_data)

class BloodRequestSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    blood_group = serializers.CharField(allow_blank=True, required=False)
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), required=True)
    registered_donors = BloodRequestDonorSerializer(many=True, read_only=True)
    media = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'user', 'blood_group', 'university', 'title', 'description',
            'request_date', 'urgent', 'location', 'status',
            'created_at', 'updated_at', 'resolved_by', 'media', 'registered_donors'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'resolved_by']

    def get_media(self, obj):
        return []

    def validate_blood_group(self, value):
        if not value:
            return None
        try:
            blood_group = BloodGroup.objects.get(name=value)
            return blood_group
        except BloodGroup.DoesNotExist:
            raise serializers.ValidationError(f"Blood group '{value}' does not exist.")

    def validate_request_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Request date cannot be in the past.")
        return value
    

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        if request and not (request.user == instance.user or request.user.admin_level in ['university', 'app']):
            ret['registered_donors'] = []
        return ret