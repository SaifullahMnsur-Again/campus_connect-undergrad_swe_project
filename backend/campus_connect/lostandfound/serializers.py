from rest_framework import serializers
from .models import LostItem, FoundItem, LostItemClaim, FoundItemClaim, ItemMedia
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
        try:
            return request.build_absolute_uri(reverse('accounts:user-detail', kwargs={'pk': obj.pk}))
        except:
            return None  # Fallback if user-detail is not defined

class SimpleItemMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemMedia
        fields = ['id', 'file_url']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        return request.build_absolute_uri(reverse('lostandfound:media-access', kwargs={'pk': obj.id}))

class BaseItemSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    media = SimpleItemMediaSerializer(many=True, read_only=True)
    post_type = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    claims_url = serializers.SerializerMethodField()
    resolve_url = serializers.SerializerMethodField()
    approve_url = serializers.SerializerMethodField()

    def get_post_type(self, obj):
        return 'lost' if isinstance(obj, LostItem) else 'found'

    def get_is_admin(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.admin_level in ['university', 'app']
        return False

    def get_detail_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        view_name = 'lostandfound:lost-item-detail' if isinstance(obj, LostItem) else 'lostandfound:found-item-detail'
        return request.build_absolute_uri(reverse(view_name, kwargs={'pk': obj.pk}))

    def get_claims_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        view_name = 'lostandfound:lost-item-claims' if isinstance(obj, LostItem) else 'lostandfound:found-item-claims'
        return request.build_absolute_uri(reverse(view_name, kwargs={'pk': obj.pk}))

    def get_resolve_url(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return None
        # Only owners can resolve
        if obj.user != request.user:
            return None
        view_name = 'lostandfound:lost-item-resolve' if isinstance(obj, LostItem) else 'lostandfound:found-item-resolve'
        return request.build_absolute_uri(reverse(view_name, kwargs={'pk': obj.pk}))

    def get_approve_url(self, obj):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return None
        # Only admins with permission can approve
        user = request.user
        if user.admin_level == 'app' or (user.admin_level == 'university' and obj.university == user.university):
            view_name = 'lostandfound:lost-item-approve' if isinstance(obj, LostItem) else 'lostandfound:found-item-approve'
            return request.build_absolute_uri(reverse(view_name, kwargs={'pk': obj.pk}))
        return None

class SimpleLostItemSerializer(BaseItemSerializer):
    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'title', 'description', 'lost_date', 'approximate_time',
            'location', 'status', 'approval_status', 'created_at', 'updated_at',
            'media', 'post_type', 'is_admin', 'detail_url', 'claims_url',
            'resolve_url', 'approve_url'
        ]

class LostItemSerializer(BaseItemSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'university', 'title', 'description', 'lost_date',
            'approximate_time', 'location', 'status', 'approval_status',
            'created_at', 'updated_at', 'media', 'media_files', 'post_type',
            'is_admin', 'detail_url', 'claims_url', 'resolve_url', 'approve_url'
        ]
        read_only_fields = ['user', 'approval_status', 'created_at', 'updated_at']

    def validate_lost_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Lost date cannot be in the future.")
        return value

    def validate_approximate_time(self, value):
        if value is None:
            return value
        return value

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        lost_item = LostItem.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(lost_item=lost_item, file=file)
        return lost_item

class FoundItemSerializer(BaseItemSerializer):
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.all())
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'university', 'title', 'description', 'found_date',
            'approximate_time', 'location', 'status', 'approval_status',
            'created_at', 'updated_at', 'media', 'media_files', 'post_type',
            'is_admin', 'detail_url', 'claims_url', 'resolve_url', 'approve_url'
        ]
        read_only_fields = ['user', 'approval_status', 'created_at', 'updated_at']

    def validate_found_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Found date cannot be in the future.")
        return value

    def validate_approximate_time(self, value):
        if value is None:
            return value
        return value

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        found_item = FoundItem.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(found_item=found_item, file=file)
        return found_item

class LostItemClaimSerializer(serializers.ModelSerializer):
    claimant = SimpleUserSerializer(read_only=True)
    lost_item = serializers.PrimaryKeyRelatedField(
        queryset=LostItem.objects.filter(approval_status='approved', status='open')
    )
    media = SimpleItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = LostItemClaim
        fields = ['id', 'lost_item', 'claimant', 'description', 'created_at', 'media', 'media_files']
        read_only_fields = ['claimant', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        lost_item = data['lost_item']
        if lost_item.user == request.user:
            raise serializers.ValidationError("You cannot claim your own lost item.")
        if LostItemClaim.objects.filter(lost_item=lost_item, claimant=request.user).exists():
            raise serializers.ValidationError("You have already claimed this item.")
        return data

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        claim = LostItemClaim.objects.create(**validated_data)
        for file in media_files:
            ItemMedia.objects.create(lost_item_claim=claim, file=file)
        return claim

class FoundItemClaimSerializer(serializers.ModelSerializer):
    claimant = SimpleUserSerializer(read_only=True)
    found_item = serializers.PrimaryKeyRelatedField(
        queryset=FoundItem.objects.filter(approval_status='approved', status='open')
    )
    media = SimpleItemMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = FoundItemClaim
        fields = ['id', 'found_item', 'claimant', 'description', 'created_at', 'media', 'media_files']
        read_only_fields = ['claimant', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        found_item = data['found_item']
        if found_item.user == request.user:
            raise serializers.ValidationError("You cannot claim your own found item.")
        if FoundItemClaim.objects.filter(found_item=found_item, claimant=request.user).exists():
            raise serializers.ValidationError("You have already claimed this item.")
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
        queryset=User.objects.all(), required=False, allow_null=True
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
        queryset=User.objects.all(), required=False, allow_null=True
    )

    def validate(self, data):
        status = data['status']
        resolved_by = data.get('resolved_by')
        if status == 'returned' and not resolved_by:
            raise serializers.ValidationError("Resolved_by is required when marking as 'returned'.")
        if status == 'externally_returned' and resolved_by:
            raise serializers.ValidationError("Resolved_by should not be set when marking as 'externally_returned'.")
        return data

class LostItemApprovalSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(choices=['approved', 'rejected'])

class FoundItemApprovalSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(choices=['approved', 'rejected'])

class HistorySerializer(serializers.Serializer):
    posts = serializers.SerializerMethodField()
    claims_made = serializers.SerializerMethodField()
    claims_received = serializers.SerializerMethodField()

    def get_posts(self, obj):
        request = self.context['request']
        lost_items = LostItem.objects.filter(user=request.user)
        found_items = FoundItem.objects.filter(user=request.user)
        lost_serializer = SimpleLostItemSerializer(lost_items, many=True, context={'request': request})
        found_serializer = FoundItemSerializer(found_items, many=True, context={'request': request})
        all_posts = lost_serializer.data + found_serializer.data
        all_posts.sort(key=lambda x: x['created_at'], reverse=True)
        return all_posts

    def get_claims_made(self, obj):
        request = self.context['request']
        lost_claims = LostItemClaim.objects.filter(claimant=request.user)
        found_claims = FoundItemClaim.objects.filter(claimant=request.user)
        lost_serializer = LostItemClaimSerializer(lost_claims, many=True, context={'request': request})
        found_serializer = FoundItemClaimSerializer(found_claims, many=True, context={'request': request})
        all_claims = lost_serializer.data + found_serializer.data
        all_claims.sort(key=lambda x: x['created_at'], reverse=True)
        return all_claims

    def get_claims_received(self, obj):
        request = self.context['request']
        lost_items = LostItem.objects.filter(user=request.user)
        found_items = FoundItem.objects.filter(user=request.user)
        lost_claims = LostItemClaim.objects.filter(lost_item__in=lost_items)
        found_claims = FoundItemClaim.objects.filter(found_item__in=found_items)
        lost_serializer = LostItemClaimSerializer(lost_claims, many=True, context={'request': request})
        found_serializer = FoundItemClaimSerializer(found_claims, many=True, context={'request': request})
        all_claims = lost_serializer.data + found_serializer.data
        all_claims.sort(key=lambda x: x['created_at'], reverse=True)
        return all_claims