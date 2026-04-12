from rest_framework.routers import DefaultRouter
from .views import OutpatientVisitViewSet

router = DefaultRouter()
router.register(r'outpatient-visits', OutpatientVisitViewSet)

urlpatterns = router.urls