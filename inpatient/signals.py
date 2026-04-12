from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import PrescriptionExecution, InpatientProcedure
from .services import recalculate_admission_cost
from inventory.services import (
    write_off_medication,
    restore_medication,
    write_off_materials,
    restore_materials,
)


@receiver(pre_save, sender=PrescriptionExecution)
def prescription_execution_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_instance = None
        return
    instance._old_instance = PrescriptionExecution.objects.filter(pk=instance.pk).first()


@receiver(post_save, sender=PrescriptionExecution)
def prescription_execution_post_save(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_instance', None)
    source = f"inpatient:admission:{instance.prescription.admission_id}:execution:{instance.id}"

    old_status = old.status if old else None
    new_status = instance.status

    if created:
        if new_status == 'confirmed' and not instance.is_written_off:
            write_off_medication(
                medication=instance.prescription.medication,
                qty=instance.qty,
                source=source
            )
            PrescriptionExecution.objects.filter(pk=instance.pk).update(is_written_off=True)
            instance.is_written_off = True

    else:
        if old_status == 'draft' and new_status == 'confirmed' and not instance.is_written_off:
            write_off_medication(
                medication=instance.prescription.medication,
                qty=instance.qty,
                source=source + ":confirm"
            )
            PrescriptionExecution.objects.filter(pk=instance.pk).update(is_written_off=True)
            instance.is_written_off = True

        elif old_status == 'confirmed' and new_status == 'cancelled' and instance.is_written_off:
            restore_medication(
                medication=instance.prescription.medication,
                qty=instance.qty,
                source=source + ":cancel"
            )
            PrescriptionExecution.objects.filter(pk=instance.pk).update(is_written_off=False)
            instance.is_written_off = False

    recalculate_admission_cost(instance.prescription.admission)


@receiver(post_delete, sender=PrescriptionExecution)
def prescription_execution_post_delete(sender, instance, **kwargs):
    if instance.is_written_off:
        restore_medication(
            medication=instance.prescription.medication,
            qty=instance.qty,
            source=f"inpatient:admission:{instance.prescription.admission_id}:execution:{instance.id}:delete_restore"
        )

    recalculate_admission_cost(instance.prescription.admission)


@receiver(pre_save, sender=InpatientProcedure)
def inpatient_procedure_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_instance = None
        return
    instance._old_instance = InpatientProcedure.objects.filter(pk=instance.pk).first()


@receiver(post_save, sender=InpatientProcedure)
def inpatient_procedure_post_save(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_instance', None)
    source = f"inpatient:admission:{instance.admission_id}:procedure:{instance.id}"

    old_status = old.status if old else None
    new_status = instance.status

    if created:
        if new_status == 'confirmed' and not instance.is_written_off:
            write_off_materials(
                service=instance.service,
                qty=instance.qty,
                source=source
            )
            InpatientProcedure.objects.filter(pk=instance.pk).update(is_written_off=True)
            instance.is_written_off = True

    else:
        if old_status == 'draft' and new_status == 'confirmed' and not instance.is_written_off:
            write_off_materials(
                service=instance.service,
                qty=instance.qty,
                source=source + ":confirm"
            )
            InpatientProcedure.objects.filter(pk=instance.pk).update(is_written_off=True)
            instance.is_written_off = True

        elif old_status == 'confirmed' and new_status == 'cancelled' and instance.is_written_off:
            restore_materials(
                service=instance.service,
                qty=instance.qty,
                source=source + ":cancel"
            )
            InpatientProcedure.objects.filter(pk=instance.pk).update(is_written_off=False)
            instance.is_written_off = False

    recalculate_admission_cost(instance.admission)


@receiver(post_delete, sender=InpatientProcedure)
def inpatient_procedure_post_delete(sender, instance, **kwargs):
    if instance.is_written_off:
        restore_materials(
            service=instance.service,
            qty=instance.qty,
            source=f"inpatient:admission:{instance.admission_id}:procedure:{instance.id}:delete_restore"
        )

    recalculate_admission_cost(instance.admission)