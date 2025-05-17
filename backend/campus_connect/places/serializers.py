from rest_framework import serializers
from .models import Place, PlaceType, PlaceMedia, PlaceUpdate
from universities.models import University, AcademicUnit
from accounts.serializers import SimpleUserSerializer
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)

class PlaceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceType
        fields = ['id', 'name']

class PlaceSearchSerializer(serializers.Serializer):
    university = serializers.CharField(required=False)
    place_type = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    relative_location = serializers.CharField(required=False)
    academic_unit = serializers.CharField(required=False)

    def validate(self, data):
        request = self.context.get('request')
        query_string = request.META.get('QUERY_STRING', '') if request else ''
        
        # Extract raw query (unnamed query string)
        raw_query = None
        if query_string:
            # Remove known parameters
            specific_fields = ['university', 'place_type', 'name', 'relative_location', 'academic_unit']
            query_parts = query_string.split('&')
            for part in query_parts:
                if '=' not in part or part.split('=')[0] not in specific_fields:
                    raw_query = part.split('=')[-1] if '=' in part else part
                    break
        
        # Store raw query in validated data
        data['raw_query'] = raw_query if raw_query else None
        logger.debug(f"Raw query extracted: {data['raw_query']}")

        # Prevent mixing raw query with specific fields
        has_specific_fields = any(data.get(field) for field in ['university', 'place_type', 'name', 'relative_location', 'academic_unit'])
        if raw_query and has_specific_fields:
            raise serializers.ValidationError({
                'non_field_errors': 'Cannot use general search with specific fields (university, place_type, name, relative_location, academic_unit).'
            })
        
        return data

class PlaceMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    next_media_url = serializers.SerializerMethodField()
    previous_media_url = serializers.SerializerMethodField()

    class Meta:
        model = PlaceMedia
        fields = ['id', 'file_url', 'uploaded_at', 'next_media_url', 'previous_media_url']
        read_only_fields = ['uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('places:media-access', kwargs={'pk': obj.id}))

    def get_next_media_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        if obj.place:
            next_media = PlaceMedia.objects.filter(
                place=obj.place, uploaded_at__gt=obj.uploaded_at
            ).order_by('uploaded_at').first()
        else:
            next_media = PlaceMedia.objects.filter(
                place_update=obj.place_update, uploaded_at__gt=obj.uploaded_at
            ).order_by('uploaded_at').first()
        if next_media:
            return request.build_absolute_uri(reverse('places:media-access', kwargs={'pk': next_media.id}))
        return None

    def get_previous_media_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        if obj.place:
            previous_media = PlaceMedia.objects.filter(
                place=obj.place, uploaded_at__lt=obj.uploaded_at
            ).order_by('-uploaded_at').first()
        else:
            previous_media = PlaceMedia.objects.filter(
                place_update=obj.place_update, uploaded_at__lt=obj.uploaded_at
            ).order_by('-uploaded_at').first()
        if previous_media:
            return request.build_absolute_uri(reverse('places:media-access', kwargs={'pk': previous_media.id}))
        return None

class SimplePlaceSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ['id', 'name', 'detail_url']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('places:place-detail', kwargs={'pk': obj.pk}))

class PlaceSerializer(serializers.ModelSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    academic_unit = serializers.PrimaryKeyRelatedField(queryset=AcademicUnit.objects.all(), required=False, allow_null=True)
    place_type = serializers.CharField()
    parent = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all(), required=False, allow_null=True)
    media_files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        write_only=True,
        required=False,
        max_length=5
    )
    media = PlaceMediaSerializer(many=True, read_only=True)
    parent_data = SimplePlaceSerializer(source='parent', read_only=True)
    children = SimplePlaceSerializer(many=True, read_only=True)
    created_by = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Place
        fields = [
            'id', 'university', 'academic_unit', 'parent', 'parent_data', 'children',
            'name', 'description', 'history', 'establishment_year', 'place_type',
            'relative_location', 'latitude', 'longitude', 'maps_link', 'created_at',
            'updated_at', 'created_by', 'media', 'media_files', 'approval_status',
            'university_root', 'academic_unit_root'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'approval_status']
        extra_kwargs = {
            'created_by': {'write_only': False}
        }

    def validate_place_type(self, value):
        if not value:
            return None
        value = value.strip().lower()
        place_type, created = PlaceType.objects.get_or_create(name=value)
        return place_type

    def validate_establishment_year(self, value):
        if value and value > timezone.now().year:
            raise serializers.ValidationError("Establishment year cannot be in the future.")
        return value

    def validate_media_files(self, value):
        max_size = 10 * 1024 * 1024
        for file in value:
            if file.size > max_size:
                raise serializers.ValidationError(f"File {file.name} exceeds maximum size of 10MB.")
        return value

    def validate(self, data):
        try:
            university = data.get('university')
            academic_unit = data.get('academic_unit')
            parent = data.get('parent')

            if academic_unit and academic_unit.university != university:
                raise serializers.ValidationError({
                    'academic_unit': 'Academic unit must belong to the selected university.'
                })

            if parent and parent.university != university:
                raise serializers.ValidationError({
                    'parent': 'Parent place must belong to the same university.'
                })

            place = Place(**data)
            place.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        logger.debug(f"Received media files: {media_files}")
        validated_data.pop('created_by', None)
        try:
            place = Place.objects.create(created_by=self.context['request'].user, **validated_data)
            for file in media_files:
                try:
                    logger.debug(f"Creating PlaceMedia for file: {file}")
                    PlaceMedia.objects.create(
                        place=place,
                        file=file,
                        uploaded_by=self.context['request'].user
                    )
                except DjangoValidationError as e:
                    logger.error(f"Failed to create PlaceMedia: {str(e)}")
                    raise serializers.ValidationError(f"Invalid media file: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error creating PlaceMedia: {str(e)}")
                    raise serializers.ValidationError(f"Error saving media file: {str(e)}")
            return place
        except DjangoValidationError as e:
            logger.error(f"Validation error creating place: {str(e)}")
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})

class PlaceUpdateSerializer(serializers.ModelSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all(), required=False, allow_null=True)
    academic_unit = serializers.PrimaryKeyRelatedField(queryset=AcademicUnit.objects.all(), required=False, allow_null=True)
    place_type = serializers.CharField(required=False, allow_blank=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all(), required=False, allow_null=True)
    media_files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        write_only=True,
        required=False,
        max_length=5
    )
    media = PlaceMediaSerializer(many=True, read_only=True)
    updated_by = SimpleUserSerializer(read_only=True)
    detail_url = serializers.SerializerMethodField()
    approval_url = serializers.SerializerMethodField()

    class Meta:
        model = PlaceUpdate
        fields = [
            'id', 'place', 'university', 'academic_unit', 'parent', 'name', 'description',
            'history', 'establishment_year', 'place_type', 'relative_location', 'latitude',
            'longitude', 'maps_link', 'created_at', 'updated_at', 'updated_by', 'media',
            'media_files', 'approval_status', 'university_root', 'academic_unit_root',
            'detail_url', 'approval_url'
        ]
        read_only_fields = ['place', 'created_at', 'updated_at', 'updated_by', 'approval_status']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('places:place-update-detail', kwargs={'pk': obj.pk}))

    def get_approval_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('places:place-update-approve', kwargs={'pk': obj.pk}))

    def validate_place_type(self, value):
        if not value:
            return None
        value = value.strip().lower()
        place_type, created = PlaceType.objects.get_or_create(name=value)
        return place_type

    def validate_establishment_year(self, value):
        if value and value > timezone.now().year:
            raise serializers.ValidationError("Establishment year cannot be in the future.")
        return value

    def validate_media_files(self, value):
        max_size = 10 * 1024 * 1024
        for file in value:
            if file.size > max_size:
                raise serializers.ValidationError(f"File {file.name} exceeds maximum size of 10MB.")
        return value

    def validate(self, data):
        try:
            university = data.get('university')
            academic_unit = data.get('academic_unit')
            parent = data.get('parent')
            request = self.context.get('request')

            if academic_unit and university and academic_unit.university != university:
                raise serializers.ValidationError({
                    'academic_unit': 'Academic unit must belong to the selected university.'
                })

            if parent and university and parent.university != university:
                raise serializers.ValidationError({
                    'parent': 'Parent place must belong to the same university.'
                })

            if request.user.admin_level not in ['university', 'app']:
                allowed_fields = ['media_files']
                for field in data:
                    if field not in allowed_fields:
                        raise serializers.ValidationError({
                            field: 'Only media updates are allowed for non-admin users.'
                        })

            place_update = PlaceUpdate(place=self.context['place'], **data)
            place_update.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        logger.debug(f"Received media files for update: {media_files}")
        try:
            place_update = PlaceUpdate.objects.create(
                updated_by=self.context['request'].user,
                place=self.context['place'],
                **validated_data
            )
            for file in media_files:
                try:
                    logger.debug(f"Creating PlaceMedia for update file: {file}")
                    PlaceMedia.objects.create(
                        place_update=place_update,
                        file=file,
                        uploaded_by=self.context['request'].user
                    )
                except DjangoValidationError as e:
                    logger.error(f"Failed to create PlaceMedia for update: {str(e)}")
                    raise serializers.ValidationError(f"Invalid media file: {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error creating PlaceMedia for update: {str(e)}")
                    raise serializers.ValidationError(f"Error saving media file: {str(e)}")
            return place_update
        except DjangoValidationError as e:
            logger.error(f"Validation error creating place update: {str(e)}")
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'non_field_errors': str(e)})