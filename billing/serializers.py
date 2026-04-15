from rest_framework import serializers
from .models import Service, ServiceMaterial


class ServiceSerializer(serializers.ModelSerializer):
    materials_info = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = "__all__"

    def get_materials_info(self, obj):
        items = ServiceMaterial.objects.filter(service=obj).select_related("material")

        return [
            {
                "material_id": x.material.id,
                "material_name": x.material.name,
                "required_qty": x.qty,
                "stock_qty": x.material.stock_qty,
                "min_stock": x.material.min_stock,
                "is_low_stock": x.material.stock_qty <= x.material.min_stock,
            }
            for x in items
        ]