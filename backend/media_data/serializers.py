from rest_framework import serializers
from .models import InspectionData, RevisionDefect, Mockup, LastDefect

class InspectionDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = InspectionData
        fields = '_all_'

class RevisionDefectSerializer(serializers.ModelSerializer):

    class Meta:
        model = RevisionDefect
        fields = '_all_'

class MockupSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Mockup
        fields = '_all_'
