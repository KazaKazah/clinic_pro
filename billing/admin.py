from django.contrib import admin

from .models import MedicalService, Payment


@admin.action(description="Активировать выбранные услуги")
def activate_services(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Деактивировать выбранные услуги")
def deactivate_services(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(MedicalService)
class MedicalServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "specialty",
        "service_type",
        "price",
        "requires_referral",
        "allow_repeat",
        "daily_limit",
        "is_active",
    )
    search_fields = ("name", "specialty__name")
    list_filter = (
        "specialty",
        "service_type",
        "requires_referral",
        "allow_repeat",
        "is_active",
    )
    autocomplete_fields = ("specialty",)
    actions = (activate_services, deactivate_services)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "amount",
        "status",
        "method",
        "paid_at",
        "created_at",
    )
    search_fields = (
        "appointment__patient__last_name",
        "appointment__patient__first_name",
        "appointment__patient__iin",
        "appointment__doctor__full_name",
    )
    list_filter = ("status", "method", "created_at", "paid_at")
    readonly_fields = ("created_at", "paid_at")
    autocomplete_fields = ("appointment",)
