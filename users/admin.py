from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


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
