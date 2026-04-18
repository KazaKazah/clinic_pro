from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from outpatient.models import Appointment, PatientVisit


@login_required
def dashboard_page(request):
    today = timezone.localdate()
    appointments = (
        Appointment.objects.filter(appointment_date=today)
        .select_related("patient", "doctor", "service", "payment")
        .order_by("appointment_time")
    )
    context = {
        "today": today,
        "appointments": appointments,
        "waiting_payment_count": PatientVisit.objects.filter(status="waiting_payment").count(),
        "sent_to_doctor_count": PatientVisit.objects.filter(status="sent_to_doctor").count(),
        "in_progress_count": PatientVisit.objects.filter(status="in_progress").count(),
        "completed_count": PatientVisit.objects.filter(status="completed").count(),
    }
    return render(request, "dashboard.html", context)
