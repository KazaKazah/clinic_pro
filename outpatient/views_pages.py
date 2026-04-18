from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from patients.models import Patient
from .forms import CreateVisitAppointmentForm
from .models import Appointment, Doctor


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
