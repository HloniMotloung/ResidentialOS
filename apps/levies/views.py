from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.permissions import IsEstateAdmin, IsEstateMember
from .models import LevyBilling, Payment
from .serializers import LevyBillingSerializer, PaymentSerializer


class LevyBillingViewSet(viewsets.ModelViewSet):
    serializer_class   = LevyBillingSerializer
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def get_queryset(self):
        qs = LevyBilling.objects.filter(
            estate=self.request.estate
        ).select_related("unit", "resident").prefetch_related("payments")

        status_ = self.request.query_params.get("status")
        if status_:
            qs = qs.filter(status=status_)
        return qs.order_by("-billing_month")

    def perform_create(self, serializer):
        serializer.save(estate=self.request.estate)

    @action(detail=False, methods=["get"], url_path="arrears")
    def arrears(self, request):
        overdue = LevyBilling.objects.filter(
            estate=request.estate,
            status__in=["overdue", "outstanding", "partial"]
        ).select_related("unit", "resident").order_by("-billing_month")
        return Response(LevyBillingSerializer(overdue, many=True).data)

    @action(detail=True, methods=["post"], url_path="payments")
    def add_payment(self, request, pk=None):
        billing    = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            estate=request.estate,
            levy_billing=billing,
            recorded_by=request.user,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)