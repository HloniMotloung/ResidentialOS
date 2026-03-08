from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.permissions import IsEstateAdmin, IsEstateMember
from .models import Unit, Resident
from .serializers import UnitSerializer, ResidentSerializer


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class   = UnitSerializer
    permission_classes = [IsAuthenticated, IsEstateMember]

    def get_queryset(self):
        return Unit.objects.filter(
            estate=self.request.estate
        ).order_by("unit_number")

    def perform_create(self, serializer):
        serializer.save(estate=self.request.estate)


class ResidentViewSet(viewsets.ModelViewSet):
    serializer_class   = ResidentSerializer
    permission_classes = [IsAuthenticated, IsEstateMember]

    def get_queryset(self):
        return Resident.objects.filter(
            estate=self.request.estate
        ).select_related("unit", "user").order_by("last_name", "first_name")

    def get_permissions(self):
        if self.action in ["create", "destroy", "move_out"]:
            return [IsAuthenticated(), IsEstateAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        resident = serializer.save(estate=self.request.estate)
        if resident.unit:
            resident.unit.is_occupied = True
            resident.unit.save(update_fields=["is_occupied"])

    @action(detail=True, methods=["post"], url_path="move-out")
    def move_out(self, request, pk=None):
        resident      = self.get_object()
        move_out_date = request.data.get("move_out_date")
        if not move_out_date:
            return Response(
                {"error": "move_out_date is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        resident.move_out(move_out_date)
        return Response(ResidentSerializer(resident).data)