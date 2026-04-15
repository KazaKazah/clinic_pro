from django.db import models


class Material(models.Model):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_qty = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Medication(models.Model):
    name = models.CharField(max_length=255)
    form = models.CharField(max_length=100, blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_qty = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ("in", "Приход"),
        ("out", "Расход"),
        ("return", "Возврат"),
        ("adjustment", "Корректировка"),
    )

    ITEM_TYPES = (
        ("material", "Материал"),
        ("medication", "Лекарство"),
    )

    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_id = models.PositiveIntegerField()
    item_name = models.CharField(max_length=255)

    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    qty = models.PositiveIntegerField()

    source = models.CharField(max_length=255, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_name} | {self.movement_type} | {self.qty}"