from rest_framework import serializers
from .models import Material, Medication, StockMovement


class MaterialSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = "__all__"

    def get_is_low_stock(self, obj):
        return obj.stock_qty <= obj.min_stock


class MedicationSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Medication
        fields = "__all__"

    def get_is_low_stock(self, obj):
        return obj.stock_qty <= obj.min_stock


class StockMovementSerializer(serializers.ModelSerializer):
    movement_type_display = serializers.CharField(source="get_movement_type_display", read_only=True)
    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)

    class Meta:
        model = StockMovement
        fields = "__all__"