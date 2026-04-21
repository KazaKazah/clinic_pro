from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from billing.models import Payment
from patients.models import Patient
from .forms import CreateVisitAppointmentForm, MedicalRecordForm, SpecialistReferralForm
from .models import Appointment, Doctor, MedicalRecord, PatientVisit, SpecialistReferral
from .forms import (
    AppointmentReservationForm,
    CreateVisitAppointmentForm,
    MedicalRecordForm,
    SpecialistReferralForm,
)
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render


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
            .select_related(
                "patient",
                "visit",
                "doctor",
                "service",
                "payment",
                "created_from_referral",
                "created_from_referral__source_appointment",
                "created_from_referral__source_appointment__doctor",
            )
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

    record_form = MedicalRecordForm(request.POST or None, instance=medical_record, prefix="record")
    referral_form = SpecialistReferralForm(request.POST or None, prefix="referral")

    if request.method == "POST":
        if record_form.is_valid() and referral_form.is_valid():
            record = record_form.save(commit=False)
            record.appointment = appointment
            record.created_by = request.user
            record.save()

            appointment.status = "completed"
            appointment.is_locked = True
            appointment.performed_by = request.user
            appointment.performed_at = timezone.now()
            appointment.save(update_fields=["status", "is_locked", "performed_by", "performed_at", "updated_at"])

            outcome_to_visit_status = {
                "consultation_completed": "completed",
                "need_examination": "need_examination",
                "hospitalization_required": "hospitalization_required",
                "repeat_visit": "repeat_visit_required",
                "referral": "referred",
            }
            appointment.visit.status = outcome_to_visit_status[record.outcome]
            appointment.visit.save(update_fields=["status", "updated_at"])

            if record.outcome == "referral" and referral_form.has_referral:
                new_visit = PatientVisit.objects.create(
                    patient=appointment.patient,
                    visit_type="consultation",
                    reason=referral_form.cleaned_data["reason"],
                    status="sent_to_doctor",
                    created_by=request.user,
                )
                target_service = referral_form.cleaned_data["target_service"]
                target_doctor = referral_form.cleaned_data["target_doctor"]
                referral_reason = referral_form.cleaned_data["reason"]

                new_appointment = Appointment.objects.create(
                    visit=new_visit,
                    patient=appointment.patient,
                    doctor=target_doctor,
                    service=target_service,
                    appointment_date=referral_form.cleaned_data["appointment_date"],
                    appointment_time=referral_form.cleaned_data["appointment_time"],
                    status="waiting",
                    registrar_comment=(
                        f"Направление от врача: {appointment.doctor.full_name}. "
                        f"Исходный прием #{appointment.id}. "
                        f"Причина: {referral_reason}"
                    ),
                )

                Payment.objects.create(
                    appointment=new_appointment,
                    amount=target_service.price,
                    status="not_paid",
                )

                SpecialistReferral.objects.create(
                    source_appointment=appointment,
                    patient=appointment.patient,
                    target_specialty=referral_form.cleaned_data["target_specialty"],
                    target_doctor=target_doctor,
                    target_service=target_service,
                    reason=referral_reason,
                    appointment=new_appointment,
                    status="appointment_created",
                    created_by=request.user,
                )


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
        {
            "appointment": appointment,
            "form": record_form,
            "referral_form": referral_form,
            "medical_record": medical_record,
        },
    )

@login_required
@transaction.atomic
def reserve_appointment_page(request):
    doctor_id = request.GET.get("doctor")
    raw_date = request.GET.get("date")
    raw_time = request.GET.get("time")

    doctor = get_object_or_404(Doctor, id=doctor_id, is_active=True)

    try:
        appointment_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        appointment_time = datetime.strptime(raw_time, "%H:%M").time()
    except (TypeError, ValueError):
        messages.error(request, "Некорректные дата или время для бронирования.")
        return redirect("dashboard_page")

    form = AppointmentReservationForm(
        request.POST or None,
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
    )

    if request.method == "POST" and form.is_valid():
        try:
            appointment = form.save(registrar=request.user)
        except IntegrityError:
            messages.error(request, "Этот слот уже занят другим приемом.")
            return redirect("dashboard_page")

        messages.success(request, "Бронь приема создана.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)

    return render(
        request,
        "outpatient/reserve_appointment.html",
        {
            "form": form,
            "doctor": doctor,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
        },
    )


@login_required
@transaction.atomic
def activate_reservation_page(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.status != "reserved":
        messages.warning(request, "Активировать можно только забронированный прием.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)

    appointment.status = "waiting"
    appointment.visit.status = "sent_to_doctor"
    appointment.save(update_fields=["status", "updated_at"])
    appointment.visit.save(update_fields=["status", "updated_at"])

    messages.success(request, "Пациент отмечен как прибывший. Прием отправлен врачу.")
    return redirect("appointment_detail_page", appointment_id=appointment.id)


@login_required
@transaction.atomic
def cancel_reservation_page(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.is_locked or appointment.status in {"completed", "in_progress"}:
        messages.error(request, "Этот прием нельзя отменить.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)

    appointment.status = "cancelled"
    appointment.visit.status = "cancelled"
    appointment.save(update_fields=["status", "updated_at"])
    appointment.visit.save(update_fields=["status", "updated_at"])

    messages.success(request, "Бронь/прием отменены.")
    return redirect("dashboard_page")
