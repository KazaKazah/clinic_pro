from decimal import Decimal
from django.db import models
from django.utils import timezone
from patients.models import Patient
from users.models import User
from inventory.models import Medication
from billing.models import Service


class Ward(models.Model):
    name = models.CharField(max_length=100)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.daily_price})"


class InpatientAdmission(models.Model):
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('discharged', 'Выписан'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(blank=True, null=True)

    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.TextField(blank=True)

    bed_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medication_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    procedure_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.patient} - {self.admission_date}"


class Prescription(models.Model):
    ROUTE_CHOICES = (
        ('iv', 'В/в'),
        ('im', 'В/м'),
        ('oral', 'Перорально'),
    )

    admission = models.ForeignKey(InpatientAdmission, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)

    dosage = models.CharField(max_length=100)
    frequency = models.IntegerField()
    duration = models.IntegerField()

    route = models.CharField(max_length=10, choices=ROUTE_CHOICES)
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admission_id} - {self.medication.name}"


class PrescriptionExecution(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    )

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='executions'
    )

    execution_time = models.DateTimeField(default=timezone.now)
    qty = models.IntegerField(default=1)
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_written_off = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prescription.medication.name} - {self.qty}"


class InpatientProcedure(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    admission = models.ForeignKey(
        InpatientAdmission,
        on_delete=models.CASCADE,
        related_name='procedures'
    )
    service = models.ForeignKey(
        'billing.Service',
        on_delete=models.CASCADE
    )

    procedure_date = models.DateTimeField()
    qty = models.PositiveIntegerField(default=1)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    is_written_off = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.service and self.qty:
            self.price = self.service.price
            self.total = self.qty * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} ({self.procedure_date})"