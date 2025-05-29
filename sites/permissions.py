from rest_framework import permissions

class IsSiteOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'site'):
            site = obj.site
        else:
            site = obj

        return site.members.filter(
            user=request.user,
            role__in=['owner', 'admin'],
            is_active=True
        ).exists()