from django.db import models


class Material(models.Model):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Medication(models.Model):
    name = models.CharField(max_length=255)
    form = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)

    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    MOVEMENT_TYPE = (
        ('in', 'Приход'),
        ('out', 'Расход'),
    )

    ITEM_TYPE = (
        ('material', 'Материал'),
        ('medication', 'Лекарство'),
    )

    item_type = models.CharField(max_length=20, choices=ITEM_TYPE, null=True, blank=True)
    item_id = models.PositiveIntegerField(null=True, blank=True)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    qty = models.IntegerField()
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPE)
    source = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item_type} {self.item_name} - {self.qty}"