from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "iin", "birth_date", "phone", "created_at")
    search_fields = ("last_name", "first_name", "middle_name", "iin", "phone")
    list_filter = ("gender", "created_at")
