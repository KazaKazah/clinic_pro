from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from billing.models import Payment
from patients.models import Patient

from .forms import (
    AppointmentReservationForm,
    CreateVisitAppointmentForm,
    DiagnosticStudyResultFormSet,
    InpatientRecordForm,
    MedicalRecordForm,
    PaymentStatusUpdateForm,
    SpecialistReferralForm,
)
from .models import Appointment, Doctor, ICD10Diagnosis, InpatientRecord, MedicalRecord, PatientVisit, SpecialistReferral


RECEPTION_ROLES = {"admin", "manager", "registrar"}
CLINICAL_ROLES = {"admin", "manager", "doctor", "nurse"}


def user_role(user):
    return getattr(user, "role", "")


def user_can_manage_appointments(user):
    return user.is_superuser or user.is_staff or user_role(user) in RECEPTION_ROLES


def user_can_do_clinical_work(user):
    return user.is_superuser or user.is_staff or user_role(user) in CLINICAL_ROLES


def get_user_doctor(user):
    return Doctor.objects.filter(user=user, is_active=True).first()


def user_can_view_appointment(user, appointment):
    if user_can_manage_appointments(user):
        return True
    doctor = get_user_doctor(user)
    return bool(doctor and appointment.doctor_id == doctor.id)


def user_can_consult_appointment(user, appointment):
    if not user_can_do_clinical_work(user):
        return False
    if user.is_superuser or user.is_staff or user_role(user) in {"admin", "manager"}:
        return True
    doctor = get_user_doctor(user)
    return bool(doctor and appointment.doctor_id == doctor.id)


def deny_with_message(request, message="У вас нет доступа к этому действию."):
    messages.error(request, message)
    return redirect("dashboard_page")


def build_study_summary(appointment):
    rows = []
    for result in appointment.study_results.select_related("study").all():
        parts = [result.study.name]
        if result.result_value:
            parts.append(f"результат: {result.result_value}")
        if result.conclusion:
            parts.append(f"заключение: {result.conclusion}")
        rows.append("; ".join(parts))
    return "\n".join(rows)


def inpatient_defaults_from_appointment(appointment, user):
    record = getattr(appointment, "medical_record", None)
    diagnosis = None
    diagnosis_text = ""
    if record:
        diagnosis = record.clinical_icd10 or record.preliminary_icd10
        if diagnosis:
            diagnosis_text = f"{diagnosis.code} - {diagnosis.name}"

    return {
        "patient": appointment.patient,
        "admitting_doctor": appointment.doctor,
        "created_by": user,
        "admission_reason": appointment.visit.reason,
        "complaints": record.complaints if record else "",
        "anamnesis": record.anamnesis_disease if record else "",
        "objective_status": record.status_praesens if record else "",
        "diagnosis": diagnosis,
        "diagnosis_text": diagnosis_text,
        "treatment_plan": record.treatment_plan if record else "",
        "recommendations": record.recommendations if record else "",
        "study_summary": build_study_summary(appointment),
    }



@login_required
@transaction.atomic
def visit_create_page(request, patient_id):
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

    patient = get_object_or_404(Patient, id=patient_id)
    initial = {"patient": patient}
    form = CreateVisitAppointmentForm(request.POST or None, initial=initial)
    form.fields["patient"].queryset = Patient.objects.filter(id=patient.id)
    if request.method == "POST" and form.is_valid():
        appointment = form.save(created_by=request.user)
        messages.success(request, "Обращение, прием и оплата созданы. Карточка отправлена врачу.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)
    return render(request, "outpatient/visit_form.html", {"form": form, "patient": patient})


@login_required
def appointment_detail_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient",
            "visit",
            "doctor",
            "service",
            "payment",
            "medical_record",
            "medical_record__preliminary_icd10",
            "medical_record__clinical_icd10",
            "created_from_referral",
            "created_from_referral__source_appointment",
            "created_from_referral__source_appointment__doctor",
        ).prefetch_related(
            "study_results",
            "study_results__study",
        ),
        id=appointment_id,
    )

    if not user_can_view_appointment(request.user, appointment):
        return deny_with_message(request)

    payment = getattr(appointment, "payment", None)
    payment_status_form = PaymentStatusUpdateForm(
        current_status=payment.status if payment else "not_paid"
    )
    return render(
        request,
        "outpatient/appointment_detail.html",
        {
            "appointment": appointment,
            "payment_status_form": payment_status_form,
            "can_manage_appointments": user_can_manage_appointments(request.user),
            "can_update_payment": user_can_manage_appointments(request.user),
            "can_consult": user_can_consult_appointment(request.user, appointment),
            "can_open_inpatient_record": (
                user_can_consult_appointment(request.user, appointment)
                and hasattr(appointment, "medical_record")
                and appointment.medical_record.outcome == "hospitalization_required"
            ),
        },
    )


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
def patient_history_page(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    appointments = (
        Appointment.objects.filter(patient=patient)
        .select_related("visit", "doctor", "doctor__specialty", "service", "payment", "medical_record")
        .order_by("-appointment_date", "-appointment_time", "-id")
    )

    if not user_can_manage_appointments(request.user):
        doctor = get_user_doctor(request.user)
        if not doctor:
            return deny_with_message(request)
        appointments = appointments.filter(doctor=doctor)

    return render(
        request,
        "outpatient/patient_history.html",
        {
            "patient": patient,
            "appointments": appointments,
        },
    )


@login_required
def unpaid_appointments_page(request):
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

    appointments = (
        Appointment.objects.filter(Q(payment__isnull=True) | Q(payment__status__in=["not_paid", "partial"]))
        .exclude(status="cancelled")
        .select_related("patient", "visit", "doctor", "doctor__specialty", "service", "payment")
        .order_by("appointment_date", "appointment_time", "id")
    )

    return render(
        request,
        "outpatient/unpaid_appointments.html",
        {"appointments": appointments},
    )


@login_required
def inpatient_records_page(request):
    if not (user_can_manage_appointments(request.user) or user_can_do_clinical_work(request.user)):
        return deny_with_message(request)

    status = (request.GET.get("status") or "active").strip()
    records = (
        InpatientRecord.objects.select_related(
            "patient",
            "admitting_doctor",
            "admitting_doctor__specialty",
            "source_appointment",
            "diagnosis",
        )
        .order_by("-admission_date", "-updated_at")
    )

    if status == "active":
        records = records.filter(status__in=["draft", "admitted"])
    elif status in {"draft", "admitted", "discharged", "cancelled"}:
        records = records.filter(status=status)
    else:
        status = "all"

    query = (request.GET.get("q") or "").strip()
    if query:
        records = records.filter(
            Q(patient__last_name__icontains=query)
            | Q(patient__first_name__icontains=query)
            | Q(patient__middle_name__icontains=query)
            | Q(patient__iin__icontains=query)
            | Q(department__icontains=query)
            | Q(ward__icontains=query)
            | Q(diagnosis_text__icontains=query)
            | Q(diagnosis__code__icontains=query)
            | Q(diagnosis__name__icontains=query)
        )

    counts = {
        "active": InpatientRecord.objects.filter(status__in=["draft", "admitted"]).count(),
        "draft": InpatientRecord.objects.filter(status="draft").count(),
        "admitted": InpatientRecord.objects.filter(status="admitted").count(),
        "discharged": InpatientRecord.objects.filter(status="discharged").count(),
        "cancelled": InpatientRecord.objects.filter(status="cancelled").count(),
        "all": InpatientRecord.objects.count(),
    }

    return render(
        request,
        "outpatient/inpatient_records.html",
        {
            "records": records,
            "status": status,
            "query": query,
            "counts": counts,
        },
    )


@login_required
@transaction.atomic
def appointment_consultation_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "visit", "doctor", "service", "payment"),
        id=appointment_id,
    )
    if not user_can_consult_appointment(request.user, appointment):
        return deny_with_message(request, "Врач может вести только свои приемы.")

    medical_record = MedicalRecord.objects.filter(appointment=appointment).first()

    record_form = MedicalRecordForm(request.POST or None, instance=medical_record, prefix="record")
    referral_form = SpecialistReferralForm(request.POST or None, prefix="referral")

    study_formset = DiagnosticStudyResultFormSet(
        request.POST or None,
        instance=appointment,
        prefix="studies",
    )

    if request.method == "POST":
        record_valid = record_form.is_valid()
        referral_valid = referral_form.is_valid()
        study_formset_valid = study_formset.is_valid()

        if record_valid and referral_valid and study_formset_valid:

            record = record_form.save(commit=False)
            record.appointment = appointment
            record.created_by = request.user
            record.save()

            study_instances = study_formset.save(commit=False)

            for obj in study_formset.deleted_objects:
                obj.delete()

            for study_result in study_instances:
                study_result.appointment = appointment
                if study_result.performed_by_id is None:
                    study_result.performed_by = request.user
                if study_result.performed_at is None:
                    study_result.performed_at = timezone.now()
                study_result.save()

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
                target_service = referral_form.cleaned_data["target_service"]
                target_doctor = referral_form.cleaned_data["target_doctor"]
                referral_reason = referral_form.cleaned_data["reason"]

                new_visit = PatientVisit.objects.create(
                    patient=appointment.patient,
                    visit_type="consultation",
                    reason=referral_reason,
                    status="sent_to_doctor",
                    created_by=request.user,
                )
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
            if record.outcome == "hospitalization_required":
                return redirect("inpatient_record_page", appointment_id=appointment.id)
            return redirect("appointment_detail_page", appointment_id=appointment.id)

        messages.error(request, "Форма не сохранена. Проверьте ошибки ниже.")

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
            "study_formset": study_formset,
        },
    )


@login_required
def appointment_print_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient",
            "visit",
            "doctor",
            "doctor__specialty",
            "service",
            "payment",
            "medical_record",
            "medical_record__preliminary_icd10",
            "medical_record__clinical_icd10",
        ).prefetch_related("study_results", "study_results__study"),
        id=appointment_id,
    )

    if not user_can_view_appointment(request.user, appointment):
        return deny_with_message(request)

    return render(request, "outpatient/appointment_print.html", {"appointment": appointment})


@login_required
@transaction.atomic
def inpatient_record_page(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient",
            "visit",
            "doctor",
            "doctor__specialty",
            "service",
            "medical_record",
            "medical_record__preliminary_icd10",
            "medical_record__clinical_icd10",
            "inpatient_record",
        ).prefetch_related("study_results", "study_results__study"),
        id=appointment_id,
    )

    if not user_can_consult_appointment(request.user, appointment):
        return deny_with_message(request)

    medical_record = getattr(appointment, "medical_record", None)
    if not medical_record or medical_record.outcome != "hospitalization_required":
        messages.warning(request, "Стационарная карта открывается для приемов с итогом “Требуется госпитализация”.")
        return redirect("appointment_detail_page", appointment_id=appointment.id)

    inpatient_record, created = InpatientRecord.objects.get_or_create(
        source_appointment=appointment,
        defaults=inpatient_defaults_from_appointment(appointment, request.user),
    )

    form = InpatientRecordForm(request.POST or None, instance=inpatient_record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Стационарная карта сохранена.")
        return redirect("inpatient_record_page", appointment_id=appointment.id)

    if created:
        messages.info(request, "Создан черновик стационарной карты на основе завершенного приема.")

    return render(
        request,
        "outpatient/inpatient_record.html",
        {
            "appointment": appointment,
            "medical_record": medical_record,
            "inpatient_record": inpatient_record,
            "form": form,
        },
    )



@login_required
@transaction.atomic
def reserve_appointment_page(request):
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

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
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

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
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

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


@login_required
def icd10_search_api(request):
    query = (request.GET.get("q") or "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    diagnoses = (
        ICD10Diagnosis.objects.filter(is_active=True)
        .exclude(code__contains="-")
        .filter(
            Q(code__icontains=query) |
            Q(name__icontains=query)
        )
        .order_by("code")[:20]
    )

    results = [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "label": f"{item.code} — {item.name}",
        }
        for item in diagnoses
    ]

    return JsonResponse({"results": results})



@login_required
@transaction.atomic
def appointment_payment_status_update_page(request, appointment_id):
    if not user_can_manage_appointments(request.user):
        return deny_with_message(request)

    appointment = get_object_or_404(
        Appointment.objects.select_related("payment", "service"),
        id=appointment_id,
    )

    payment = getattr(appointment, "payment", None)
    if payment is None:
        payment = Payment.objects.create(
            appointment=appointment,
            amount=appointment.service.price,
            status="not_paid",
        )

    form = PaymentStatusUpdateForm(
        request.POST or None,
        current_status=payment.status,
    )

    if request.method == "POST" and form.is_valid():
        payment.status = form.cleaned_data["payment_status"]
        payment.save(update_fields=["status"])
        messages.success(request, "Статус оплаты обновлен.")
    else:
        if request.method == "POST":
            messages.error(request, "Не удалось обновить статус оплаты.")

    return redirect("appointment_detail_page", appointment_id=appointment.id)
