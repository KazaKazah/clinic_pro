from django.db.models import Prefetch
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Ward,
    InpatientAdmission,
    Prescription,
    PrescriptionExecution,
    InpatientProcedure,
)
from .serializers import (
    WardSerializer,
    InpatientAdmissionSerializer,
    PrescriptionSerializer,
    PrescriptionExecutionSerializer,
    InpatientProcedureSerializer,
    DailySheetPrescriptionSerializer,
    DailySheetResponseSerializer,
)


class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.all().order_by("name")
    serializer_class = WardSerializer


class InpatientAdmissionViewSet(viewsets.ModelViewSet):
    queryset = InpatientAdmission.objects.select_related(
        "patient",
        "doctor",
        "ward"
    ).order_by("-id")
    serializer_class = InpatientAdmissionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if getattr(self, "action", None) == "list":
            queryset = queryset.filter(status="active")
        return queryset

    @action(detail=True, methods=["get"])
    def daily_sheet(self, request, pk=None):
        admission = self.get_object()

        date_str = request.query_params.get("date")
        target_date = parse_date(date_str) if date_str else None

        if not target_date:
            return Response(
                {"detail": "Передайте дату в формате YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        executions_qs = PrescriptionExecution.objects.filter(
            execution_time__date=target_date
        ).select_related(
            "performed_by",
            "prescription",
            "prescription__medication",
        ).order_by("execution_time")

        prescriptions = Prescription.objects.filter(
            admission=admission
        ).select_related("medication").prefetch_related(
            Prefetch("executions", queryset=executions_qs)
        ).order_by("-id")

        procedures = InpatientProcedure.objects.filter(
            admission=admission,
            procedure_date__date=target_date
        ).select_related("service").order_by("procedure_date")

        data = {
            "admission_id": admission.id,
            "patient_id": admission.patient_id,
            "patient_name": admission.patient.full_name,
            "doctor_name": admission.doctor.full_name if admission.doctor else None,
            "ward_name": admission.ward.name if admission.ward else None,
            "date": target_date,
            "prescriptions": DailySheetPrescriptionSerializer(prescriptions, many=True).data,
            "procedures": InpatientProcedureSerializer(procedures, many=True).data,
        }

        return Response(data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all().order_by("-id")
    serializer_class = PrescriptionSerializer


class PrescriptionExecutionViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionExecution.objects.all().order_by("-id")
    serializer_class = PrescriptionExecutionSerializer

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(performed_by=user)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "draft":
            return Response(
                {"detail": "Подтвердить можно только запись в статусе draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj.status = "confirmed"
        obj.save()
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "confirmed":
            return Response(
                {"detail": "Отменить можно только подтверждённую запись."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj.status = "cancelled"
        obj.save()
        return Response(self.get_serializer(obj).data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.status != "draft":
            return Response(
                {"detail": "Удалять можно только черновик."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)


class InpatientProcedureViewSet(viewsets.ModelViewSet):
    queryset = InpatientProcedure.objects.all().order_by("-id")
    serializer_class = InpatientProcedureSerializer

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "draft":
            return Response(
                {"detail": "Подтвердить можно только запись в статусе draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj.status = "confirmed"
        obj.save()
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "confirmed":
            return Response(
                {"detail": "Отменить можно только подтверждённую запись."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj.status = "cancelled"
        obj.save()
        return Response(self.get_serializer(obj).data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.status != "draft":
            return Response(
                {"detail": "Удалять можно только черновик."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)