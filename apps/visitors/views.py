from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.permissions import IsSecurityOfficer, IsEstateMember
from .models import VisitorPreRegistration, GateLog
from .serializers import VisitorPreRegistrationSerializer, GateLogSerializer


class VisitorPreRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class   = VisitorPreRegistrationSerializer
    permission_classes = [IsAuthenticated, IsEstateMember]

    def get_queryset(self):
        qs = VisitorPreRegistration.objects.filter(
            estate=self.request.estate
        ).select_related("resident").order_by("-expected_arrival")

        # Residents only see their own
        if not self.request.user.estate_memberships.filter(
                estate=self.request.estate,
                role__in=["estate_admin", "estate_manager", "security"]
        ).exists():
            qs = qs.filter(resident__user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(estate=self.request.estate)


class GateLogViewSet(viewsets.ModelViewSet):
    serializer_class   = GateLogSerializer
    permission_classes = [IsAuthenticated, IsSecurityOfficer]

    def get_queryset(self):
        return GateLog.objects.filter(
            estate=self.request.estate
        ).select_related("host_resident", "security_officer").order_by("-entry_time")

    def perform_create(self, serializer):
        access_code = self.request.data.get("access_code")
        pre_reg     = None
        if access_code:
            try:
                pre_reg = VisitorPreRegistration.objects.get(
                    estate=self.request.estate,
                    access_code=access_code,
                )
                if pre_reg.is_valid:
                    pre_reg.is_used = True
                    pre_reg.save(update_fields=["is_used"])
            except VisitorPreRegistration.DoesNotExist:
                pass
        serializer.save(
            estate=self.request.estate,
            security_officer=self.request.user,
            pre_registration=pre_reg,
        )

    @action(detail=True, methods=["patch"], url_path="exit")
    def log_exit(self, request, pk=None):
        gate_log = self.get_object()
        if gate_log.exit_time:
            return Response(
                {"error": "Exit already recorded."},
                status=status.HTTP_400_BAD_REQUEST
            )
        gate_log.log_exit()
        return Response(GateLogSerializer(gate_log).data)