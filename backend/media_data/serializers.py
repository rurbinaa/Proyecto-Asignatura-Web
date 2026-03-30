from rest_framework import serializers
from quality_data.models import DefectType, Color
from .models import InspectionData, RevisionDefect, Mockup

class InspectionDataSerializer(serializers.ModelSerializer):
    inspector = serializers.PrimaryKeyRelatedField(read_only=True)
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.filter(is_active=True))
    class Meta:
        model = InspectionData
        fields = [
        'inspector',
        'created_at',
        'color'
        ]

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

class MockupSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Mockup
        fields = [
            'id',
            'name',
            'image',
            'width',
            'height'
        ]
