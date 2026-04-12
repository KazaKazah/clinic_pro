from rest_framework import viewsets
from .models import OutpatientVisit
from .serializers import OutpatientVisitSerializer

class OutpatientVisitViewSet(viewsets.ModelViewSet):
    queryset = OutpatientVisit.objects.all().order_by('-id')
    serializer_class = OutpatientVisitSerializer