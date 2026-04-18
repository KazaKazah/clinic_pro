from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import PatientForm, PatientSearchForm


@login_required
def patient_search_page(request):
    form = PatientSearchForm(request.GET or None)
    patients = None
    if form.is_valid():
        patients = form.search()
    return render(request, "patients/search.html", {"form": form, "patients": patients})


@login_required
def patient_create_page(request):
    form = PatientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        patient = form.save()
        messages.success(request, "Пациент добавлен в базу данных.")
        return redirect("outpatient_visit_create_page", patient_id=patient.id)
    return render(request, "patients/form.html", {"form": form})
