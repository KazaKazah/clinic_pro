from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Администратор"),
        ("manager", "Ответственный сотрудник"),
        ("registrar", "Регистратор"),
        ("doctor", "Врач"),
        ("nurse", "Медсестра"),
    ]

    role = models.CharField("Роль", max_length=30, choices=ROLE_CHOICES, default="registrar")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
