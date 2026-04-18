from django.core.validators import RegexValidator
from django.db import models


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
