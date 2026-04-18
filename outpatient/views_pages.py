from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from patients.models import Patient
from .forms import CreateVisitAppointmentForm, MedicalRecordForm
from .models import Appointment, Doctor, MedicalRecord


@login_required
@transaction.atomic
def visit_create_page(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    form = CreateVisitAppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appointment = form.save(patient=patient, registrar=request.user)
        messages.success(request, "Обращение, прием и оплата созданы. Карточка отправлена врачу.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)
    return render(request, "outpatient/visit_form.html", {"form": form, "patient": patient})


@login_required
def appointment_detail_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "visit", "doctor", "service", "payment"),
        id=appointment_id,
    )
    return render(request, "outpatient/appointment_detail.html", {"appointment": appointment})


@login_required
def doctor_queue_page(request):
    doctor = Doctor.objects.filter(user=request.user, is_active=True).first()
    appointments = Appointment.objects.none()
    if doctor:
        appointments = (
            Appointment.objects.filter(doctor=doctor, status__in=["waiting", "in_progress"])
            .select_related("patient", "visit", "service", "payment")
            .order_by("appointment_date", "appointment_time")
        )
    return render(request, "outpatient/doctor_queue.html", {"doctor": doctor, "appointments": appointments})


@login_required
@transaction.atomic
def appointment_consultation_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "visit", "doctor", "service", "payment"),
        id=appointment_id,
    )
    medical_record = MedicalRecord.objects.filter(appointment=appointment).first()
    form = MedicalRecordForm(request.POST or None, instance=medical_record)

    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.appointment = appointment
        record.created_by = request.user
        record.save()

        appointment.status = "completed"
        appointment.save(update_fields=["status", "updated_at"])

        outcome_to_visit_status = {
            "consultation_completed": "completed",
            "need_examination": "need_examination",
            "hospitalization_required": "hospitalization_required",
            "repeat_visit": "repeat_visit_required",
            "referral": "referred",
        }
        appointment.visit.status = outcome_to_visit_status[record.outcome]
        appointment.visit.save(update_fields=["status", "updated_at"])

        messages.success(request, "Прием завершен, медицинская запись сохранена.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)

    if appointment.status == "waiting":
        appointment.status = "in_progress"
        appointment.visit.status = "in_progress"
        appointment.save(update_fields=["status", "updated_at"])
        appointment.visit.save(update_fields=["status", "updated_at"])

    return render(
        request,
        "outpatient/consultation_form.html",
        {"appointment": appointment, "form": form, "medical_record": medical_record},
    )
