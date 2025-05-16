from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import LostItem, FoundItem, ItemMedia, LostItemClaim, FoundItemClaim
from django.utils import timezone
from datetime import timedelta

# Custom filter for date ranges
class DateRangeFilter(admin.SimpleListFilter):
    title = 'Date Range'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'Past Week'),
            ('month', 'Past Month'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(created_at__date=timezone.now().date())
        if self.value() == 'week':
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=7))
        if self.value() == 'month':
            return queryset.filter(created_at__gte=timezone.now() - timedelta(days=30))
        return queryset

# Inline for ItemMedia
class ItemMediaInline(admin.TabularInline):
    model = ItemMedia
    fields = ['file_preview', 'file', 'uploaded_at']
    readonly_fields = ['file_preview', 'uploaded_at']
    extra = 0

    def file_preview(self, obj):
        if obj.file:
            if obj.file.name.endswith(('.jpg', '.jpeg', '.png')):
                return format_html('<img src="{}" style="max-height: 100px;" />', obj.file.url)
            elif obj.file.name.endswith(('.mp4', '.mov')):
                return format_html('<a href="{}">View Video</a>', obj.file.url)
        return "No media"
    file_preview.short_description = "Media Preview"

# Inline for LostItemClaim
class LostItemClaimInline(admin.TabularInline):
    model = LostItemClaim
    fields = ['claimant', 'description', 'created_at', 'media_count']
    readonly_fields = ['claimant', 'created_at', 'media_count']
    extra = 0

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"

# Inline for FoundItemClaim
class FoundItemClaimInline(admin.TabularInline):
    model = FoundItemClaim
    fields = ['claimant', 'description', 'created_at', 'media_count']
    readonly_fields = ['claimant', 'created_at', 'media_count']
    extra = 0

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'university', 'status', 'approval_status', 'lost_date', 'created_at', 'media_count']
    list_filter = ['status', 'approval_status', 'university', DateRangeFilter]
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']
    inlines = [ItemMediaInline, LostItemClaimInline]
    readonly_fields = ['created_at', 'updated_at', 'resolved_by']
    fieldsets = (
        (None, {
            'fields': ('title', 'user', 'university')
        }),
        ('Details', {
            'fields': ('description', 'lost_date', 'approximate_time', 'location')
        }),
        ('Status', {
            'fields': ('status', 'approval_status', 'resolved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['approve_items', 'reject_items', 'mark_found', 'mark_externally_found']

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"

    def approve_items(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to approve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.approval_status = 'approved'
            item.save()
        self.message_user(request, "Selected items approved.")
    approve_items.short_description = "Approve selected items"

    def reject_items(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to reject items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.approval_status = 'rejected'
            item.save()
        self.message_user(request, "Selected items rejected.")
    reject_items.short_description = "Reject selected items"

    def mark_found(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to resolve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.status = 'found'
            item.resolved_by = request.user
            item.save()
        self.message_user(request, "Selected items marked as found.")
    mark_found.short_description = "Mark selected items as found"

    def mark_externally_found(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to resolve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.status = 'externally_found'
            item.resolved_by = None
            item.save()
        self.message_user(request, "Selected items marked as externally found.")
    mark_externally_found.short_description = "Mark selected items as externally found"

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'university', 'status', 'approval_status', 'found_date', 'created_at', 'media_count']
    list_filter = ['status', 'approval_status', 'university', DateRangeFilter]
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']
    inlines = [ItemMediaInline, FoundItemClaimInline]
    readonly_fields = ['created_at', 'updated_at', 'resolved_by']
    fieldsets = (
        (None, {
            'fields': ('title', 'user', 'university')
        }),
        ('Details', {
            'fields': ('description', 'found_date', 'approximate_time', 'location')
        }),
        ('Status', {
            'fields': ('status', 'approval_status', 'resolved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['approve_items', 'reject_items', 'mark_returned', 'mark_externally_returned']

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"

    def approve_items(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to approve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.approval_status = 'approved'
            item.save()
        self.message_user(request, "Selected items approved.")
    approve_items.short_description = "Approve selected items"

    def reject_items(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to reject items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.approval_status = 'rejected'
            item.save()
        self.message_user(request, "Selected items rejected.")
    reject_items.short_description = "Reject selected items"

    def mark_returned(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to resolve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.status = 'returned'
            item.resolved_by = request.user
            item.save()
        self.message_user(request, "Selected items marked as returned.")
    mark_returned.short_description = "Mark selected items as returned"

    def mark_externally_returned(self, request, queryset):
        if not request.user.admin_level in ['app', 'university']:
            self.message_user(request, "You do not have permission to resolve items.", level='error')
            return
        for item in queryset:
            if request.user.admin_level == 'university' and item.university != request.user.university:
                continue
            item.status = 'externally_returned'
            item.resolved_by = None
            item.save()
        self.message_user(request, "Selected items marked as externally returned.")
    mark_externally_returned.short_description = "Mark selected items as externally returned"

@admin.register(ItemMedia)
class ItemMediaAdmin(admin.ModelAdmin):
    list_display = ['file_preview', 'lost_item', 'found_item', 'lost_item_claim', 'found_item_claim', 'uploaded_at']
    search_fields = ['lost_item__title', 'found_item__title', 'lost_item_claim__description', 'found_item_claim__description']
    ordering = ['-uploaded_at']
    readonly_fields = ['file_preview', 'uploaded_at']

    def file_preview(self, obj):
        if obj.file:
            if obj.file.name.endswith(('.jpg', '.jpeg', '.png')):
                return format_html('<img src="{}" style="max-height: 100px;" />', obj.file.url)
            elif obj.file.name.endswith(('.mp4', '.mov')):
                return format_html('<a href="{}">View Video</a>', obj.file.url)
        return "No media"
    file_preview.short_description = "Media Preview"

@admin.register(LostItemClaim)
class LostItemClaimAdmin(admin.ModelAdmin):
    list_display = ['lost_item', 'claimant', 'created_at', 'media_count']
    search_fields = ['lost_item__title', 'claimant__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    inlines = [ItemMediaInline]

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"

@admin.register(FoundItemClaim)
class FoundItemClaimAdmin(admin.ModelAdmin):
    list_display = ['found_item', 'claimant', 'created_at', 'media_count']
    search_fields = ['found_item__title', 'claimant__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    inlines = [ItemMediaInline]

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Files"