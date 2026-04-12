from rest_framework.routers import DefaultRouter
from .views import (
    WardViewSet,
    InpatientAdmissionViewSet,
    PrescriptionViewSet,
    PrescriptionExecutionViewSet,
    InpatientProcedureViewSet,
)

router = DefaultRouter()
router.register(r'wards', WardViewSet)
router.register(r'inpatient-admissions', InpatientAdmissionViewSet, basename='inpatient-admission')
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'prescription-executions', PrescriptionExecutionViewSet)
router.register(r'inpatient-procedures', InpatientProcedureViewSet)


urlpatterns = router.urls