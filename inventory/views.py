from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Material, Medication, StockMovement
from .serializers import (
    MaterialSerializer,
    MedicationSerializer,
    StockMovementSerializer,
)
from .services import add_material_stock, add_medication_stock
from .services import (
    add_material_stock,
    add_medication_stock,
    adjust_material_stock,
    adjust_medication_stock,
)

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all().order_by("name")
    serializer_class = MaterialSerializer

    @action(detail=True, methods=["post"])
    def adjust_stock(self, request, pk=None):
        obj = self.get_object()
        new_qty = int(request.data.get("new_qty", -1))
        comment = request.data.get("comment", "")

        try:
            adjust_material_stock(
                material=obj,
                new_qty=new_qty,
                source="api:adjust_stock",
                comment=comment,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        obj.refresh_from_db()
        return Response(self.get_serializer(obj).data)


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all().order_by("name")
    serializer_class = MedicationSerializer

    @action(detail=True, methods=["post"])
    def adjust_stock(self, request, pk=None):
        obj = self.get_object()
        new_qty = int(request.data.get("new_qty", -1))
        comment = request.data.get("comment", "")

        try:
            adjust_medication_stock(
                medication=obj,
                new_qty=new_qty,
                source="api:adjust_stock",
                comment=comment,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        obj.refresh_from_db()
        return Response(self.get_serializer(obj).data)
    

class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all().order_by("-created_at")
    serializer_class = StockMovementSerializer


