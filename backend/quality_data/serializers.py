from rest_framework import serializers
from .models import InspectionDefect, DefectType

from rest_framework import serializers
from .models import InspectionDefect

class DefectSerializer(serializers.ModelSerializer):
    inspector_name = serializers.ReadOnlyField(source='inspector.username')
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = InspectionDefect
        fields = [
            'id', 
            'inspection', 
            'defect_type', 
            'amount', 
            'inspector',
            'inspector_name', 
            'timestamp'
        ]
        read_only_fields = ('inspector', 'timestamp')