from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet, MedicationViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r"materials", MaterialViewSet)
router.register(r"medications", MedicationViewSet)
router.register(r"stock-movements", StockMovementViewSet)

urlpatterns = router.urls