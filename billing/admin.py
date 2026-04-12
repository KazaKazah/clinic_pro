from django.contrib import admin
from .models import ServiceMaterial,Service

admin.site.register(Service)
admin.site.register(ServiceMaterial)