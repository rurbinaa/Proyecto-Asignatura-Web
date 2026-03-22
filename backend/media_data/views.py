from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import InspectionDefect, DefectType
from .serializers import DefectSerializer

# Endpoint para obtener la maqueta según el lote
class MockupMetadataView(APIView):
    def get(self, request, lote_id):
       
        return Response({
            "technical_image_url": request.build_absolute_uri('/media/mockups/shirt.png'),
            "dimensions": {"width": 1024, "height": 768}
        })
    
# Endpoint para deshacer la última captura de defectos del inspector
class UndoCaptureView(APIView):
    def delete(self, request):
        last_defect = InspectionDefect.objects.filter(
            inspector=request.user
        ).last()

        if last_defect:
            last_defect.delete()
            return Response({"message": "Last record deleted"}, status=204)
        return Response({"error": "No records found"}, status=404)

class CreateDefectView(APIView):
    def post(self, request):
        serializer = DefectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(inspector=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
