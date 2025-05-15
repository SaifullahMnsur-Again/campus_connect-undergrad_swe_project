from rest_framework import serializers
from .models import LostItem, FoundItem, ItemMedia, LostItemClaim, FoundItemClaim
from universities.models import University
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'detail_url']

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('user-detail', kwargs={'pk': obj.pk}))

class SimpleItemMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemMedia
        fields = ['id', 'file_url']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('media-access', kwargs={'pk': obj.id}))

class SimpleLostItemSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    detail_url = serializers.SerializerMethodField()
    media = SimpleItemMediaSerializer(many=True, read_only=True)

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'title', 'description', 'lost_date',
            'approximate_time', 'location', 'status', 'created_at',
            'media', 'detail_url'
        ]

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('lost-item-detail', kwargs={'pk': obj.pk}))

class ItemMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemMedia
        fields = ['id', 'file_url']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('media-access', kwargs={'pk': obj.id}))

class LostItemSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    media = ItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'university', 'title', 'description', 'lost_date',
            'approximate_time', 'location', 'status', 'created_at', 'media', 'media_files'
        ]

    def validate_lost_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Lost date cannot be in the future.")
        return value

    def validate_approximate_time(self, value):
        if value is None:
            return value
        # Ensure time is in valid format (handled by TimeField)
        return value

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        lost_item = LostItem.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(lost_item=lost_item, file=file)
        return lost_item

class FoundItemSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    media = ItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'university', 'title', 'description', 'found_date',
            'approximate_time', 'location', 'status', 'created_at', 'media', 'media_files'
        ]

    def validate_found_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Found date cannot be in the future.")
        return value

    def validate_approximate_time(self, value):
        if value is None:
            return value
        # Ensure time is in valid format (handled by TimeField)
        return value

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        found_item = FoundItem.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(found_item=found_item, file=file)
        return found_item

class LostItemClaimSerializer(serializers.ModelSerializer):
    claimant = SimpleUserSerializer(read_only=True)
    lost_item = serializers.PrimaryKeyRelatedField(queryset=LostItem.objects.all())
    media = ItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LostItemClaim
        fields = ['id', 'lost_item', 'claimant', 'description', 'created_at', 'media', 'media_files']

    def validate(self, data):
        request = self.context.get('request')
        lost_item = data['lost_item']
        if lost_item.user == request.user:
            raise serializers.ValidationError("You cannot claim your own lost item.")
        if lost_item.status != 'open':
            raise serializers.ValidationError("This item is not open for claims.")
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        claim = LostItemClaim.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(lost_item_claim=claim, file=file)
        return claim

class FoundItemClaimSerializer(serializers.ModelSerializer):
    claimant = SimpleUserSerializer(read_only=True)
    found_item = serializers.PrimaryKeyRelatedField(queryset=FoundItem.objects.all())
    media = ItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = FoundItemClaim
        fields = ['id', 'found_item', 'claimant', 'description', 'created_at', 'media', 'media_files']

    def validate(self, data):
        request = self.context.get('request')
        found_item = data['found_item']
        if found_item.user == request.user:
            raise serializers.ValidationError("You cannot claim your own found item.")
        if found_item.status != 'open':
            raise serializers.ValidationError("This item is not open for claims.")
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        claim = FoundItemClaim.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(found_item_claim=claim, file=file)
        return claim

class LostItemResolveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['found', 'externally_found'])
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    def validate(self, data):
        status = data['status']
        resolved_by = data.get('resolved_by')
        if status == 'found' and not resolved_by:
            raise serializers.ValidationError("Resolved_by is required when marking as 'found'.")
        if status == 'externally_found' and resolved_by:
            raise serializers.ValidationError("Resolved_by should not be set when marking as 'externally_found'.")
        return data

class FoundItemResolveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['returned', 'externally_returned'])
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    def validate(self, data):
        status = data['status']
        resolved_by = data.get('resolved_by')
        if status == 'returned' and not resolved_by:
            raise serializers.ValidationError("Resolved_by is required when marking as 'returned'.")
        if status == 'externally_returned' and resolved_by:
            raise serializers.ValidationError("Resolved_by should not be set when marking as 'externally_returned'.")
        return data