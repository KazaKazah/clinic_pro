from dataclasses import field

from django import forms
from billing.models import MedicalService, Payment
from .models import Appointment, Doctor, MedicalRecord, PatientVisit, SpecialistReferral, Specialty
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
from django.forms import inlineformset_factory




class DiagnosticStudyResultForm(forms.ModelForm):
    class Meta:
        model = DiagnosticStudyResult
        fields = [
            "study",
            "result_value",
            "conclusion",
            "include_in_reasoning",
        ]
        widgets = {
            "conclusion": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["study"].queryset = DiagnosticStudyCatalog.objects.filter(is_active=True).order_by("kind", "name")

        for field_name, field in self.fields.items():
            if field_name == "include_in_reasoning":
                field.widget.attrs["class"] = "form-check-input"
            else:
                css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
                field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()

        study = cleaned_data.get("study")
        result_value = (cleaned_data.get("result_value") or "").strip()
        conclusion = (cleaned_data.get("conclusion") or "").strip()

        if not study and not result_value and not conclusion:
            self.empty_permitted = True
            return cleaned_data

        if not study and (result_value or conclusion):
            self.add_error("study", "Выберите исследование.")

        return cleaned_data


DiagnosticStudyResultFormSet = inlineformset_factory(
    Appointment,
    DiagnosticStudyResult,
    form=DiagnosticStudyResultForm,
    extra=1,
    can_delete=True,
)




class AppointmentReservationForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Пациент",
        queryset=None,
        empty_label="Выберите пациента",
    )
    visit_type = forms.ChoiceField(
        label="Тип обращения",
        choices=PatientVisit.VISIT_TYPES,
        initial="consultation",
    )
    reason = forms.CharField(
        label="Причина записи",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.none(),
        empty_label="Выберите услугу",
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

    def __init__(self, *args, doctor=None, appointment_date=None, appointment_time=None, **kwargs):
        super().__init__(*args, **kwargs)
        from patients.models import Patient

        self.doctor = doctor
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time

        self.fields["patient"].queryset = Patient.objects.all().order_by(
            "last_name",
            "first_name",
            "middle_name",
        )

        if doctor:
            self.fields["service"].queryset = MedicalService.objects.filter(
                is_active=True,
                specialty=doctor.specialty,
            ).order_by("name")

        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()

        if not self.doctor or not self.appointment_date or not self.appointment_time:
            raise forms.ValidationError("Не удалось определить врача, дату или время приема.")

        duplicate_exists = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
        ).exclude(status="cancelled").exists()

        if duplicate_exists:
            raise forms.ValidationError("Этот слот уже занят. Выберите другое время.")

        service = cleaned_data.get("service")
        if service and service.specialty_id != self.doctor.specialty_id:
            self.add_error("service", "Услуга не относится к специальности выбранного врача.")

        return cleaned_data

    def save(self, registrar):
        patient = self.cleaned_data["patient"]
        service = self.cleaned_data["service"]
        payment_status = self.cleaned_data["payment_status"]

        visit = PatientVisit.objects.create(
            patient=patient,
            visit_type=self.cleaned_data["visit_type"],
            reason=self.cleaned_data["reason"],
            status="reserved",
            created_by=registrar,
        )

        appointment = Appointment.objects.create(
            visit=visit,
            patient=patient,
            doctor=self.doctor,
            service=service,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
            status="reserved",
            registrar_comment=self.cleaned_data["registrar_comment"],
        )

        Payment.objects.create(
            appointment=appointment,
            amount=service.price,
            status=payment_status,
        )

        return appointment



class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            "complaints",
            "anamnesis_disease",
            "anamnesis_life",
            "status_praesens",
            "gynecological_anamnesis",
            "preliminary_icd10",
            "diagnosis_reasoning",
            "clinical_icd10",
            "treatment_plan",
            "recommendations",
            "outcome",
        ]
        widgets = {
            "complaints": forms.Textarea(attrs={"rows": 3}),
            "anamnesis_disease": forms.Textarea(attrs={"rows": 3}),
            "anamnesis_life": forms.Textarea(attrs={"rows": 3}),
            "status_praesens": forms.Textarea(attrs={"rows": 3}),
            "gynecological_anamnesis": forms.Textarea(attrs={"rows": 3}),
            "diagnosis_reasoning": forms.Textarea(attrs={"rows": 3}),
            "treatment_plan": forms.Textarea(attrs={"rows": 3}),
            "recommendations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["preliminary_icd10"].queryset = ICD10Diagnosis.objects.filter(is_active=True).exclude(code__contains="-").order_by("code")
        self.fields["preliminary_icd10"].label = "Предварительный диагноз по МКБ-10"
        self.fields["preliminary_icd10"].widget.attrs["class"] = "d-none icd10-hidden-select"
        self.fields["preliminary_icd10"].empty_label = "Выберите предварительный диагноз"
        self.fields["clinical_icd10"].widget.attrs["class"] = "d-none icd10-hidden-select"

        self.fields["clinical_icd10"].queryset = ICD10Diagnosis.objects.filter(is_active=True).exclude(code__contains="-").order_by("code")
        self.fields["clinical_icd10"].label = "Клинический диагноз по МКБ-10"
        self.fields["clinical_icd10"].empty_label = "Выберите клинический диагноз"

        self.fields["preliminary_icd10"].required = False
        self.fields["clinical_icd10"].required = False

        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = f"{existing_classes} {css_class}".strip()



class SpecialistReferralForm(forms.Form):
    target_specialty = forms.ModelChoiceField(
        label="Специальность",
        queryset=Specialty.objects.none(),
        empty_label="Выберите специальность",
        required=False,
    )
    target_doctor = forms.ModelChoiceField(
        label="Врач",
        queryset=Doctor.objects.none(),
        empty_label="Выберите врача",
        required=False,
    )
    target_service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.none(),
        empty_label="Выберите услугу",
        required=False,
    )
    appointment_date = forms.DateField(
        label="Дата приема",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    appointment_time = forms.TimeField(
        label="Время приема",
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=False,
    )
    reason = forms.CharField(
        label="Причина направления",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["target_specialty"].queryset = Specialty.objects.filter(is_active=True).order_by("name")
        self.fields["target_doctor"].queryset = (
            Doctor.objects.filter(is_active=True, specialty__is_active=True)
            .select_related("specialty")
            .order_by("specialty__name", "full_name")
        )
        self.fields["target_service"].queryset = (
            MedicalService.objects.filter(is_active=True, specialty__is_active=True)
            .select_related("specialty")
            .order_by("specialty__name", "name")
        )

        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class


    def clean(self):
        cleaned_data = super().clean()
        target_specialty = cleaned_data.get("target_specialty")
        target_doctor = cleaned_data.get("target_doctor")
        target_service = cleaned_data.get("target_service")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")
        reason = (cleaned_data.get("reason") or "").strip()

        has_any_referral_data = any([
            target_specialty,
            target_doctor,
            target_service,
            appointment_date,
            appointment_time,
            reason,
        ])

        if not has_any_referral_data:
            return cleaned_data


    @property
    def has_referral(self):
        if not hasattr(self, "cleaned_data"):
            return False
        return any([
            self.cleaned_data.get("target_specialty"),
            self.cleaned_data.get("target_doctor"),
            self.cleaned_data.get("target_service"),
            self.cleaned_data.get("appointment_date"),
            self.cleaned_data.get("appointment_time"),
            self.cleaned_data.get("reason"),
        ])


class AppointmentReservationForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Пациент",
        queryset=None,
        empty_label="Выберите пациента",
    )
    visit_type = forms.ChoiceField(
        label="Тип обращения",
        choices=PatientVisit.VISIT_TYPES,
        initial="consultation",
    )
    reason = forms.CharField(
        label="Причина записи",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.none(),
        empty_label="Выберите услугу",
    )
    registrar_comment = forms.CharField(
        label="Комментарий регистратора",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def __init__(self, *args, doctor=None, appointment_date=None, appointment_time=None, **kwargs):
        super().__init__(*args, **kwargs)
        from patients.models import Patient

        self.doctor = doctor
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time

        self.fields["patient"].queryset = Patient.objects.all().order_by(
            "last_name",
            "first_name",
            "middle_name",
        )

        if doctor:
            self.fields["service"].queryset = MedicalService.objects.filter(
                is_active=True,
                specialty=doctor.specialty,
            ).order_by("name")

        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()

        if not self.doctor or not self.appointment_date or not self.appointment_time:
            raise forms.ValidationError("Не удалось определить врача, дату или время приема.")

        duplicate_exists = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
        ).exclude(status="cancelled").exists()

        if duplicate_exists:
            raise forms.ValidationError("Этот слот уже занят. Выберите другое время.")

        service = cleaned_data.get("service")
        if service and service.specialty_id != self.doctor.specialty_id:
            self.add_error("service", "Услуга не относится к специальности выбранного врача.")

        return cleaned_data

    def save(self, registrar):
        patient = self.cleaned_data["patient"]
        service = self.cleaned_data["service"]

        visit = PatientVisit.objects.create(
            patient=patient,
            visit_type=self.cleaned_data["visit_type"],
            reason=self.cleaned_data["reason"],
            status="reserved",
            created_by=registrar,
        )

        appointment = Appointment.objects.create(
            visit=visit,
            patient=patient,
            doctor=self.doctor,
            service=service,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
            status="reserved",
            registrar_comment=self.cleaned_data["registrar_comment"],
        )

        Payment.objects.create(
            appointment=appointment,
            amount=service.price,
            status="not_paid",
        )

        return appointment


class PaymentStatusUpdateForm(forms.Form):
    payment_status = forms.ChoiceField(
        label="Статус оплаты",
        choices=Payment.STATUS_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop("current_status", None)
        super().__init__(*args, **kwargs)

        if current_status:
            self.fields["payment_status"].initial = current_status

        self.fields["payment_status"].widget.attrs["class"] = "form-select"


