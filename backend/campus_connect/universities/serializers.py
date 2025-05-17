from rest_framework import serializers
from .models import University, AcademicUnit, TeacherDesignation
from places.models import Place
from django.urls import reverse

class UniversitySerializer(serializers.ModelSerializer):
    place_url = serializers.SerializerMethodField()

    class Meta:
        model = University
        fields = ['id', 'name', 'short_name', 'place_url']

    def get_place_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        root_place = Place.objects.filter(
            university=obj, parent__isnull=True, approval_status='approved'
        ).first()
        if root_place:
            return request.build_absolute_uri(reverse('places:place-detail', kwargs={'pk': root_place.pk}))
        return None

class AcademicUnitSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)
    university_id = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(), source='university', write_only=True
    )
    name = serializers.CharField()  # Raw name for input
    unit_type = serializers.ChoiceField(choices=AcademicUnit.UNIT_TYPES)
    place_url = serializers.SerializerMethodField()

    class Meta:
        model = AcademicUnit
        fields = ['id', 'name', 'short_name', 'unit_type', 'university', 'university_id', 'place_url']

    def get_place_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        root_place = Place.objects.filter(
            academic_unit=obj, parent__isnull=True, approval_status='approved'
        ).first()
        if root_place:
            return request.build_absolute_uri(reverse('places:place-detail', kwargs={'pk': root_place.pk}))
        return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Format name as "Department of {name}" or "Institute of {name}"
        if instance.unit_type == 'department':
            ret['name'] = f"Department of {instance.name}"
        else:  # institute
            ret['name'] = f"Institute of {instance.name}"
        return ret

    def validate(self, data):
        name = data.get('name')
        unit_type = data.get('unit_type')
        university = data.get('university')
        instance = self.instance

        # Check for unique name, university, unit_type combination
        filters = {
            'name': name,
            'unit_type': unit_type,
            'university': university
        }
        if instance:
            # Exclude current instance during update
            if AcademicUnit.objects.filter(**filters).exclude(id=instance.id).exists():
                raise serializers.ValidationError({
                    'name': f"An {unit_type} with this name already exists for the selected university."
                })
        else:
            # Check for create
            if AcademicUnit.objects.filter(**filters).exists():
                raise serializers.ValidationError({
                    'name': f"An {unit_type} with this name already exists for the selected university."
                })

        return data

class TeacherDesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherDesignation
        fields = ['id', 'name']