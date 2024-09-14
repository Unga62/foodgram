from rest_framework import permissions


class CreateUpadateDeletePermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        return (
            request.method in permissions.SAFE_METHODS
            or is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        is_authenticated = request.user and request.user.is_authenticated
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or (is_authenticated and request.user.is_admin)
        )
