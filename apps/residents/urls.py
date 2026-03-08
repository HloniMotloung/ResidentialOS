from rest_framework.routers import DefaultRouter
from .views import UnitViewSet, ResidentViewSet

router = DefaultRouter()
router.register("units",     UnitViewSet,     basename="unit")
router.register("",          ResidentViewSet, basename="resident")

urlpatterns = router.urls