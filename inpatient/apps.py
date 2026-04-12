from django.apps import AppConfig


class InpatientConfig(AppConfig):
    name = 'inpatient'

    def ready(self):
        import inpatient.signals