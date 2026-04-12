from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import OutpatientService
from inventory.services import write_off_materials, restore_materials


@receiver(pre_save, sender=OutpatientService)
def outpatient_service_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_instance = None
        return

    try:
        instance._old_instance = OutpatientService.objects.get(pk=instance.pk)
    except OutpatientService.DoesNotExist:
        instance._old_instance = None


@receiver(post_save, sender=OutpatientService)
def outpatient_service_post_save(sender, instance, created, **kwargs):
    source = f"outpatient:visit:{instance.visit_id}:service:{instance.id}"

    if created:
        if not instance.is_written_off:
            write_off_materials(
                service=instance.service,
                qty=instance.qty,
                source=source
            )
            OutpatientService.objects.filter(pk=instance.pk).update(is_written_off=True)
            instance.is_written_off = True

    else:
        old = getattr(instance, '_old_instance', None)

        if old and old.is_written_off:
            service_changed = old.service_id != instance.service_id
            qty_changed = old.qty != instance.qty

            if service_changed or qty_changed:
                restore_materials(
                    service=old.service,
                    qty=old.qty,
                    source=source + ":restore_old"
                )

                write_off_materials(
                    service=instance.service,
                    qty=instance.qty,
                    source=source + ":write_new"
                )


@receiver(post_delete, sender=OutpatientService)
def outpatient_service_post_delete(sender, instance, **kwargs):
    if instance.is_written_off:
        restore_materials(
            service=instance.service,
            qty=instance.qty,
            source=f"outpatient:visit:{instance.visit_id}:service:{instance.id}:delete_restore"
        )