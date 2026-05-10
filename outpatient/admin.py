from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
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

@admin.action(description="Активировать")
def activate_items(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Деактивировать")
def deactivate_items(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active",)
    actions = (activate_items, deactivate_items)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "specialty",
        "room_number",
        "phone",
        "is_active",
    )
    search_fields = (
        "full_name",
        "phone",
        "user__username",
        "specialty__name",
    )
    list_filter = ("specialty", "is_active")
    autocomplete_fields = ("user", "specialty")
    actions = (activate_items, deactivate_items)


@admin.register(ICD10Diagnosis)
class ICD10DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "external_url")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    actions = (activate_items, deactivate_items)


@admin.register(PatientVisit)
class PatientVisitAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "visit_type",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = (
        "patient__last_name",
        "patient__first_name",
        "patient__middle_name",
        "patient__iin",
        "reason",
    )
    list_filter = ("visit_type", "status", "created_at")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("patient", "created_by")


@admin.action(description="Отметить как выполненные и заблокировать")
def mark_completed_and_lock(modeladmin, request, queryset):
    for appointment in queryset:
        if appointment.status == "cancelled":
            continue
        appointment.status = "completed"
        appointment.is_locked = True
        if appointment.performed_at is None:
            appointment.performed_at = timezone.now()
        if appointment.performed_by_id is None:
            appointment.performed_by = request.user
        appointment.save()


@admin.action(description="Отменить выбранные приемы")
def cancel_appointments(modeladmin, request, queryset):
    for appointment in queryset:
        if appointment.is_locked:
            continue
        appointment.status = "cancelled"
        appointment.save()


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "service",
        "appointment_date",
        "appointment_time",
        "status",
        "performed_by",
        "performed_at",
        "is_locked",
    )
    search_fields = (
        "patient__last_name",
        "patient__first_name",
        "patient__middle_name",
        "patient__iin",
        "doctor__full_name",
        "service__name",
    )
    list_filter = (
        "status",
        "appointment_date",
        "doctor__specialty",
        "doctor",
        "service",
        "is_locked",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "performed_at",
        "is_locked",
    )
    autocomplete_fields = (
        "visit",
        "patient",
        "doctor",
        "service",
        "performed_by",
    )
    actions = (mark_completed_and_lock, cancel_appointments)

    fieldsets = (
        ("Пациент и направление", {
            "fields": (
                "visit",
                "patient",
                "doctor",
                "service",
            )
        }),
        ("Дата и статус", {
            "fields": (
                "appointment_date",
                "appointment_time",
                "status",
                "registrar_comment",
            )
        }),
        ("Выполнение услуги", {
            "fields": (
                "performed_by",
                "performed_at",
                "is_locked",
            )
        }),
        ("Служебная информация", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old = Appointment.objects.filter(pk=obj.pk).first()
            if old and old.is_locked and obj.status == "cancelled":
                raise ValidationError("Завершенный прием нельзя отменить.")

        if obj.status == "completed":
            obj.is_locked = True
            if obj.performed_by_id is None:
                obj.performed_by = request.user
            if obj.performed_at is None:
                obj.performed_at = timezone.now()

        super().save_model(request, obj, form, change)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "preliminary_icd10",
        "clinical_icd10",
        "outcome",
        "created_by",
        "created_at",
    )
    search_fields = (
        "appointment__patient__last_name",
        "appointment__patient__first_name",
        "appointment__patient__iin",
        "preliminary_icd10__code",
        "preliminary_icd10__name",
        "clinical_icd10__code",
        "clinical_icd10__name",
        "diagnosis_reasoning",
        "recommendations",
    )
    list_filter = (
        "outcome",
        "created_at",
        "preliminary_icd10",
        "clinical_icd10",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = (
        "appointment",
        "preliminary_icd10",
        "clinical_icd10",
        "created_by",
    )
    fieldsets = (
        ("Прием", {
            "fields": (
                "appointment",
                "created_by",
            )
        }),
        ("Анамнез и статус", {
            "fields": (
                "complaints",
                "anamnesis_disease",
                "anamnesis_life",
                "status_praesens",
                "gynecological_anamnesis",
            )
        }),
        ("Диагнозы МКБ-10", {
            "fields": (
                "preliminary_icd10",
                "diagnosis_reasoning",
                "clinical_icd10",
            )
        }),
        ("Назначения", {
            "fields": (
                "treatment_plan",
                "recommendations",
                "outcome",
            )
        }),
        ("Служебная информация", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

@admin.register(DiagnosticStudyCatalog)
class DiagnosticStudyCatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "unit", "reference_range", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name",)


@admin.register(DiagnosticStudyResult)
class DiagnosticStudyResultAdmin(admin.ModelAdmin):
    list_display = ("appointment", "study", "result_value", "include_in_reasoning", "performed_at")
    list_filter = ("study__kind", "include_in_reasoning")
    search_fields = ("study__name", "result_value", "conclusion")
