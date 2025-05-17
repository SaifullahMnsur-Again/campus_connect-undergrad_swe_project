from rest_framework import permissions

class PlaceOwnerOrAdminPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.admin_level == 'app':
            return True
        if request.user.admin_level == 'university' and obj.university == request.user.university:
            return True
        return obj.created_by == request.user

class UniversityAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.admin_level in ['university', 'app']

    def has_object_permission(self, request, view, obj):
        if request.user.admin_level == 'app':
            return True
        return request.user.admin_level == 'university' and obj.university == request.user.university