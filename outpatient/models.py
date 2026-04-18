from django.conf import settings
from django.db import models
from django.utils import timezone


class Specialty(models.Model):
    name = models.CharField("Название специальности", max_length=150, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь",
    )
    full_name = models.CharField("ФИО врача", max_length=200)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, verbose_name="Специальность")
    room_number = models.CharField("Кабинет", max_length=20, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    def __str__(self):
        return f"{self.full_name} ({self.specialty})"


class PatientVisit(models.Model):
    VISIT_TYPES = [
        ("primary", "Первичное обращение"),
        ("repeat", "Повторное обращение"),
        ("consultation", "Консультация"),
        ("examination", "Обследование"),
        ("hospitalization", "Госпитализация"),
        ("emergency", "Экстренное обращение"),
    ]

    STATUS_CHOICES = [
        ("created", "Создано"),
        ("waiting_payment", "Ожидает оплаты"),
        ("paid", "Оплачено"),
        ("sent_to_doctor", "Направлен к врачу"),
        ("in_progress", "На приеме"),
        ("need_examination", "Требуется обследование"),
        ("hospitalization_required", "Требуется госпитализация"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
    ]

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, verbose_name="Пациент")
    visit_type = models.CharField("Тип обращения", max_length=30, choices=VISIT_TYPES)
    reason = models.TextField("Причина обращения")
    status = models.CharField("Статус", max_length=40, choices=STATUS_CHOICES, default="created")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Регистратор")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обращение пациента"
        verbose_name_plural = "Обращения пациентов"

    def __str__(self):
        return f"{self.patient} - {self.get_visit_type_display()}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Запланирован"),
        ("waiting", "Ожидает приема"),
        ("in_progress", "Идет прием"),
        ("completed", "Завершен"),
        ("cancelled", "Отменен"),
    ]

    visit = models.ForeignKey(PatientVisit, on_delete=models.CASCADE, verbose_name="Обращение")
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name="Врач")
    service = models.ForeignKey("billing.MedicalService", on_delete=models.PROTECT, verbose_name="Услуга")
    appointment_date = models.DateField("Дата приема", default=timezone.localdate)
    appointment_time = models.TimeField("Время приема")
    status = models.CharField("Статус", max_length=30, choices=STATUS_CHOICES, default="waiting")
    registrar_comment = models.TextField("Комментарий регистратора", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ["appointment_date", "appointment_time"]
        verbose_name = "Прием"
        verbose_name_plural = "Приемы"

    def __str__(self):
        return f"{self.patient} -> {self.doctor} ({self.appointment_date} {self.appointment_time})"
