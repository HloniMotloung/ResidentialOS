from rest_framework.routers import DefaultRouter
from .views import EstateViewSet

router = DefaultRouter()
router.register("", EstateViewSet, basename="estate")

urlpatterns = router.urls