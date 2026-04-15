from rest_framework import serializers
from inventory.services import get_material_stock

from .models import (
    Ward,
    InpatientAdmission,
    Prescription,
    PrescriptionExecution,
    InpatientProcedure,
)


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = "__all__"


class InpatientAdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    ward_name = serializers.CharField(source="ward.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = InpatientAdmission
        fields = "__all__"


class PrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)

    class Meta:
        model = Prescription
        fields = "__all__"


class PrescriptionExecutionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source="prescription.medication.name",
        read_only=True
    )
    performed_by_name = serializers.CharField(
        source="performed_by.full_name",
        read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    class Meta:
        model = PrescriptionExecution
        fields = "__all__"
        read_only_fields = ("performed_by",)

    def validate_qty(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество должно быть не меньше 1.")
        return value

    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        prescription = attrs.get("prescription") or getattr(instance, "prescription", None)
        execution_time = attrs.get("execution_time") or getattr(instance, "execution_time", None)
        new_status = attrs.get("status", getattr(instance, "status", "draft"))

        if not prescription or not execution_time:
            return attrs
        
        if prescription:
            stock = get_material_stock(prescription.medication)

        qty = attrs.get("qty") or getattr(instance, "qty", 1)

        if prescription.medication.stock_qty < qty:
            raise serializers.ValidationError(
                "Недостаточно лекарства на складе."
            )

        if instance and instance.status == "confirmed":
            protected_changed = (
                ("prescription" in attrs and attrs["prescription"].id != instance.prescription_id) or
                ("execution_time" in attrs and attrs["execution_time"] != instance.execution_time) or
                ("qty" in attrs and attrs["qty"] != instance.qty)
            )

            if protected_changed and new_status == "confirmed":
                raise serializers.ValidationError(
                    "Нельзя редактировать подтверждённое выполнение. Сначала отмените запись."
                )

        
        same_day_qs = PrescriptionExecution.objects.filter(
            prescription=prescription,
            execution_time__date=execution_time.date(),
            status__in=["draft", "confirmed"],
        )

        if instance:
            same_day_qs = same_day_qs.exclude(pk=instance.pk)

        if same_day_qs.count() >= prescription.frequency:
            raise serializers.ValidationError(
                "Превышено допустимое количество выполнений на сегодня."
            )

        return attrs


class InpatientProcedureSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    class Meta:
        model = InpatientProcedure
        fields = "__all__"
        read_only_fields = ("price", "total")

    def validate_qty(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество должно быть не меньше 1.")
        return value

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        new_status = attrs.get("status", getattr(instance, "status", "draft"))

        if instance and instance.status == "confirmed":
            protected_changed = (
                ("service" in attrs and attrs["service"].id != instance.service_id) or
                ("procedure_date" in attrs and attrs["procedure_date"] != instance.procedure_date) or
                ("qty" in attrs and attrs["qty"] != instance.qty)
            )

            if protected_changed and new_status == "confirmed":
                raise serializers.ValidationError(
                    "Нельзя редактировать подтверждённую процедуру. Сначала отмените запись."
                )

        return attrs


class DailySheetPrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)
    executions = PrescriptionExecutionSerializer(many=True, read_only=True)
    confirmed_today_count = serializers.SerializerMethodField()
    remaining_today_count = serializers.SerializerMethodField()
    stock_qty = serializers.SerializerMethodField()
    min_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id",
            "medication",
            "medication_name",
            "dosage",
            "frequency",
            "duration",
            "route",
            "note",
            "executions",
            "confirmed_today_count",
            "remaining_today_count",
            "stock_qty",
            "min_stock",
            "is_low_stock",
        ]

    def get_stock_qty(self, obj):
        return obj.medication.stock_qty

    def get_min_stock(self, obj):
        return obj.medication.min_stock

    def get_is_low_stock(self, obj):
        return obj.medication.stock_qty <= obj.medication.min_stock

    def get_confirmed_today_count(self, obj):
        return sum(1 for e in obj.executions.all() if e.status == "confirmed")

    def get_remaining_today_count(self, obj):
        confirmed = sum(1 for e in obj.executions.all() if e.status == "confirmed")
        remaining = obj.frequency - confirmed
        return remaining if remaining > 0 else 0


class DailySheetResponseSerializer(serializers.Serializer):
    admission_id = serializers.IntegerField()
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    doctor_name = serializers.CharField(allow_null=True)
    ward_name = serializers.CharField(allow_null=True)
    date = serializers.DateField()
    prescriptions = DailySheetPrescriptionSerializer(many=True)
    procedures = InpatientProcedureSerializer(many=True)