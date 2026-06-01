from django.test import TestCase

from quality_data.serializers import (
    KpiBarEnvelopeSerializer,
    KpiSeriesEnvelopeSerializer,
    ScalarMetricSerializer,
    FilterOptionsSerializer,
    KpiBarSerializer,
    KpiDonutSerializer,
    KpiSeriesSerializer,
    WorstContainerSerializer,
)

from quality_data.dashboard_assemblers import (
    build_container_payload,
    build_seconds_a4_payload,
    build_seconds_general_payload,
    build_qcfa_payload,
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


class AssemblerContractValidationTest(TestCase):
    """
    Verify that assembler outputs pass validation through their
    registered serializers — proving the shared contract is stable.
    """

    def test_container_payload_fields_validate_through_serializers(self):
        """Each KPI in the container payload should pass its serializer validation."""
        kpis = {
            "executive_summary": [
                {"label": "Total Containers", "value": 3},
            ],
            "containers_by_state": [
                {"name": "< 80%", "value": 2},
                {"name": "80-90%", "value": 0},
                {"name": "90-95%", "value": 1},
                {"name": "> 95%", "value": 0},
            ],
            "pass_rate_trend": [{"name": "Pass Rate", "data": []}],
            "inspected_trend": [{"name": "Inspected", "data": []}],
            "rejected_trend": [{"name": "Rejected", "data": []}],
            "top_defects": [{"label": "Dirt", "value": 5}],
            "defect_composition": [{"name": "Dirt", "value": 5}],
            "worst_containers": [{
                "containerNumber": 101, "customer": "A",
                "passRate": 50.0, "rejectedPalettes": 5,
                "inspectionDate": "2025-01-11",
            }],
        }
        payload = build_container_payload(kpis)

        # ScalarMetricSerializer — validate executive_summary items
        for item in payload["executive_summary"]:
            s = ScalarMetricSerializer(data=item)
            self.assertTrue(s.is_valid(), f"executive_summary item failed: {s.errors}")

        # KpiDonutSerializer — validate containers_by_state items
        for item in payload["containers_by_state"]:
            s = KpiDonutSerializer(data=item)
            self.assertTrue(s.is_valid(), f"containers_by_state item failed: {s.errors}")

        # KpiSeriesSerializer — validate trend items
        for item in payload["pass_rate_trend"]:
            s = KpiSeriesSerializer(data=item)
            self.assertTrue(s.is_valid(), f"pass_rate_trend item failed: {s.errors}")

        # KpiBarSerializer — validate top_defects items
        for item in payload["top_defects"]:
            s = KpiBarSerializer(data=item)
            self.assertTrue(s.is_valid(), f"top_defects item failed: {s.errors}")

        # KpiDonutSerializer — validate defect_composition items
        for item in payload["defect_composition"]:
            s = KpiDonutSerializer(data=item)
            self.assertTrue(s.is_valid(), f"defect_composition item failed: {s.errors}")

        # WorstContainerSerializer — validate worst_containers items
        for item in payload["worst_containers"]:
            s = WorstContainerSerializer(data=item)
            self.assertTrue(s.is_valid(), f"worst_containers item failed: {s.errors}")

    def test_qcfa_payload_fields_validate_through_serializers(self):
        """Key QC FA KPI fields should pass serializer validation."""
        kpis = {
            "aql_by_style": [{"label": "ST-A", "value": 2.5}],
            "aql_weekly": [{"name": "AQL", "data": []}, {"name": "Trend", "data": []}],
            "audited_pieces": [{"name": "Pieces", "data": []}],
            "ac_re_rate_by_line": [{"label": "1 - PASS", "value": 10}],
            "seconds_rework": [{"name": "Sewing", "data": []}],
            "performance_by_customer": [{"label": "CUST_A", "value": 95.0}],
            "performance_by_line": [{"label": "1", "value": 95.0}],
            "top_defects": [{"label": "Uneven", "value": 5}],
            "fabric_defects": [{"label": "Corrido", "value": 3}],
            "defects_by_style_type": [{"x": "ST-A", "y": "Uneven", "value": 5}],
            "pass_reject_distribution": [{"name": "PASS", "value": 10}],
            "rejected_evolution": [{"name": "Rejected", "data": []}],
            "containers_by_state": [{"name": "< 80%", "value": 1}],
            "defect_rate": {"label": "Defect Rate", "value": 2.34},
            "defect_composition": [{"name": "Uneven", "value": 5}],
            "defect_trend_top_3": [{"name": "Uneven", "data": []}],
            "filter_options": {
                "week": [1], "team": [1], "style": ["ST-A"],
                "color": ["Red"], "customer": ["CUST_A"], "batch": [1],
            },
        }
        payload = build_qcfa_payload(kpis)

        # ScalarMetricSerializer — defect_rate is scalar
        s = ScalarMetricSerializer(data=payload["defect_rate"])
        self.assertTrue(s.is_valid(), f"defect_rate item failed: {s.errors}")

        # KpiBarSerializer — aql_by_style items
        for item in payload["aql_by_style"]:
            s = KpiBarSerializer(data=item)
            self.assertTrue(s.is_valid(), f"aql_by_style item failed: {s.errors}")

        # KpiSeriesSerializer — aql_weekly items
        for item in payload["aql_weekly"]:
            s = KpiSeriesSerializer(data=item)
            self.assertTrue(s.is_valid(), f"aql_weekly item failed: {s.errors}")

        # FilterOptionsSerializer — filter_options
        s = FilterOptionsSerializer(data=payload["filter_options"])
        self.assertTrue(s.is_valid(), f"filter_options item failed: {s.errors}")

    def test_seconds_a4_payload_fields_validate(self):
        """Seconds A4 payload fields should pass serializer validation."""
        kpis = {
            "filter_options": {
                "year": [2025], "week": [1], "line": ["L1"],
                "cut_num": [101], "style": ["ST-A"], "color": ["Red"],
            },
            "executive_summary": {
                "totals": {"total_of_2ds": 100, "seconds_by_sew": 60,
                           "seconds_by_fab": 40, "seconds_sew_a4": 50,
                           "seconds_fab_a4": 30, "accepted": 80, "rejected": 20},
                "percentages": [],
            },
            "weekly_trend": [{"name": "2DS", "data": []}],
            "sew_vs_fab": [{"label": "Sew", "value": 60}],
            "by_style": [{"label": "ST-A", "value": 100}],
            "by_color": [{"label": "Red", "value": 100}],
            "by_line": [{"label": "L1", "value": 100}],
            "by_cut": [{"label": "Cut 101", "value": 100}],
            "pass_fail_weekly": [{"name": "Pass", "data": []}, {"name": "Fail", "data": []}],
        }
        payload = build_seconds_a4_payload(kpis)

        for item in payload["weekly_trend"]:
            s = KpiSeriesSerializer(data=item)
            self.assertTrue(s.is_valid(), f"weekly_trend item failed: {s.errors}")

        for item in payload["sew_vs_fab"]:
            s = KpiBarSerializer(data=item)
            self.assertTrue(s.is_valid(), f"sew_vs_fab item failed: {s.errors}")

    def test_seconds_general_payload_fields_validate(self):
        """Seconds General payload fields should pass serializer validation."""
        kpis = {
            "filter_options": {
                "customer": ["A"], "style": ["ST-1"], "week": [1],
                "color": ["Red"], "size": ["M"], "team": [5],
            },
            "defects_by_customer": [{"label": "A", "value": 50}],
            "defects_by_style": [{"label": "ST-1", "value": 50}],
            "weekly_trend": [{"name": "Defects", "data": []}],
            "sewing_vs_fabric": [{"label": "Sewing", "value": 30}],
            "production_totals": {"total_produced": 100, "total_fixed": 60, "total_definitive": 40},
            "top_sewing_defects": [{"label": "Picado", "value": 15}],
            "top_fabric_defects": [{"label": "Corrido", "value": 10}],
            "fix_vs_definitive": [{"name": "Fixed", "data": []}, {"name": "Definitive", "data": []}],
            "defects_by_color": [{"label": "Red", "value": 25}],
            "defects_by_size": [{"label": "M", "value": 25}],
            "defects_by_line": [{"label": "Line 5", "value": 50}],
        }
        payload = build_seconds_general_payload(kpis)

        for item in payload["defects_by_customer"]:
            s = KpiBarSerializer(data=item)
            self.assertTrue(s.is_valid(), f"defects_by_customer item failed: {s.errors}")

        for item in payload["weekly_trend"]:
            s = KpiSeriesSerializer(data=item)
            self.assertTrue(s.is_valid(), f"weekly_trend item failed: {s.errors}")
