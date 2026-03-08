from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsEstateAdmin, IsEstateMember
from .models import MaintenanceRequest, MaintenanceComment
from .serializers import MaintenanceRequestSerializer, MaintenanceCommentSerializer


class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated, IsEstateMember]

    def get_queryset(self):
        qs = MaintenanceRequest.objects.filter(
            estate=self.request.estate
        ).select_related("unit", "reported_by", "assigned_to")

        # Residents only see their own requests
        if not self.request.user.estate_memberships.filter(
                estate=self.request.estate, role__in=["estate_admin", "estate_manager"]
        ).exists():
            qs = qs.filter(reported_by__user=self.request.user)

        priority = self.request.query_params.get("priority")
        status_  = self.request.query_params.get("status")
        if priority:
            qs = qs.filter(priority=priority)
        if status_:
            qs = qs.filter(status=status_)

        return qs.order_by(
            # Critical and high first
            "priority",
            "-created_at"
        )

    def perform_create(self, serializer):
        serializer.save(estate=self.request.estate)

    @action(detail=True, methods=["patch"], url_path="assign",
            permission_classes=[IsAuthenticated, IsEstateAdmin])
    def assign(self, request, pk=None):
        req     = self.get_object()
        user_id = request.data.get("user_id")
        from django.contrib.auth import get_user_model
        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        req.assign(user)
        return Response(MaintenanceRequestSerializer(req).data)

    @action(detail=True, methods=["patch"], url_path="status",
            permission_classes=[IsAuthenticated, IsEstateAdmin])
    def update_status(self, request, pk=None):
        req        = self.get_object()
        new_status = request.data.get("status")
        cost       = request.data.get("actual_cost")
        if new_status not in dict(MaintenanceRequest.STATUS):
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == "resolved":
            req.resolve(cost)
        else:
            req.status = new_status
            req.save(update_fields=["status"])
        return Response(MaintenanceRequestSerializer(req).data)

    @action(detail=True, methods=["post", "get"], url_path="comments")
    def comments(self, request, pk=None):
        req = self.get_object()
        if request.method == "GET":
            qs = req.comments.all()
            # Residents don't see internal comments
            if not request.user.estate_memberships.filter(
                    estate=request.estate, role__in=["estate_admin", "estate_manager"]
            ).exists():
                qs = qs.filter(is_internal=False)
            return Response(MaintenanceCommentSerializer(qs, many=True).data)

        serializer = MaintenanceCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            estate=self.request.estate,
            request=req,
            author=request.user,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)