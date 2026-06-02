from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.html import format_html

from outpatient.models import Doctor

from .models import User


class DoctorProfileInline(admin.StackedInline):
    model = Doctor
    fk_name = "user"
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = "Профиль врача"
    verbose_name_plural = "Профиль врача"
    fields = (
        "full_name",
        "specialty",
        "room_number",
        "phone",
        "is_active",
    )
    autocomplete_fields = ("specialty",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Клиника", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Клиника", {"fields": ("role",)}),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "doctor_profile_link",
        "is_staff",
        "is_active",
    )
    list_filter = UserAdmin.list_filter + ("role",)
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )
    inlines = (DoctorProfileInline,)

    @admin.display(description="Профиль врача")
    def doctor_profile_link(self, obj):
        try:
            doctor = obj.doctor
        except Doctor.DoesNotExist:
            return "Нет"
        url = reverse("admin:outpatient_doctor_change", args=[doctor.id])
        return format_html('<a href="{}">{}</a>', url, doctor.full_name)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if Doctor.objects.filter(user=form.instance).exists() and form.instance.role != "doctor":
            form.instance.role = "doctor"
            form.instance.save(update_fields=["role"])
