from django.contrib import admin
from .models import Material, Medication, StockMovement

admin.site.register(Material)
admin.site.register(Medication)
admin.site.register(StockMovement)