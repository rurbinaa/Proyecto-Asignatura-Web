from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import RevisionDefect, Mockup
from .serializers import RevisionDefectSerializer, MockupSerializer


# Endpoint para capturar defectos durante la inspección y para deshacer la última captura de defectos
class RevisionDefectViewSet(viewsets.ModelViewSet):
    queryset = RevisionDefect.objects.all()
    serializer_class = RevisionDefectSerializer
    
    def perform_create(self, serializer):
        serializer.save(inspector=self.request.user)
    
    @action(detail=False, methods=['delete'], url_path='undo')
    def undo(self, request):
        last_defect = RevisionDefect.objects.filter(inspector=request.user).order_by('-timestamp').first()
        if last_defect:
            last_defect.delete()
            return Response({"message": "Última captura de defectos eliminada"}, status=200)
        return Response({"message": "No se encontró ninguna captura de defectos para eliminar"}, status=404)

# Endpoint para obtener la metadata del mockup asociado a una inspección específica
class MockupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mockup.objects.all()
    serializer_class = MockupSerializer
