from rest_framework.routers import DefaultRouter
from .views import LevyBillingViewSet

router = DefaultRouter()
router.register("", LevyBillingViewSet, basename="levy")

urlpatterns = router.urls