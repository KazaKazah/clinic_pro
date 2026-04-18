from django.urls import path

from . import views_pages


urlpatterns = [
    path("patients/search/", views_pages.patient_search_page, name="patient_search_page"),
    path("patients/new/", views_pages.patient_create_page, name="patient_create_page"),
]
