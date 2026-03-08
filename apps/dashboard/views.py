from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.permissions import IsEstateAdmin
from apps.residents.models import Unit, Resident
from apps.levies.models import LevyBilling
from apps.maintenance.models import MaintenanceRequest
from apps.visitors.models import GateLog


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsEstateAdmin]

    def get(self, request):
        estate      = request.estate
        today       = timezone.now().date()
        month_start = today.replace(day=1)

        units     = Unit.objects.filter(estate=estate)
        residents = Resident.objects.filter(estate=estate, is_active=True)
        billings  = LevyBilling.objects.filter(estate=estate)
        maint     = MaintenanceRequest.objects.filter(estate=estate)
        gate      = GateLog.objects.filter(estate=estate)

        return Response({
            "units": {
                "total":    units.count(),
                "occupied": units.filter(is_occupied=True).count(),
                "vacant":   units.filter(is_occupied=False).count(),
            },
            "residents": {
                "total":   residents.count(),
                "owners":  residents.filter(resident_type="owner").count(),
                "tenants": residents.filter(resident_type="tenant").count(),
            },
            "levies": {
                "outstanding_count":    billings.filter(status="outstanding").count(),
                "overdue_count":        billings.filter(status="overdue").count(),
                "outstanding_amount":   billings.filter(
                    status__in=["outstanding", "overdue", "partial"]
                ).aggregate(t=Sum("amount_due"))["t"] or 0,
                "collected_this_month": billings.filter(
                    billing_month=month_start, status="paid"
                ).aggregate(t=Sum("amount_due"))["t"] or 0,
            },
            "maintenance": {
                "open":        maint.filter(status="open").count(),
                "in_progress": maint.filter(status="in_progress").count(),
                "critical":    maint.filter(
                    priority="critical",
                    status__in=["open", "in_progress"]
                ).count(),
            },
            "visitors": {
                "inside_now":  gate.filter(exit_time__isnull=True).count(),
                "today_total": gate.filter(entry_time__date=today).count(),
                "month_total": gate.filter(entry_time__date__gte=month_start).count(),
            },
        })