from django.contrib import admin

from .models import Appointment, Doctor, PatientVisit, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialty", "room_number", "is_active")
    search_fields = ("full_name", "phone")
    list_filter = ("specialty", "is_active")


@admin.register(PatientVisit)
class PatientVisitAdmin(admin.ModelAdmin):
    list_display = ("patient", "visit_type", "status", "created_by", "created_at")
    search_fields = ("patient__last_name", "patient__first_name", "patient__iin", "reason")
    list_filter = ("visit_type", "status", "created_at")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "service", "appointment_date", "appointment_time", "status")
    search_fields = ("patient__last_name", "patient__first_name", "patient__iin", "doctor__full_name")
    list_filter = ("status", "appointment_date", "doctor__specialty")
