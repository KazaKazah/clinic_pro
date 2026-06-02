from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from billing.models import MedicalService, Payment
from patients.models import Patient

from .forms import CreateVisitAppointmentForm, SpecialistReferralForm
from .models import (
    Appointment,
    DiagnosticStudyCatalog,
    DiagnosticStudyResult,
    Doctor,
    InpatientRecord,
    MedicalRecord,
    PatientVisit,
    Specialty,
)


class OutpatientWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.registrar = User.objects.create_user(
            username="registrar",
            password="pass",
            role="registrar",
        )
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="pass",
            role="doctor",
        )
        self.other_doctor_user = User.objects.create_user(
            username="other-doctor",
            password="pass",
            role="doctor",
        )
        self.specialty = Specialty.objects.create(name="Терапия")
        self.other_specialty = Specialty.objects.create(name="Кардиология")
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            full_name="Иванов Иван",
            specialty=self.specialty,
        )
        self.other_doctor = Doctor.objects.create(
            user=self.other_doctor_user,
            full_name="Петров Петр",
            specialty=self.other_specialty,
        )
        self.service = MedicalService.objects.create(
            name="Консультация терапевта",
            specialty=self.specialty,
            price="5000.00",
        )
        self.other_service = MedicalService.objects.create(
            name="Консультация кардиолога",
            specialty=self.other_specialty,
            price="7000.00",
        )
        self.patient = Patient.objects.create(
            last_name="Сидоров",
            first_name="Азамат",
            iin="123456789012",
            birth_date=date(1990, 1, 1),
            gender="male",
            phone="+77010000000",
        )

    def create_visit(self, *, doctor=None, service=None, status="waiting"):
        doctor = doctor or self.doctor
        service = service or self.service
        visit = PatientVisit.objects.create(
            patient=self.patient,
            visit_type="consultation",
            reason="Плановая консультация",
            status="sent_to_doctor",
            created_by=self.registrar,
        )
        appointment = Appointment.objects.create(
            visit=visit,
            patient=self.patient,
            doctor=doctor,
            service=service,
            appointment_date=date(2026, 6, 1),
            appointment_time=time(10, 0),
            status=status,
        )
        Payment.objects.create(appointment=appointment, amount=service.price, status="not_paid")
        return appointment

    def test_create_visit_form_rejects_busy_slot(self):
        self.create_visit()
        form = CreateVisitAppointmentForm(
            data={
                "patient": self.patient.id,
                "visit_type": "consultation",
                "reason": "Повторная консультация",
                "doctor": self.doctor.id,
                "service": self.service.id,
                "appointment_date": "2026-06-01",
                "appointment_time": "10:00",
                "payment_status": "not_paid",
                "registrar_comment": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("appointment_time", form.errors)

    def test_registrar_can_update_payment_status(self):
        appointment = self.create_visit()
        self.client.force_login(self.registrar)

        response = self.client.post(
            reverse("appointment_payment_status_update_page", args=[appointment.id]),
            {"payment_status": "paid"},
        )

        self.assertRedirects(response, reverse("appointment_detail_page", args=[appointment.id]))
        appointment.payment.refresh_from_db()
        self.assertEqual(appointment.payment.status, "paid")

    def test_doctor_cannot_open_other_doctor_consultation(self):
        appointment = self.create_visit(doctor=self.other_doctor, service=self.other_service)
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse("appointment_consultation_page", args=[appointment.id]))

        self.assertRedirects(response, reverse("dashboard_page"))

    def test_referral_form_requires_complete_referral_data(self):
        form = SpecialistReferralForm(
            data={
                "target_specialty": self.other_specialty.id,
                "target_doctor": "",
                "target_service": "",
                "appointment_date": "",
                "appointment_time": "",
                "reason": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("target_doctor", form.errors)
        self.assertIn("target_service", form.errors)

    def test_inpatient_record_is_created_from_hospitalization_appointment(self):
        appointment = self.create_visit()
        MedicalRecord.objects.create(
            appointment=appointment,
            complaints="Боль и слабость",
            anamnesis_disease="Болеет три дня",
            status_praesens="Состояние средней тяжести",
            treatment_plan="Госпитализация и обследование",
            recommendations="Стационарное лечение",
            outcome="hospitalization_required",
            created_by=self.doctor_user,
        )
        study = DiagnosticStudyCatalog.objects.create(name="ОАК", kind="lab")
        DiagnosticStudyResult.objects.create(
            appointment=appointment,
            study=study,
            result_value="Лейкоцитоз",
            conclusion="Воспалительные изменения",
            performed_by=self.doctor_user,
        )
        self.client.force_login(self.doctor_user)

        response = self.client.get(reverse("inpatient_record_page", args=[appointment.id]))

        self.assertEqual(response.status_code, 200)
        inpatient_record = InpatientRecord.objects.get(source_appointment=appointment)
        self.assertEqual(inpatient_record.patient, self.patient)
        self.assertEqual(inpatient_record.complaints, "Боль и слабость")
        self.assertIn("ОАК", inpatient_record.study_summary)
        self.assertIn("Лейкоцитоз", inpatient_record.study_summary)

    def test_inpatient_records_page_lists_stationary_patients(self):
        appointment = self.create_visit()
        inpatient_record = InpatientRecord.objects.create(
            source_appointment=appointment,
            patient=self.patient,
            admitting_doctor=self.doctor,
            department="Терапевтическое отделение",
            ward="204",
            bed="2",
            status="admitted",
            created_by=self.doctor_user,
        )
        self.client.force_login(self.registrar)

        response = self.client.get(reverse("inpatient_records_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, inpatient_record.patient.full_name)
        self.assertContains(response, "Терапевтическое отделение")
