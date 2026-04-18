from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


iin_validator = RegexValidator(
    regex=r"^\d{12}$",
    message="ИИН должен состоять из 12 цифр.",
)


class Patient(models.Model):
    GENDER_CHOICES = [
        ("male", "Мужской"),
        ("female", "Женский"),
    ]

    last_name = models.CharField("Фамилия", max_length=100)
    first_name = models.CharField("Имя", max_length=100)
    middle_name = models.CharField("Отчество", max_length=100, blank=True)
    iin = models.CharField("ИИН", max_length=12, unique=True, validators=[iin_validator])
    birth_date = models.DateField("Дата рождения")
    gender = models.CharField("Пол", max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField("Телефон", max_length=20)
    address = models.TextField("Адрес проживания", blank=True)
    document_number = models.CharField("Номер документа", max_length=50, blank=True)
    emergency_contact = models.CharField("Контактное лицо", max_length=200, blank=True)
    note = models.TextField("Примечание", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "middle_name"]
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)


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
        User,
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


class MedicalService(models.Model):
    name = models.CharField("Название услуги", max_length=200)
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, verbose_name="Специальность")
    price = models.DecimalField("Стоимость", max_digits=10, decimal_places=2)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["specialty__name", "name"]
        verbose_name = "Медицинская услуга"
        verbose_name_plural = "Медицинские услуги"

    def __str__(self):
        return f"{self.name} - {self.price} тг"


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

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Пациент")
    visit_type = models.CharField("Тип обращения", max_length=30, choices=VISIT_TYPES)
    reason = models.TextField("Причина обращения")
    status = models.CharField("Статус", max_length=40, choices=STATUS_CHOICES, default="created")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Регистратор")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Обращение пациента"
        verbose_name_plural = "Обращения пациентов"

    def __str__(self):
        return f"{self.patient} - {self.get_visit_type_display()} от {self.created_at:%d.%m.%Y}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Запланирован"),
        ("waiting", "Ожидает приема"),
        ("in_progress", "Идет прием"),
        ("completed", "Завершен"),
        ("cancelled", "Отменен"),
    ]

    visit = models.ForeignKey(PatientVisit, on_delete=models.CASCADE, verbose_name="Обращение")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name="Врач")
    service = models.ForeignKey(MedicalService, on_delete=models.PROTECT, verbose_name="Услуга")
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

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, verbose_name="Прием")
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
