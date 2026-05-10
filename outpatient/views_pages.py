from django import forms
from django.forms import inlineformset_factory

from billing.models import MedicalService, Payment
from patients.models import Patient

from .models import (
    Appointment,
    DiagnosticStudyCatalog,
    DiagnosticStudyResult,
    Doctor,
    ICD10Diagnosis,
    MedicalRecord,
    PatientVisit,
    SpecialistReferral,
    Specialty,
)
from .forms import (
    AppointmentReservationForm,
    CreateVisitAppointmentForm,
    DiagnosticStudyResultFormSet,
    MedicalRecordForm,
    PaymentStatusUpdateForm,
    SpecialistReferralForm,
)
from django import forms
from billing.models import MedicalService, Payment
from patients.models import Patient
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from outpatient.models import ICD10Diagnosis
from django.db.models import Q


class CreateVisitAppointmentForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Пациент",
        queryset=Patient.objects.all().order_by("last_name", "first_name", "middle_name"),
        empty_label="Выберите пациента",
    )
    visit_type = forms.ChoiceField(
        label="Тип обращения",
        choices=PatientVisit.VISIT_TYPES,
        initial="consultation",
    )
    reason = forms.CharField(
        label="Причина обращения",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    doctor = forms.ModelChoiceField(
        label="Врач",
        queryset=Doctor.objects.filter(is_active=True).select_related("specialty").order_by("full_name"),
        empty_label="Выберите врача",
    )
    service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.filter(is_active=True).select_related("specialty").order_by("name"),
        empty_label="Выберите услугу",
    )
    appointment_date = forms.DateField(
        label="Дата приема",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    appointment_time = forms.TimeField(
        label="Время приема",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    payment_status = forms.ChoiceField(
        label="Статус оплаты",
        choices=Payment.STATUS_CHOICES,
        initial="not_paid",
    )
    registrar_comment = forms.CharField(
        label="Комментарий регистратора",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()

        doctor = cleaned_data.get("doctor")
        service = cleaned_data.get("service")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if doctor and service and getattr(service, "specialty_id", None) and doctor.specialty_id != service.specialty_id:
            self.add_error("service", "Услуга не относится к специальности выбранного врача.")

        if doctor and appointment_date and appointment_time:
            duplicate_exists = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status="cancelled").exists()

            if duplicate_exists:
                self.add_error("appointment_time", "У врача уже есть запись на это время.")

        return cleaned_data

    def save(self, created_by):
        patient = self.cleaned_data["patient"]
        doctor = self.cleaned_data["doctor"]
        service = self.cleaned_data["service"]

        visit = PatientVisit.objects.create(
            patient=patient,
            visit_type=self.cleaned_data["visit_type"],
            reason=self.cleaned_data["reason"],
            status="sent_to_doctor",
            created_by=created_by,
        )

        appointment = Appointment.objects.create(
            visit=visit,
            patient=patient,
            doctor=doctor,
            service=service,
            appointment_date=self.cleaned_data["appointment_date"],
            appointment_time=self.cleaned_data["appointment_time"],
            status="waiting",
            registrar_comment=self.cleaned_data["registrar_comment"],
        )

        Payment.objects.create(
            appointment=appointment,
            amount=service.price,
            status=self.cleaned_data["payment_status"],
        )

        return appointment



class CreateVisitAppointmentForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Пациент",
        queryset=Patient.objects.all().order_by("last_name", "first_name", "middle_name"),
        empty_label="Выберите пациента",
    )
    visit_type = forms.ChoiceField(
        label="Тип обращения",
        choices=PatientVisit.VISIT_TYPES,
        initial="consultation",
    )
    reason = forms.CharField(
        label="Причина обращения",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    doctor = forms.ModelChoiceField(
        label="Врач",
        queryset=Doctor.objects.filter(is_active=True).select_related("specialty").order_by("full_name"),
        empty_label="Выберите врача",
    )
    service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.filter(is_active=True).select_related("specialty").order_by("name"),
        empty_label="Выберите услугу",
    )
    appointment_date = forms.DateField(
        label="Дата приема",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    appointment_time = forms.TimeField(
        label="Время приема",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    payment_status = forms.ChoiceField(
        label="Статус оплаты",
        choices=Payment.STATUS_CHOICES,
        initial="not_paid",
    )
    registrar_comment = forms.CharField(
        label="Комментарий регистратора",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()

        doctor = cleaned_data.get("doctor")
        service = cleaned_data.get("service")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if doctor and service and getattr(service, "specialty_id", None) and doctor.specialty_id != service.specialty_id:
            self.add_error("service", "Услуга не относится к специальности выбранного врача.")

        if doctor and appointment_date and appointment_time:
            duplicate_exists = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status="cancelled").exists()

            if duplicate_exists:
                self.add_error("appointment_time", "У врача уже есть запись на это время.")

        return cleaned_data

    def save(self, created_by):
        patient = self.cleaned_data["patient"]
        doctor = self.cleaned_data["doctor"]
        service = self.cleaned_data["service"]

        visit = PatientVisit.objects.create(
            patient=patient,
            visit_type=self.cleaned_data["visit_type"],
            reason=self.cleaned_data["reason"],
            status="sent_to_doctor",
            created_by=created_by,
        )

        appointment = Appointment.objects.create(
            visit=visit,
            patient=patient,
            doctor=doctor,
            service=service,
            appointment_date=self.cleaned_data["appointment_date"],
            appointment_time=self.cleaned_data["appointment_time"],
            status="waiting",
            registrar_comment=self.cleaned_data["registrar_comment"],
        )

        Payment.objects.create(
            appointment=appointment,
            amount=service.price,
            status=self.cleaned_data["payment_status"],
        )

        return appointment



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
        Appointment.objects.select_related(
            "patient",
            "visit",
            "doctor",
            "service",
            "payment",
            "created_from_referral",
            "created_from_referral__source_appointment",
            "created_from_referral__source_appointment__doctor",
        ).prefetch_related(
            "study_results",
            "study_results__study",
        ),
        id=appointment_id,
    )

    payment = getattr(appointment, "payment", None)
    payment_status_form = PaymentStatusUpdateForm(
        current_status=payment.status if payment else "not_paid"
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
            return redirect("appointment_detail_page", appointment_id=appointment.id)

        messages.error(request, "Форма не сохранена. Проверьте ошибки ниже.")
        print("record_form.errors =", record_form.errors)
        print("record_form.non_field_errors =", record_form.non_field_errors())
        print("referral_form.errors =", referral_form.errors)
        print("referral_form.non_field_errors =", referral_form.non_field_errors())
        print("study_formset.errors =", study_formset.errors)
        print("study_formset.non_form_errors =", study_formset.non_form_errors())

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
