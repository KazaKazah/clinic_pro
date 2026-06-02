from django.urls import path
from . import views_pages

urlpatterns = [
    path("patients/<int:patient_id>/visit/new/", views_pages.visit_create_page, name="outpatient_visit_create_page"),
    path("appointments/reserve/", views_pages.reserve_appointment_page, name="reserve_appointment_page"),
    path("appointments/<int:appointment_id>/", views_pages.appointment_detail_page, name="appointment_detail_page"),
    path("appointments/<int:appointment_id>/print/", views_pages.appointment_print_page, name="appointment_print_page"),
    path("appointments/<int:appointment_id>/inpatient/", views_pages.inpatient_record_page, name="inpatient_record_page"),
    path("appointments/<int:appointment_id>/consultation/", views_pages.appointment_consultation_page, name="appointment_consultation_page"),
    path("appointments/<int:appointment_id>/activate-reservation/", views_pages.activate_reservation_page, name="activate_reservation_page"),
    path("appointments/<int:appointment_id>/cancel-reservation/", views_pages.cancel_reservation_page, name="cancel_reservation_page"),
    path("doctor/queue/", views_pages.doctor_queue_page, name="doctor_queue_page"),
    path("inpatient/", views_pages.inpatient_records_page, name="inpatient_records_page"),
    path("patients/<int:patient_id>/history/", views_pages.patient_history_page, name="patient_history_page"),
    path("payments/unpaid/", views_pages.unpaid_appointments_page, name="unpaid_appointments_page"),
    path("icd10/search/", views_pages.icd10_search_api, name="icd10_search_api"),
    path(
        "appointments/<int:appointment_id>/payment-status/",
        views_pages.appointment_payment_status_update_page,
        name="appointment_payment_status_update_page",
    ),
]
