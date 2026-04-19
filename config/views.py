from collections import defaultdict
from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render
from django.utils import timezone

from outpatient.models import Appointment, Doctor


WORKDAY_START_HOUR = 9
WORKDAY_END_HOUR = 18

WEEKDAY_LABELS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]


def get_week_start(request):
    raw_week = request.GET.get("week")
    today = timezone.localdate()

    if raw_week:
        try:
            selected_date = datetime.strptime(raw_week, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    return selected_date - timedelta(days=selected_date.weekday())


def user_can_view_all_doctors(user):
    role = getattr(user, "role", "")
    return user.is_superuser or user.is_staff or role in {"admin", "manager", "registrar"}


def get_selected_doctor(request, doctors, can_view_all):
    if not doctors:
        return None

    if can_view_all:
        doctor_id = request.GET.get("doctor")
        if doctor_id:
            selected_doctor = doctors.filter(id=doctor_id).first()
            if selected_doctor:
                return selected_doctor
        return doctors.first()

    return doctors.filter(user=request.user).first()


def build_week_calendar(selected_doctor, week_start):
    week_days = []
    for index in range(7):
        current_date = week_start + timedelta(days=index)
        week_days.append({
            "date": current_date,
            "label": WEEKDAY_LABELS[index],
            "is_today": current_date == timezone.localdate(),
        })

    if not selected_doctor:
        return week_days, []

    week_end = week_start + timedelta(days=6)

    appointments = (
        Appointment.objects.filter(
            doctor=selected_doctor,
            appointment_date__range=(week_start, week_end),
        )
        .select_related(
            "patient",
            "visit",
            "doctor",
            "doctor__specialty",
            "service",
            "payment",
            "created_from_referral",
            "created_from_referral__source_appointment",
            "created_from_referral__source_appointment__doctor",
        )
        .order_by("appointment_date", "appointment_time", "id")
    )

    appointments_by_slot = defaultdict(list)
    for appointment in appointments:
        slot_time = appointment.appointment_time.replace(minute=0, second=0, microsecond=0)
        appointments_by_slot[(appointment.appointment_date, slot_time)].append(appointment)

    schedule_rows = []
    for hour in range(WORKDAY_START_HOUR, WORKDAY_END_HOUR + 1):
        slot_time = time(hour=hour, minute=0)
        schedule_rows.append({
            "time": slot_time,
            "days": [
                {
                    "date": day["date"],
                    "appointments": appointments_by_slot.get((day["date"], slot_time), []),
                }
                for day in week_days
            ],
        })

    return week_days, schedule_rows


@login_required
def dashboard_page(request):
    today = timezone.localdate()
    week_start = get_week_start(request)
    previous_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    can_view_all = user_can_view_all_doctors(request.user)

    all_doctors = Doctor.objects.filter(is_active=True).select_related("specialty").order_by(
        "specialty__name",
        "full_name",
    )

    if can_view_all:
        available_doctors = all_doctors
    else:
        available_doctors = all_doctors.filter(user=request.user)

    selected_doctor = get_selected_doctor(request, available_doctors, can_view_all)
    week_days, schedule_rows = build_week_calendar(selected_doctor, week_start)

    today_appointments = (
        Appointment.objects.filter(appointment_date=today)
        .select_related(
            "patient",
            "visit",
            "doctor",
            "doctor__specialty",
            "service",
            "payment",
            "created_from_referral",
            "created_from_referral__source_appointment",
            "created_from_referral__source_appointment__doctor",
        )
        .order_by("appointment_time", "id")
    )

    if not can_view_all and selected_doctor:
        today_appointments = today_appointments.filter(doctor=selected_doctor)

    waiting_payment_count = today_appointments.filter(
        Q(payment__isnull=True) | Q(payment__status="not_paid")
    ).count()
    waiting_doctor_count = today_appointments.filter(status="waiting").count()
    in_progress_count = today_appointments.filter(status="in_progress").count()
    completed_count = today_appointments.filter(status="completed").count()
    referred_count = today_appointments.filter(created_from_referral__isnull=False).count()

    expected_amount = today_appointments.aggregate(total=Sum("service__price"))["total"] or 0
    paid_amount = today_appointments.filter(payment__status="paid").aggregate(total=Sum("payment__amount"))["total"] or 0

    context = {
        "today": today,
        "appointments": today_appointments,
        "available_doctors": available_doctors,
        "selected_doctor": selected_doctor,
        "can_view_all": can_view_all,
        "week_start": week_start,
        "previous_week": previous_week,
        "next_week": next_week,
        "week_days": week_days,
        "schedule_rows": schedule_rows,
        "waiting_payment_count": waiting_payment_count,
        "waiting_doctor_count": waiting_doctor_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
        "referred_count": referred_count,
        "expected_amount": expected_amount,
        "paid_amount": paid_amount,
    }
    return render(request, "dashboard.html", context)
