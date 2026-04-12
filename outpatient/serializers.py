from rest_framework import serializers
from .models import OutpatientVisit

class OutpatientVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model = OutpatientVisit
        fields = '__all__'