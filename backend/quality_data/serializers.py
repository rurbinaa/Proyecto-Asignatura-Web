"""
KPI Serializers for dashboard visualizations.

These serializers transform query data into formats suitable for
various chart types: bar, series, donut, and heatmap.
"""

from rest_framework import serializers


class KpiBarSerializer(serializers.Serializer):
    """
    Serializer for horizontal bar chart data.
    
    Output format:
        {"label": "Style A", "value": 42.5}
    """
    label = serializers.CharField()
    value = serializers.FloatField()


class KpiSeriesSerializer(serializers.Serializer):
    """
    Serializer for time series / line chart data.
    
    Output format:
        {"name": "Series Name", "data": [{"x": "2025-W01", "y": 42.5}, ...]}
    """
    name = serializers.CharField()
    data = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField()
        )
    )


class KpiDonutSerializer(serializers.Serializer):
    """
    Serializer for donut / pie chart data.
    
    Output format:
        {"name": "Category", "value": 150}
    """
    name = serializers.CharField()
    value = serializers.FloatField()


class KpiHeatmapSerializer(serializers.Serializer):
    """
    Serializer for heatmap grid data.
    
    Output format:
        {"x": "Style A", "y": "Defect Type 1", "value": 25}
    """
    x = serializers.CharField()
    y = serializers.CharField()
    value = serializers.FloatField()
