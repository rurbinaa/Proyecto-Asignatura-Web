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
    value = serializers.JSONField()


class KpiPointSerializer(serializers.Serializer):
    """Serializer for a single point in a time series chart."""
    x = serializers.JSONField()
    y = serializers.FloatField()

class KpiSeriesSerializer(serializers.Serializer):
    """
    Serializer for time series / line chart data.
    
    Output format:
        {"name": "Series Name", "data": [{"x": "2025-W01", "y": 42.5}, ...]}
    """
    name = serializers.CharField()
    data = KpiPointSerializer(many=True)


class KpiDonutSerializer(serializers.Serializer):
    """
    Serializer for donut / pie chart data.
    
    Output format:
        {"name": "Category", "value": 150}
    """
    name = serializers.CharField()
    value = serializers.JSONField()


class KpiHeatmapSerializer(serializers.Serializer):
    """
    Serializer for heatmap grid data.
    
    Output format:
        {"x": "Style A", "y": "Defect Type 1", "value": 25}
    """
    x = serializers.CharField()
    y = serializers.CharField()
    value = serializers.JSONField()


class KpiBarEnvelopeSerializer(serializers.Serializer):
    """Envelope serializer for bar KPI families returned as {data:[...]}"""

    data = KpiBarSerializer(many=True)


class KpiSeriesEnvelopeSerializer(serializers.Serializer):
    """Envelope serializer for series KPI families returned as {data:[...]}"""

    data = KpiSeriesSerializer(many=True)


class KpiDonutEnvelopeSerializer(serializers.Serializer):
    """Envelope serializer for donut KPI families returned as {data:[...]}"""

    data = KpiDonutSerializer(many=True)


class KpiHeatmapEnvelopeSerializer(serializers.Serializer):
    """Envelope serializer for heatmap KPI families returned as {data:[...]}"""

    data = KpiHeatmapSerializer(many=True)


class ScalarMetricSerializer(serializers.Serializer):
    """Serializer for scalar metric contract: {label, value}."""

    label = serializers.CharField()
    value = serializers.FloatField()


class FilterOptionsSerializer(serializers.Serializer):
    """Serializer for filter options endpoint contract."""

    week = serializers.ListField(child=serializers.IntegerField())
    team = serializers.ListField(child=serializers.IntegerField())
    style = serializers.ListField(child=serializers.CharField())
    color = serializers.ListField(child=serializers.CharField())
    customer = serializers.ListField(child=serializers.CharField())
    batch = serializers.ListField(child=serializers.IntegerField())
