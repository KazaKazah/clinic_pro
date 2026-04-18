from django.urls import path

from . import views_pages


urlpatterns = [
    path("patients/<int:patient_id>/visit/new/", views_pages.visit_create_page, name="outpatient_visit_create_page"),
    path("appointments/<int:appointment_id>/", views_pages.appointment_detail_page, name="appointment_detail_page"),
    path("doctor/queue/", views_pages.doctor_queue_page, name="doctor_queue_page"),
]
