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
            'height',
        ]


class FlexiblePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    A PrimaryKeyRelatedField that accepts both integer IDs and string names.
    If a string is passed, it looks up or creates the related object by name.
    """
    
    def __init__(self, **kwargs):
        self.get_or_create_name = kwargs.pop('get_or_create_name', None)
        self.get_or_create_defaults = kwargs.pop('get_or_create_defaults', {'is_active': True})
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        # If it's an integer, use default behavior
        if isinstance(data, int):
            return super().to_internal_value(data)
        
        # If it's a string, treat as name and get_or_create
        if isinstance(data, str):
            data = data.strip()
            if not data:
                raise serializers.ValidationError({self.field_name: 'This field is required.'})
            
            model = self.queryset.model
            name = data.lower().replace(' ', '_')
            
            obj, _ = model.objects.get_or_create(
                name=name,
                defaults=self.get_or_create_defaults
            )
            return obj
        
        raise serializers.ValidationError(
            {self.field_name: 'Must be an integer ID or string name.'}
        )


class InspectionDataSerializer(serializers.ModelSerializer):
    inspector = serializers.CharField(source='inspector.get_full_name', read_only=True)
    color = FlexiblePrimaryKeyRelatedField(
        queryset=Color.objects.filter(is_active=True),
        get_or_create_defaults={'is_active': True},
    )

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
            'lot',
            'color',
            'is_closed',
            'status',
            'closed_at',
        ]
        read_only_fields = [
            'id', 'inspector', 'date', 'week',
            'is_closed', 'status', 'closed_at',
        ]


class RevisionDefectSerializer(serializers.ModelSerializer):
    inspection = serializers.PrimaryKeyRelatedField(queryset=InspectionData.objects.all())
    inspector = serializers.PrimaryKeyRelatedField(read_only=True)
    defect_type = FlexiblePrimaryKeyRelatedField(
        queryset=DefectType.objects.filter(is_active=True),
        get_or_create_defaults={'is_active': True},
    )

    class Meta:
        model = RevisionDefect
        fields = [
            'id',
            'inspection',
            'inspector',
            'defect_type',
            'defect_size',
            'notes',
            'defect_count',
            'timestamp',
            'coordinates_x',
            'coordinates_y',
        ]
        read_only_fields = ['id', 'inspector', 'timestamp']
