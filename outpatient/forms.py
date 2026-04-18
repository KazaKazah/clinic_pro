from django import forms

from billing.models import MedicalService, Payment
from .models import Appointment, Doctor, PatientVisit


class CreateVisitAppointmentForm(forms.Form):
    visit_type = forms.ChoiceField(label="Тип обращения", choices=PatientVisit.VISIT_TYPES)
    reason = forms.CharField(
        label="Причина обращения",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Кратко опишите жалобу или цель визита"}),
    )
    service = forms.ModelChoiceField(
        label="Услуга",
        queryset=MedicalService.objects.none(),
        empty_label="Выберите услугу",
    )
    doctor = forms.ModelChoiceField(
        label="Врач",
        queryset=Doctor.objects.none(),
        empty_label="Выберите врача",
    )
    appointment_date = forms.DateField(label="Дата приема", widget=forms.DateInput(attrs={"type": "date"}))
    appointment_time = forms.TimeField(label="Время приема", widget=forms.TimeInput(attrs={"type": "time"}))
    payment_status = forms.ChoiceField(label="Статус оплаты", choices=Payment.STATUS_CHOICES)
    payment_method = forms.ChoiceField(
        label="Способ оплаты",
        choices=[("", "Не выбран")] + Payment.METHOD_CHOICES,
        required=False,
    )
    registrar_comment = forms.CharField(
        label="Комментарий регистратора",
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = (
            MedicalService.objects.filter(is_active=True, specialty__is_active=True)
            .select_related("specialty")
            .order_by("specialty__name", "name")
        )
        self.fields["doctor"].queryset = (
            Doctor.objects.filter(is_active=True, specialty__is_active=True)
            .select_related("specialty")
            .order_by("specialty__name", "full_name")
        )
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()
        service = cleaned_data.get("service")
        doctor = cleaned_data.get("doctor")
        payment_status = cleaned_data.get("payment_status")
        payment_method = cleaned_data.get("payment_method")

        if service and doctor and service.specialty_id != doctor.specialty_id:
            self.add_error("doctor", "Выбранный врач не относится к специальности выбранной услуги.")
        if payment_status in {"paid", "partial", "free"} and not payment_method:
            self.add_error("payment_method", "Укажите способ оплаты.")
        return cleaned_data

    def save(self, patient, registrar):
        service = self.cleaned_data["service"]
        payment_status = self.cleaned_data["payment_status"]

        visit_status = "waiting_payment"
        if payment_status in {"paid", "free"}:
            visit_status = "sent_to_doctor"
        elif payment_status == "partial":
            visit_status = "paid"

        visit = PatientVisit.objects.create(
            patient=patient,
            visit_type=self.cleaned_data["visit_type"],
            reason=self.cleaned_data["reason"],
            status=visit_status,
            created_by=registrar,
        )
        appointment = Appointment.objects.create(
            visit=visit,
            patient=patient,
            doctor=self.cleaned_data["doctor"],
            service=service,
            appointment_date=self.cleaned_data["appointment_date"],
            appointment_time=self.cleaned_data["appointment_time"],
            status="waiting" if payment_status in {"paid", "partial", "free"} else "scheduled",
            registrar_comment=self.cleaned_data["registrar_comment"],
        )
        Payment.objects.create(
            appointment=appointment,
            amount=service.price,
            status=payment_status,
            method=self.cleaned_data["payment_method"],
        )
        return appointment


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select"})}
