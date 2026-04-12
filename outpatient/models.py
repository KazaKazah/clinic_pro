from django.db import models
from patients.models import Patient
from users.models import User
from billing.models import Service

class OutpatientVisit(models.Model):
    STATUS_CHOICES = (
        ('new', 'Создан'),
        ('in_progress', 'В процессе'),
        ('done', 'Завершён'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    visit_datetime = models.DateTimeField()

    complaints = models.TextField(blank=True)
    anamnesis = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)

    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f"{self.patient} - {self.visit_datetime}"
    



class OutpatientService(models.Model):
    visit = models.ForeignKey(OutpatientVisit, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)