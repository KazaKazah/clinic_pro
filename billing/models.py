from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

from django.db import models
from inventory.models import Material
from billing.models import Service

class ServiceMaterial(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    qty = models.IntegerField()