from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "iin",
        "birth_date",
        "gender",
        "phone",
        "created_at",
    )
    search_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "iin",
        "phone",
        "document_number",
    )
    list_filter = ("gender", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Основные данные", {
            "fields": (
                "last_name",
                "first_name",
                "middle_name",
                "iin",
                "birth_date",
                "gender",
            )
        }),
        ("Контакты", {
            "fields": (
                "phone",
                "address",
                "emergency_contact",
            )
        }),
        ("Документы и примечания", {
            "fields": (
                "document_number",
                "note",
            )
        }),
        ("Служебная информация", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )
