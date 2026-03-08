from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.permissions import IsEstateAdmin, IsEstateMember
from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class   = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsEstateMember]

    def get_queryset(self):
        qs = Announcement.objects.filter(estate=self.request.estate)
        # Residents only see published announcements
        if not self.request.user.estate_memberships.filter(
                estate=self.request.estate,
                role__in=["estate_admin", "estate_manager"]
        ).exists():
            qs = qs.filter(is_published=True)
        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "publish"]:
            return [IsAuthenticated(), IsEstateAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(estate=self.request.estate, created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        announcement = self.get_object()
        if announcement.is_published:
            return Response(
                {"detail": "Already published."},
                status=status.HTTP_400_BAD_REQUEST
            )
        announcement.publish()
        return Response(AnnouncementSerializer(announcement).data)