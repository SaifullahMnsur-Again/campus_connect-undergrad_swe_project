from django.contrib import admin
from .models import Place, PlaceType, PlaceMedia, PlaceUpdate
from django.core.exceptions import ValidationError

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university",
        "academic_unit",
        "place_type",
        "university_root",
        "academic_unit_root",
        "approval_status",
        "created_at",
    )
    list_filter = (
        "university",
        "academic_unit",
        "place_type",
        "university_root",
        "academic_unit_root",
        "approval_status",
    )
    search_fields = ("name", "description", "university__name", "academic_unit__name")
    raw_id_fields = ("university", "academic_unit", "parent", "place_type", "created_by")
    list_select_related = ("university", "academic_unit", "place_type")
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "university",
                    "academic_unit",
                    "parent",
                    "place_type",
                    "university_root",
                    "academic_unit_root",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "history",
                    "establishment_year",
                    "relative_location",
                    "latitude",
                    "longitude",
                    "maps_link",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                    "approval_status",
                )
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            form._errors = e.message_dict
            raise


@admin.register(PlaceType)
class PlaceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)

    def save_model(self, request, obj, form, change):
        obj.name = obj.name.strip().lower()
        super().save_model(request, obj, form, change)


@admin.register(PlaceMedia)
class PlaceMediaAdmin(admin.ModelAdmin):
    list_display = ("place", "place_update", "file", "uploaded_by", "uploaded_at")
    list_filter = ("place", "place_update", "uploaded_by")
    search_fields = ("place__name", "place_update__name", "file")
    raw_id_fields = ("place", "place_update", "uploaded_by")
    readonly_fields = ("uploaded_at",)


@admin.register(PlaceUpdate)
class PlaceUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "place",
        "university",
        "name",
        "approval_status",
        "updated_by",
        "created_at",
    )
    list_filter = ("university", "approval_status", "updated_by")
    search_fields = ("place__name", "name", "university__name")
    raw_id_fields = (
        "place",
        "university",
        "academic_unit",
        "parent",
        "place_type",
        "updated_by",
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "place",
                    "university",
                    "academic_unit",
                    "parent",
                    "name",
                    "place_type",
                    "university_root",
                    "academic_unit_root",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "description",
                    "history",
                    "establishment_year",
                    "relative_location",
                    "latitude",
                    "longitude",
                    "maps_link",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "updated_by",
                    "created_at",
                    "updated_at",
                    "approval_status",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.updated_by:
            obj.updated_by = request.user
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            form._errors = e.message_dict
            raise