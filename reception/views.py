from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CreateVisitAppointmentForm, PatientForm, PatientSearchForm
from .models import Appointment, Doctor, Patient, PatientVisit


@login_required
def dashboard(request):
    today = timezone.localdate()
    appointments = (
        Appointment.objects.filter(appointment_date=today)
        .select_related("patient", "doctor", "service", "payment")
        .order_by("appointment_time")
    )
    context = {
        "today": today,
        "appointments": appointments[:20],
        "waiting_payment_count": PatientVisit.objects.filter(status="waiting_payment").count(),
        "sent_to_doctor_count": PatientVisit.objects.filter(status="sent_to_doctor").count(),
        "in_progress_count": PatientVisit.objects.filter(status="in_progress").count(),
        "completed_count": PatientVisit.objects.filter(status="completed").count(),
    }
    return render(request, "reception/dashboard.html", context)


@login_required
def patient_search(request):
    form = PatientSearchForm(request.GET or None)
    patients = None
    if form.is_valid():
        patients = form.search()
    return render(request, "reception/patient_search.html", {"form": form, "patients": patients})


@login_required
def patient_create(request):
    form = PatientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        patient = form.save()
        messages.success(request, "Пациент добавлен в базу данных.")
        return redirect("reception:create_visit", patient_id=patient.id)
    return render(request, "reception/patient_form.html", {"form": form})


@login_required
@transaction.atomic
def create_visit(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    form = CreateVisitAppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appointment = form.save(patient=patient, registrar=request.user)
        messages.success(request, "Обращение, прием и оплата созданы. Карточка отправлена врачу.")
        return redirect("reception:appointment_detail", appointment_id=appointment.id)
    return render(request, "reception/create_visit.html", {"form": form, "patient": patient})


@login_required
def appointment_detail(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "visit", "doctor", "service", "payment"),
        id=appointment_id,
    )
    return render(request, "reception/appointment_detail.html", {"appointment": appointment})


@login_required
def doctor_queue(request):
    doctor = Doctor.objects.filter(user=request.user, is_active=True).first()
    appointments = Appointment.objects.none()
    if doctor:
        appointments = (
            Appointment.objects.filter(doctor=doctor, status__in=["waiting", "in_progress"])
            .select_related("patient", "visit", "service", "payment")
            .order_by("appointment_date", "appointment_time")
        )
    return render(
        request,
        "reception/doctor_queue.html",
        {"doctor": doctor, "appointments": appointments},
    )
