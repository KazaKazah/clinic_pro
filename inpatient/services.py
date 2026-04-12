from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone

from .models import InpatientAdmission, PrescriptionExecution, InpatientProcedure


def calculate_bed_days(admission: InpatientAdmission) -> int:
    end_dt = admission.discharge_date or timezone.now()

    delta_days = (end_dt.date() - admission.admission_date.date()).days + 1
    return max(delta_days, 1)


def calculate_bed_cost(admission: InpatientAdmission) -> Decimal:
    if not admission.ward:
        return Decimal("0.00")

    bed_days = calculate_bed_days(admission)
    return Decimal(bed_days) * Decimal(admission.ward.daily_price)


def calculate_medication_cost(admission: InpatientAdmission) -> Decimal:
    qs = PrescriptionExecution.objects.filter(
        prescription__admission=admission
    ).annotate(
        line_total=ExpressionWrapper(
            F('qty') * F('prescription__medication__sale_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )

    total = qs.aggregate(total=Sum('line_total'))['total']
    return total or Decimal("0.00")


def calculate_procedure_cost(admission: InpatientAdmission) -> Decimal:
    total = InpatientProcedure.objects.filter(
        admission=admission
    ).aggregate(total=Sum('total'))['total']

    return total or Decimal("0.00")


def recalculate_admission_cost(admission: InpatientAdmission) -> InpatientAdmission:
    admission.bed_cost = calculate_bed_cost(admission)
    admission.medication_cost = calculate_medication_cost(admission)
    admission.procedure_cost = calculate_procedure_cost(admission)
    admission.total_cost = (
        admission.bed_cost +
        admission.medication_cost +
        admission.procedure_cost
    )
    admission.save(
        update_fields=['bed_cost', 'medication_cost', 'procedure_cost', 'total_cost']
    )
    return admission