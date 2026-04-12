from rest_framework import serializers
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
        fields = '__all__'


class InpatientAdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    ward_name = serializers.CharField(source='ward.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InpatientAdmission
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'


class PrescriptionExecutionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source='prescription.medication.name',
        read_only=True
    )
    performed_by_name = serializers.CharField(
        source='performed_by.full_name',
        read_only=True
    )

    class Meta:
        model = PrescriptionExecution
        fields = '__all__'
        read_only_fields = ('performed_by',)

    def validate(self, attrs):
        prescription = attrs.get('prescription')
        execution_time = attrs.get('execution_time')
        instance = getattr(self, 'instance', None)

        if prescription and execution_time:
            same_day_qs = PrescriptionExecution.objects.filter(
                prescription=prescription,
                execution_time__date=execution_time.date(),
                status__in=['draft', 'confirmed']
            )

            if instance:
                same_day_qs = same_day_qs.exclude(pk=instance.pk)

            confirmed_count = same_day_qs.count()

            # если создаём draft, тоже учитываем лимит по подтверждённым
            # можно усилить и учитывать draft, если хочешь
            if confirmed_count >= prescription.frequency:
                raise serializers.ValidationError(
                    "На эту дату уже достигнуто максимальное количество подтверждённых выполнений."
                )

        return attrs
    

    def validate(self, attrs):
        prescription = attrs['prescription']
        date = attrs['execution_time'].date()

        count = PrescriptionExecution.objects.filter(
            prescription=prescription,
            execution_time__date=date,
            status__in=['draft','confirmed']
        ).count()

        if count >= prescription.frequency:
            raise serializers.ValidationError("Превышено количество выполнений на сегодня")

        return attrs

    
    

class InpatientProcedureSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = InpatientProcedure
        fields = '__all__'
        read_only_fields = ('price', 'total')


class DailySheetPrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    executions = PrescriptionExecutionSerializer(many=True, read_only=True)
    confirmed_today_count = serializers.SerializerMethodField()
    remaining_today_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id',
            'medication',
            'medication_name',
            'dosage',
            'frequency',
            'duration',
            'route',
            'note',
            'executions',
            'confirmed_today_count',
            'remaining_today_count',
        ]

    def get_confirmed_today_count(self, obj):
        return sum(1 for e in obj.executions.all() if e.status == 'confirmed')

    def get_remaining_today_count(self, obj):
        confirmed = sum(1 for e in obj.executions.all() if e.status == 'confirmed')
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