from django.contrib import admin
from .models import LostItem, FoundItem, ItemMedia, LostItemClaim, FoundItemClaim

@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'university', 'status', 'lost_date', 'created_at']
    list_filter = ['status', 'university']
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']

@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'university', 'status', 'found_date', 'created_at']
    list_filter = ['status', 'university']
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']

@admin.register(ItemMedia)
class ItemMediaAdmin(admin.ModelAdmin):
    list_display = ['file', 'lost_item', 'found_item', 'lost_item_claim', 'found_item_claim', 'uploaded_at']
    search_fields = ['lost_item__title', 'found_item__title', 'lost_item_claim__description', 'found_item_claim__description']
    ordering = ['-uploaded_at']

@admin.register(LostItemClaim)
class LostItemClaimAdmin(admin.ModelAdmin):
    list_display = ['lost_item', 'claimant', 'created_at']
    search_fields = ['lost_item__title', 'claimant__email']
    ordering = ['-created_at']

@admin.register(FoundItemClaim)
class FoundItemClaimAdmin(admin.ModelAdmin):
    list_display = ['found_item', 'claimant', 'created_at']
    search_fields = ['found_item__title', 'claimant__email']
    ordering = ['-created_at']