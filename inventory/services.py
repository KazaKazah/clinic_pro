from django.db import transaction
from .models import Material, Medication, StockMovement


def get_material_stock(material):
    return material.stock_qty


def get_medication_stock(medication):
    return medication.stock_qty


@transaction.atomic
def add_material_stock(material, qty, source="manual", comment=""):
    if qty < 1:
        raise ValueError("Количество должно быть больше 0.")

    material.stock_qty += qty
    material.save(update_fields=["stock_qty"])

    StockMovement.objects.create(
        item_type="material",
        item_id=material.id,
        item_name=material.name,
        movement_type="in",
        qty=qty,
        source=source,
        comment=comment,
    )


@transaction.atomic
def add_medication_stock(medication, qty, source="manual", comment=""):
    if qty < 1:
        raise ValueError("Количество должно быть больше 0.")

    medication.stock_qty += qty
    medication.save(update_fields=["stock_qty"])

    StockMovement.objects.create(
        item_type="medication",
        item_id=medication.id,
        item_name=medication.name,
        movement_type="in",
        qty=qty,
        source=source,
        comment=comment,
    )


@transaction.atomic
def write_off_materials(service, qty=1, source="outpatient", comment=""):
    from billing.models import ServiceMaterial

    service_materials = ServiceMaterial.objects.filter(service=service)

    for sm in service_materials:
        material = sm.material
        total_qty = sm.qty * qty

        if material.stock_qty < total_qty:
            raise ValueError(f"Недостаточно материала: {material.name}")

        material.stock_qty -= total_qty
        material.save(update_fields=["stock_qty"])

        StockMovement.objects.create(
            item_type="material",
            item_id=material.id,
            item_name=material.name,
            movement_type="out",
            qty=total_qty,
            source=source,
            comment=comment,
        )


@transaction.atomic
def restore_materials(service, qty=1, source="outpatient_restore", comment=""):
    from billing.models import ServiceMaterial

    service_materials = ServiceMaterial.objects.filter(service=service)

    for sm in service_materials:
        material = sm.material
        total_qty = sm.qty * qty

        material.stock_qty += total_qty
        material.save(update_fields=["stock_qty"])

        StockMovement.objects.create(
            item_type="material",
            item_id=material.id,
            item_name=material.name,
            movement_type="return",
            qty=total_qty,
            source=source,
            comment=comment,
        )


@transaction.atomic
def write_off_medication(medication, qty, source="inpatient", comment=""):
    if qty < 1:
        raise ValueError("Количество должно быть больше 0.")

    if medication.stock_qty < qty:
        raise ValueError(f"Недостаточно лекарства: {medication.name}")

    medication.stock_qty -= qty
    medication.save(update_fields=["stock_qty"])

    StockMovement.objects.create(
        item_type="medication",
        item_id=medication.id,
        item_name=medication.name,
        movement_type="out",
        qty=qty,
        source=source,
        comment=comment,
    )


@transaction.atomic
def restore_medication(medication, qty, source="inpatient_restore", comment=""):
    if qty < 1:
        raise ValueError("Количество должно быть больше 0.")

    medication.stock_qty += qty
    medication.save(update_fields=["stock_qty"])

    StockMovement.objects.create(
        item_type="medication",
        item_id=medication.id,
        item_name=medication.name,
        movement_type="return",
        qty=qty,
        source=source,
        comment=comment,
    )

@transaction.atomic
def adjust_material_stock(material, new_qty, source="manual_adjustment", comment=""):
    if new_qty < 0:
        raise ValueError("Остаток не может быть отрицательным.")

    old_qty = material.stock_qty
    diff = abs(new_qty - old_qty)

    material.stock_qty = new_qty
    material.save(update_fields=["stock_qty"])

    if diff > 0:
        StockMovement.objects.create(
            item_type="material",
            item_id=material.id,
            item_name=material.name,
            movement_type="adjustment",
            qty=diff,
            source=source,
            comment=comment or f"Корректировка с {old_qty} до {new_qty}",
        )


@transaction.atomic
def adjust_medication_stock(medication, new_qty, source="manual_adjustment", comment=""):
    if new_qty < 0:
        raise ValueError("Остаток не может быть отрицательным.")

    old_qty = medication.stock_qty
    diff = abs(new_qty - old_qty)

    medication.stock_qty = new_qty
    medication.save(update_fields=["stock_qty"])

    if diff > 0:
        StockMovement.objects.create(
            item_type="medication",
            item_id=medication.id,
            item_name=medication.name,
            movement_type="adjustment",
            qty=diff,
            source=source,
            comment=comment or f"Корректировка с {old_qty} до {new_qty}",
        )