from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import RevisionDefect, Mockup, InspectionData
from .serializers import RevisionDefectSerializer, MockupSerializer, InspectionDataSerializer


class MockupViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve mockup images for the capture interface."""
    queryset = Mockup.objects.all()
    serializer_class = MockupSerializer


class InspectionDataViewSet(viewsets.ModelViewSet):
    """
    Manage inspection sessions.

    Custom actions:
    - POST /inspections/<pk>/close_inspection/ — close and evaluate result
    """
    queryset = InspectionData.objects.all()
    serializer_class = InspectionDataSerializer

    @action(detail=True, methods=['post'])
    def close_inspection(self, request, pk=None):
        """
        Close an inspection and determine PASS/REJECT status.

        Logic:
        - If no defects were recorded → PASS
        - If any defects were recorded → REJECT
        """
        inspection = self.get_object()

        if inspection.is_closed:
            return Response(
                {"error": "The inspection is already closed"},
                status=400,
            )

        # Count total defects captured during this inspection
        total_defects = RevisionDefect.objects.filter(
            inspection=inspection,
        ).count()

        # Determine result based on defect presence
        inspection.status = 'REJECT' if total_defects > 0 else 'PASS'
        inspection.is_closed = True
        inspection.closed_at = timezone.now()
        inspection.save()

        return Response({
            'message': 'Inspection closed successfully',
            'closed_at': inspection.closed_at,
            'result': inspection.status,
            'total_defects': total_defects,
        })


class RevisionDefectViewSet(viewsets.ModelViewSet):
    """
    Capture and manage individual defects during an inspection.

    Custom actions:
    - DELETE /defects/undo/?inspection=<id> — remove last defect for inspection
    """
    queryset = RevisionDefect.objects.all()
    serializer_class = RevisionDefectSerializer

    def perform_create(self, serializer):
        serializer.save(inspector=self.request.user)

    @action(detail=False, methods=['delete'], url_path='undo')
    def undo(self, request):
        """
        Remove the most recently captured defect for a specific inspection.

        Query param:
        - inspection: inspection ID (required)
        """
        inspection_id = request.query_params.get('inspection')

        if not inspection_id:
            return Response(
                {"error": "inspection query parameter is required"},
                status=400,
            )

        last_defect = RevisionDefect.objects.filter(
            inspection_id=inspection_id,
        ).order_by('-timestamp').first()

        if last_defect:
            last_defect.delete()
            return Response(
                {"message": "Last defect capture removed"},
                status=200,
            )

        return Response(
            {"message": "No defect captures were found to remove"},
            status=404,
        )
