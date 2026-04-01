from rest_framework import serializers
from quality_data.models import DefectType, Color
from .models import InspectionData, RevisionDefect, Mockup

class MockupSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Mockup
        fields = [
            'id',
            'name',
            'image',
            'side',
            'width',
            'height'
        ]
        
class InspectionDataSerializer(serializers.ModelSerializer):
    inspector = serializers.CharField(source='inspector.get_full_name', read_only=True)
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.filter(is_active=True))
    class Meta:
        model = InspectionData
        fields = [
            'id',
            'inspector',
            'date',
            'created_at',
            'week',
            'style',
            'size',
            'color',
            'is_closed',
            'status',
            'closed_at'
        ]
        
        read_only_fields = ['id', 'inspector','date', 'week', 'is_closed', 'status', 'closed_at']

class RevisionDefectSerializer(serializers.ModelSerializer):
    inspection = serializers.PrimaryKeyRelatedField(queryset=InspectionData.objects.all())
    inspector = serializers.PrimaryKeyRelatedField(read_only=True)
    defectType = serializers.PrimaryKeyRelatedField(queryset=DefectType.objects.filter(is_active=True))
    class Meta:
        model = RevisionDefect
        fields = [
            'inspection',
            'inspector',
            'defectType',
            'defectSize',
            'notes',
            'defectCount',
            'timestamp',
            'coordinates_x',
            'coordinates_y'
        ]