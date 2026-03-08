from rest_framework.permissions import BasePermission


class IsEstateAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
                hasattr(request, "estate") and
                request.user.is_authenticated and
                request.user.estate_memberships.filter(
                    estate=request.estate,
                    role__in=["trustee","estate_admin", "estate_manager", "superadmin"],
                    is_active=True,
                ).exists()
        )


class IsEstateMember(BasePermission):
    def has_permission(self, request, view):
        return (
                hasattr(request, "estate") and
                request.user.is_authenticated and
                request.user.estate_memberships.filter(
                    estate=request.estate,
                    is_active=True,
                ).exists()
        )


class IsSecurityOfficer(BasePermission):
    def has_permission(self, request, view):
        return (
                hasattr(request, "estate") and
                request.user.is_authenticated and
                request.user.estate_memberships.filter(
                    estate=request.estate,
                    role__in=["security", "estate_admin", "estate_manager"],
                    is_active=True,
                ).exists()
        )