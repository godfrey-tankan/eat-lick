from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
class IsSupportMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='SupportMembers').exists()
class IsInquirer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Inquirers').exists()