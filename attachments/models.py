from django.db import models
from patients.models import Patient
from outpatient.models import OutpatientVisit
from inpatient.models import InpatientAdmission

class Attachment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    outpatient_visit = models.ForeignKey(
        OutpatientVisit, on_delete=models.CASCADE, null=True, blank=True
    )
    inpatient_admission = models.ForeignKey(
        InpatientAdmission, on_delete=models.CASCADE, null=True, blank=True
    )

    file = models.FileField(upload_to='attachments/')
    document_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)