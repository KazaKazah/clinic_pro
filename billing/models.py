from django.db import models
from django.utils import timezone


class MedicalService(models.Model):
    name = models.CharField("Название услуги", max_length=200)
    specialty = models.ForeignKey(
        "outpatient.Specialty",
        on_delete=models.PROTECT,
        verbose_name="Специальность",
    )
    price = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)
    SERVICE_TYPES = [
    ("primary_consultation", "Первичная консультация"),
    ("repeat_consultation", "Повторная консультация"),
    ("ultrasound", "УЗИ"),
    ("procedure", "Процедура"),
    ("laboratory", "Лабораторное исследование"),
    ("other", "Другое"),
    ]

    service_type = models.CharField(
        "Тип услуги",
        max_length=40,
        choices=SERVICE_TYPES,
        default="primary_consultation",
    )
    requires_referral = models.BooleanField("Требует направление", default=False)
    allow_repeat = models.BooleanField("Можно назначать повторно", default=True)
    daily_limit = models.PositiveIntegerField(
        "Ограничение услуги в день",
        null=True,
        blank=True,
        help_text="Оставьте пустым, если ограничения нет.",
    )



    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["specialty__name", "name"]
        verbose_name = "Медицинская услуга"
        verbose_name_plural = "Медицинские услуги"

    def __str__(self):
        return f"{self.name} - {self.price} тг"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("not_paid", "Не оплачено"),
        ("paid", "Оплачено"),
        ("partial", "Частично оплачено"),
        ("free", "Бесплатно"),
    ]

    METHOD_CHOICES = [
        ("cash", "Наличные"),
        ("card", "Банковская карта"),
        ("transfer", "Перевод"),
        ("insurance", "Страховая"),
        ("free", "Бесплатно"),
    ]

    appointment = models.OneToOneField(
        "outpatient.Appointment",
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name="Прием",
    )
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    status = models.CharField("Статус оплаты", max_length=20, choices=STATUS_CHOICES, default="not_paid")
    method = models.CharField("Способ оплаты", max_length=20, choices=METHOD_CHOICES, blank=True)
    paid_at = models.DateTimeField("Дата оплаты", null=True, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"

    def __str__(self):
        return f"{self.appointment} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.status in {"paid", "free"} and self.paid_at is None:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)
