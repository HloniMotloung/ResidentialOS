from django.utils import timezone
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from apps.core.permissions import IsEstateAdmin

from .models import User, EstateMembership, EstateInvite
from .serializers import (
    LoginSerializer,
    UserSerializer,
    SelfRegisterSerializer,
    ChangePasswordSerializer,
    EstateMembershipSerializer,
    EstateInviteSerializer,
    PendingRegistrationSerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user    = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
            "user":    UserSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
            return Response({"detail": "Successfully logged out."})
        except Exception:
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class SelfRegisterView(APIView):
    """
    POST /api/v1/auth/register/

    Public endpoint — no auth required.
    Handles both invite-based (auto-approved) and
    open (pending approval) registrations.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SelfRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.status == "approved":
            # Invite-based — log them straight in
            refresh = RefreshToken.for_user(user)
            return Response({
                "detail":  "Registration successful. Welcome!",
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
                "user":    UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        else:
            # Pending — no token yet
            return Response({
                "detail": (
                    "Registration submitted successfully. "
                    "Your request is pending approval by the estate manager. "
                    "You will receive an email once your account is activated."
                )
            }, status=status.HTTP_201_CREATED)


class ValidateInviteView(APIView):
    """
    GET /api/v1/auth/invite/{code}/

    Public endpoint — lets the frontend check if an invite is valid
    before showing the registration form.
    """
    permission_classes = [AllowAny]

    def get(self, request, code):
        try:
            invite = EstateInvite.objects.select_related("estate").get(code=code)
            if not invite.is_valid:
                return Response(
                    {"valid": False, "detail": "This invite has expired or been used."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({
                "valid":       True,
                "estate_name": invite.estate.name,
                "estate_slug": invite.estate.slug,
                "role":        invite.get_role_display(),
            })
        except EstateInvite.DoesNotExist:
            return Response(
                {"valid": False, "detail": "Invalid invite code."},
                status=status.HTTP_404_NOT_FOUND
            )


class PendingRegistrationsView(APIView):
    """
    GET  /api/v1/auth/pending/
    Lists all users pending approval for the current estate.
    Only estate managers and admins can see this.
    """
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def get(self, request):
        estate = request.estate
        pending_memberships = EstateMembership.objects.filter(
            estate=estate,
            status="pending"
        ).select_related("user")

        users = [m.user for m in pending_memberships]
        serializer = PendingRegistrationSerializer(
            users,
            many=True,
            context={"request": request, "estate": estate}
        )
        return Response(serializer.data)


class ApproveRegistrationView(APIView):
    """
    POST /api/v1/auth/pending/{membership_id}/approve/
    POST /api/v1/auth/pending/{membership_id}/reject/

    Manager approves or rejects a pending registration.
    """
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def post(self, request, membership_id, action):
        try:
            membership = EstateMembership.objects.select_related(
                "user", "estate"
            ).get(id=membership_id, estate=request.estate)
        except EstateMembership.DoesNotExist:
            return Response(
                {"detail": "Registration not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == "approve":
            membership.approve(request.user)
            # Send approval email
            from apps.notifications.tasks import notify_registration_approved
            notify_registration_approved(membership.user.id, membership.estate.id)
            return Response({
                "detail": f"{membership.user.get_full_name()} has been approved."
            })

        elif action == "reject":
            reason = request.data.get("reason", "")
            membership.reject(request.user)
            # Send rejection email
            from apps.notifications.tasks import notify_registration_rejected
            notify_registration_rejected(
                membership.user.id, membership.estate.id, reason
            )
            return Response({
                "detail": f"{membership.user.get_full_name()} has been rejected."
            })

        return Response(
            {"detail": "Invalid action."},
            status=status.HTTP_400_BAD_REQUEST
        )


class EstateInviteView(APIView):
    """
    GET  /api/v1/auth/invites/       — list all invites for this estate
    POST /api/v1/auth/invites/       — create a new invite link
    """
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def get(self, request):
        invites = EstateInvite.objects.filter(
            estate=request.estate
        ).order_by("-created_at")
        serializer = EstateInviteSerializer(
            invites, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = EstateInviteSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(
            estate=request.estate,
            created_by=request.user,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EstateInviteDetailView(APIView):
    """
    DELETE /api/v1/auth/invites/{id}/  — deactivate an invite
    """
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def delete(self, request, pk):
        try:
            invite = EstateInvite.objects.get(id=pk, estate=request.estate)
            invite.is_active = False
            invite.save()
            return Response({"detail": "Invite deactivated."})
        except EstateInvite.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(
            request.user, data=request.data,
            partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password updated successfully."})


class EstateMembershipListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = EstateMembership.objects.filter(
            user=request.user, is_active=True
        ).select_related("estate")
        return Response(EstateMembershipSerializer(memberships, many=True).data)