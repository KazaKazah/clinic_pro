from inventory.services import get_material_stock
from outpatient import serializers

class DailySheetPrescriptionSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="medication.name", read_only=True)
    stock_qty = serializers.SerializerMethodField()

    ...

    def get_stock_qty(self, obj):
        return get_material_stock(obj.medication)
    