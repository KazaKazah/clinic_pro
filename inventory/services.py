from billing.models import ServiceMaterial
from inventory.models import StockMovement


def write_off_materials(service, qty=1, source="outpatient"):
    service_materials = ServiceMaterial.objects.filter(service=service)

    for sm in service_materials:
        material = sm.material
        total_qty = sm.qty * qty

        if material.stock_qty < total_qty:
            raise Exception(f"Недостаточно {material.name} на складе")

        material.stock_qty -= total_qty
        material.save(update_fields=['stock_qty'])

        StockMovement.objects.create(
            item_type='material',
            item_id=material.id,
            item_name=material.name,
            qty=total_qty,
            movement_type='out',
            source=source
        )


def get_material_stock(material):
    from .models import Stock
    stock = Stock.objects.filter(material=material).first()
    return stock.quantity if stock else 0


def restore_materials(service, qty=1, source="outpatient_restore"):
    service_materials = ServiceMaterial.objects.filter(service=service)

    for sm in service_materials:
        material = sm.material
        total_qty = sm.qty * qty

        material.stock_qty += total_qty
        material.save(update_fields=['stock_qty'])

        StockMovement.objects.create(
            item_type='material',
            item_id=material.id,
            item_name=material.name,
            qty=total_qty,
            movement_type='in',
            source=source
        )


def write_off_medication(medication, qty, source="inpatient"):
    if medication.stock_qty < qty:
        raise Exception(f"Недостаточно {medication.name} на складе")

    medication.stock_qty -= qty
    medication.save(update_fields=['stock_qty'])

    StockMovement.objects.create(
        item_type='medication',
        item_id=medication.id,
        item_name=medication.name,
        qty=qty,
        movement_type='out',
        source=source
    )


def restore_medication(medication, qty, source="inpatient_restore"):
    medication.stock_qty += qty
    medication.save(update_fields=['stock_qty'])

    StockMovement.objects.create(
        item_type='medication',
        item_id=medication.id,
        item_name=medication.name,
        qty=qty,
        movement_type='in',
        source=source
    )