from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError



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
        ("repeat_visit_required", "Требуется повторный прием"),
        ("referred", "Направлен к другому специалисту"),
        ("completed", "Завершено"),
        ("cancelled", "Отменено"),
        ("reserved", "Забронировано"),
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
        ("reserved", "Забронирован"),
    ]

    visit = models.ForeignKey(PatientVisit, on_delete=models.CASCADE, verbose_name="Обращение")
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, verbose_name="Врач")
    service = models.ForeignKey("billing.MedicalService", on_delete=models.PROTECT, verbose_name="Услуга")
    appointment_date = models.DateField("Дата приема", default=timezone.localdate)
    appointment_time = models.TimeField("Время приема")
    status = models.CharField("Статус", max_length=30, choices=STATUS_CHOICES, default="waiting")
    registrar_comment = models.TextField("Комментарий регистратора", blank=True)
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="performed_appointments",
        verbose_name="Услугу выполнил",
    )
    performed_at = models.DateTimeField("Дата и время выполнения услуги", null=True, blank=True)
    is_locked = models.BooleanField("Запрещена отмена/изменение", default=False)

    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ["appointment_date", "appointment_time"]
        verbose_name = "Прием"
        verbose_name_plural = "Приемы"
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "appointment_date", "appointment_time"],
                condition=~models.Q(status="cancelled"),
                name="unique_active_doctor_appointment_slot",
            )
        ]

    def __str__(self):
        return f"{self.patient} -> {self.doctor} ({self.appointment_date} {self.appointment_time})"
    
    def clean(self):
        super().clean()

        if self.pk:
            old = Appointment.objects.filter(pk=self.pk).first()
            if old and old.is_locked and self.status == "cancelled":
                raise ValidationError("Завершенный прием нельзя отменить.")

        duplicate_exists = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
        ).exclude(status="cancelled")

        if self.pk:
            duplicate_exists = duplicate_exists.exclude(pk=self.pk)

        if duplicate_exists.exists():
            raise ValidationError("У этого врача уже есть прием на выбранные дату и время.")

        @property
        def can_cancel(self):
            return not self.is_locked and self.status not in {"completed", "cancelled"}
    

class ICD10Diagnosis(models.Model):
    code = models.CharField("Код МКБ-10", max_length=20, unique=True)
    name = models.CharField("Наименование", max_length=500)
    is_active = models.BooleanField("Активен", default=True)
    external_url = models.URLField("Ссылка на источник", blank=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Диагноз МКБ-10"
        verbose_name_plural = "Диагнозы МКБ-10"

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_group(self):
        return "-" in self.code



class MedicalRecord(models.Model):
    OUTCOME_CHOICES = [
        ("consultation_completed", "Консультация завершена"),
        ("need_examination", "Назначено обследование"),
        ("hospitalization_required", "Требуется госпитализация"),
        ("repeat_visit", "Назначен повторный прием"),
        ("referral", "Направлен к другому специалисту"),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="medical_record",
        verbose_name="Прием",
    )

    complaints = models.TextField("Жалобы пациента")
    anamnesis_disease = models.TextField("Анамнез болезни", blank=True)
    anamnesis_life = models.TextField("Анамнез жизни", blank=True)
    status_praesens = models.TextField("Общее состояние / Status praesens", blank=True)
    gynecological_anamnesis = models.TextField("Гинекологический анамнез", blank=True)

    preliminary_diagnosis = models.TextField("Предварительный диагноз", blank=True)
    preliminary_icd10 = models.ForeignKey(
        ICD10Diagnosis,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="preliminary_records",
        verbose_name="МКБ-10 предварительного диагноза",
    )

    diagnosis_reasoning = models.TextField("Обоснование диагноза", blank=True)

    clinical_diagnosis = models.TextField("Клинический диагноз", blank=True)
    clinical_icd10 = models.ForeignKey(
        ICD10Diagnosis,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clinical_records",
        verbose_name="МКБ-10 клинического диагноза",
    )

    treatment_plan = models.TextField("План лечения", blank=True)
    recommendations = models.TextField("Рекомендации", blank=True)
    outcome = models.CharField("Итог приема", max_length=40, choices=OUTCOME_CHOICES)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Врач")
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Медицинская запись"
        verbose_name_plural = "Медицинские записи"

    def __str__(self):
        return f"Медицинская запись: {self.appointment}"
    

class SpecialistReferral(models.Model):
    STATUS_CHOICES = [
        ("created", "Создано"),
        ("appointment_created", "Прием создан"),
        ("cancelled", "Отменено"),
    ]

    source_appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="specialist_referrals",
        verbose_name="Исходный прием",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        verbose_name="Пациент",
    )
    target_specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        verbose_name="Специальность",
    )
    target_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        verbose_name="Врач",
    )
    target_service = models.ForeignKey(
        "billing.MedicalService",
        on_delete=models.PROTECT,
        verbose_name="Услуга",
    )
    reason = models.TextField("Причина направления")
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_from_referral",
        verbose_name="Созданный прием",
    )
    status = models.CharField("Статус", max_length=30, choices=STATUS_CHOICES, default="created")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Направил",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Направление к специалисту"
        verbose_name_plural = "Направления к специалистам"

    def __str__(self):
        return f"{self.patient} -> {self.target_doctor}"


class DiagnosticStudyCatalog(models.Model):
    STUDY_KIND_CHOICES = [
        ("lab", "Лабораторное"),
        ("instrumental", "Инструментальное"),
    ]

    name = models.CharField("Наименование исследования", max_length=255)
    kind = models.CharField("Тип исследования", max_length=20, choices=STUDY_KIND_CHOICES)
    unit = models.CharField("Единица измерения", max_length=50, blank=True)
    reference_range = models.CharField("Референсные значения", max_length=255, blank=True)
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        ordering = ["kind", "name"]
        verbose_name = "Справочник исследований"
        verbose_name_plural = "Справочник исследований"

    def __str__(self):
        return self.name


class DiagnosticStudyResult(models.Model):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="study_results",
        verbose_name="Прием",
    )
    study = models.ForeignKey(
        DiagnosticStudyCatalog,
        on_delete=models.PROTECT,
        verbose_name="Исследование",
    )
    result_value = models.CharField("Результат", max_length=255, blank=True)
    conclusion = models.TextField("Заключение", blank=True)
    include_in_reasoning = models.BooleanField("Включать в обоснование", default=True)
    performed_at = models.DateTimeField("Дата выполнения", null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="performed_study_results",
        verbose_name="Кто выполнил",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Результат исследования"
        verbose_name_plural = "Результаты исследований"

    def __str__(self):
        return f"{self.study} - {self.result_value or 'без результата'}"
