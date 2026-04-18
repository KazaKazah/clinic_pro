from django import forms
from django.db.models import Q

from .models import Patient


class PatientSearchForm(forms.Form):
    query = forms.CharField(
        label="ИИН, ФИО или телефон",
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Например: 990101300000 или Иванов",
            }
        ),
    )

    def search(self):
        query = self.cleaned_data["query"].strip()
        return Patient.objects.filter(
            Q(iin__icontains=query)
            | Q(last_name__icontains=query)
            | Q(first_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(phone__icontains=query)
        )


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "iin",
            "birth_date",
            "gender",
            "phone",
            "address",
            "document_number",
            "emergency_contact",
            "note",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
