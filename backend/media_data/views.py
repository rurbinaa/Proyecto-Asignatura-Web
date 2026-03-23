from django.shortcuts import render
from rest_framework.views import APIView, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import InspectionData, RevisionDefect, Mockup
from .serializers import InspectionDataSerializer, RevisionDefectSerializer, MockupSerializer

# Endpoint para obtener la maqueta según el lote
class MockupMetadataView(APIView):
    def get(self, request):
        return Response({
            "image_url": request.build_absolute_uri(Mockup.objects.first().image.url),
            "width": Mockup.objects.first().width,
            "height": Mockup.objects.first().height
        })

class CaptureDefectView(APIView):
    def post(self, request):
        serializer = RevisionDefectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(inspector=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
# Endpoint para deshacer la última captura de defectos
class UndoCaptureView(viewsets.ViewSet):
    queryset = RevisionDefect.objects.all()
    serializer_class = RevisionDefectSerializer
    
    @action(detail=False, methods=['delete'], url_path='captura/undo/')
    def undo(self, request):
        last_defect = RevisionDefect.objects.filter(inspector=request.user).order_by('-timestamp').first()
        if last_defect:
            last_defect.delete()
            return Response({"message": "Última captura de defectos eliminada"}, status=200)
        return Response({"message": "No se encontró ninguna captura de defectos para eliminar"}, status=404)

# Endpoint para capturar defectos
class CreateDefectView(viewsets.ModelViewSet):
    queryset = RevisionDefect.objects.all()
    serializer_class = RevisionDefectSerializer
    
    
    @action(detail=False, methods=['post'], url_path='captura-defecto/')
    def capture_defect(self, request):
        serializer = RevisionDefectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(inspector=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
