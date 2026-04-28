from django.test import TestCase

from quality_data.serializers import (
    KpiBarEnvelopeSerializer,
    KpiSeriesEnvelopeSerializer,
    ScalarMetricSerializer,
    FilterOptionsSerializer,
)


class KpiDtoSerializersTest(TestCase):
    def test_envelope_serializers_expose_data_key(self):
        bar_data = [{"label": "Line 1", "value": 10.0}]
        series_data = [{"name": "AQL", "data": [{"x": 1, "y": 2.5}]}]

        self.assertEqual(KpiBarEnvelopeSerializer({"data": bar_data}).data, {"data": bar_data})
        self.assertEqual(KpiSeriesEnvelopeSerializer({"data": series_data}).data, {"data": series_data})

    def test_scalar_metric_serializer_contract(self):
        serializer = ScalarMetricSerializer(data={"label": "Defect Rate", "value": 2.34})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["label"], "Defect Rate")
        self.assertEqual(serializer.validated_data["value"], 2.34)

    def test_filter_options_serializer_contract(self):
        serializer = FilterOptionsSerializer(
            data={
                "week": [1, 2],
                "team": [1, 2],
                "style": ["Style-1"],
                "color": ["red"],
                "customer": ["CustomerA"],
                "batch": [100],
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["week"], [1, 2])
