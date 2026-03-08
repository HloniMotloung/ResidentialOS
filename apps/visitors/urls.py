from rest_framework.routers import DefaultRouter
from .views import VisitorPreRegistrationViewSet, GateLogViewSet

router = DefaultRouter()
router.register("pre-register", VisitorPreRegistrationViewSet, basename="pre-register")
router.register("gate-log",     GateLogViewSet,                basename="gate-log")

urlpatterns = router.urls