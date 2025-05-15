from rest_framework import serializers
from django.utils import timezone
from .models import BloodGroup, Donor

class BloodGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodGroup
        fields = ['name']  # Only include the name field

class DonorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    blood_group = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Donor
        fields = [
            'emergency_contact',
            'preferred_location',
            'last_donated',
            'consent',
            'name',
            'blood_group',
            'user'
        ]
        read_only_fields = ['name', 'blood_group', 'user']

    def get_name(self, obj):
        return obj.user.name

    def get_blood_group(self, obj):
        return obj.user.blood_group.name if obj.user.blood_group else None

    def validate_last_donated(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Last donated date cannot be in the future.")
        return value