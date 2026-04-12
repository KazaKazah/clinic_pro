from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('registrar', 'Регистратор'),
        ('doctor', 'Врач'),
        ('nurse', 'Медсестра'),
        ('pharmacy', 'Склад'),
        ('accountant', 'Бухгалтер'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name