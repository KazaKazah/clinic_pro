from django.contrib import admin

from .models import MedicalService, Payment


@admin.register(MedicalService)
class MedicalServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "price", "is_active")
    search_fields = ("name",)
    list_filter = ("specialty", "is_active")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("appointment", "amount", "status", "method", "paid_at")
    list_filter = ("status", "method", "created_at")
