from django.urls import path

from . import views


app_name = "reception"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("patients/search/", views.patient_search, name="patient_search"),
    path("patients/new/", views.patient_create, name="patient_create"),
    path("patients/<int:patient_id>/visit/new/", views.create_visit, name="create_visit"),
    path("appointments/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),
    path("doctor/queue/", views.doctor_queue, name="doctor_queue"),
]
