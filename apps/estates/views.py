from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Estate
from .serializers import EstateSerializer


class EstateViewSet(viewsets.ModelViewSet):
    serializer_class   = EstateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Estate.objects.all()
        # Regular users only see estates they belong to
        return Estate.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True
        )