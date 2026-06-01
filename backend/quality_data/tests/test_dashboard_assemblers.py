"""
Tests for dashboard_assemblers.py — payload assembly from pre-computed KPI data.

Verifies:
  - build_container_payload serializes each KPI through the correct serializer
  - build_seconds_a4_payload matches the live DTO contract
  - build_seconds_general_payload matches the live DTO contract
  - build_qcfa_payload matches the volatile endpoint contract
  - Empty/missing KPI data produces correct empty/null values
"""

from django.test import TestCase

from quality_data.dashboard_assemblers import (
    build_container_payload,
    build_seconds_a4_payload,
    build_seconds_general_payload,
    build_qcfa_payload,
)
from quality_data.serializers import (
    ScalarMetricSerializer,
    KpiDonutSerializer,
    KpiSeriesSerializer,
    KpiBarSerializer,
    WorstContainerSerializer,
)


class BuildContainerPayloadTest(TestCase):
    """build_container_payload must produce the canonical container KPI shape."""

    def setUp(self):
        self.sample_kpis = {
            "executive_summary": [
                {"label": "Total Containers", "value": 3},
                {"label": "Average Pass Rate", "value": 70.0},
                {"label": "Total Palettes Inspected", "value": 60},
                {"label": "Total Rejected Palettes", "value": 20},
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
            "top_defects": [{"label": "Dirt Label", "value": 12}],
            "defect_composition": [{"name": "Dirt Label", "value": 12}],
            "worst_containers": [
                {
                    "containerNumber": 101, "customer": "AlphaCorp",
                    "passRate": 50.0, "rejectedPalettes": 15,
                    "inspectionDate": "2025-01-11",
                }
            ],
        }

    def test_returns_all_container_kpi_keys(self):
        payload = build_container_payload(self.sample_kpis)
        expected_keys = {
            "executive_summary", "containers_by_state",
            "pass_rate_trend", "inspected_trend", "rejected_trend",
            "top_defects", "defect_composition", "worst_containers",
        }
        self.assertEqual(set(payload.keys()), expected_keys)

    def test_executive_summary_serialized_via_scalar_metric(self):
        payload = build_container_payload(self.sample_kpis)
        data = payload["executive_summary"]
        # ScalarMetricSerializer produces {label, value} per item
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        self.assertIn("label", data[0])
        self.assertIn("value", data[0])

    def test_containers_by_state_donut_shape(self):
        payload = build_container_payload(self.sample_kpis)
        data = payload["containers_by_state"]
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        for item in data:
            self.assertIn("name", item)
            self.assertIn("value", item)

    def test_worst_containers_dto_shape(self):
        payload = build_container_payload(self.sample_kpis)
        data = payload["worst_containers"]
        self.assertIsInstance(data, list)
        if data:
            row = data[0]
            self.assertIn("containerNumber", row)
            self.assertIn("customer", row)
            self.assertIn("passRate", row)
            self.assertIn("rejectedPalettes", row)
            self.assertIn("inspectionDate", row)

    def test_trend_kpis_use_series_serializer(self):
        payload = build_container_payload(self.sample_kpis)
        for key in ("pass_rate_trend", "inspected_trend", "rejected_trend"):
            data = payload[key]
            self.assertIsInstance(data, list, f"{key} should be a list")
            if data:
                self.assertIn("name", data[0])
                self.assertIn("data", data[0])

    def test_empty_executive_summary_still_serializes(self):
        kpis = {k: v for k, v in self.sample_kpis.items()}
        kpis["executive_summary"] = []
        payload = build_container_payload(kpis)
        self.assertEqual(payload["executive_summary"], [])

    def test_missing_kpi_returns_none(self):
        payload = build_container_payload({})
        self.assertIsNone(payload.get("executive_summary"))


class BuildSecondsA4PayloadTest(TestCase):
    """build_seconds_a4_payload must match the live SecondsA4 contract."""

    def setUp(self):
        self.sample_kpis = {
            "filter_options": {
                "year": [2025], "week": [1, 2], "line": ["L1"],
                "cut_num": [101], "style": ["ST-A"], "color": ["Red"],
            },
            "executive_summary": {
                "totals": {"total_of_2ds": 100, "seconds_by_sew": 60,
                           "seconds_by_fab": 40, "seconds_sew_a4": 50,
                           "seconds_fab_a4": 30, "accepted": 80, "rejected": 20},
                "percentages": [],
            },
            "weekly_trend": [{"name": "2DS", "data": []}],
            "sew_vs_fab": [{"label": "Sew", "value": 60}, {"label": "Fabric", "value": 40}],
            "by_style": [{"label": "ST-A", "value": 100}],
            "by_color": [{"label": "Red", "value": 100}],
            "by_line": [{"label": "L1", "value": 100}],
            "by_cut": [{"label": "Cut 101", "value": 100}],
            "pass_fail_weekly": [
                {"name": "Pass", "data": []},
                {"name": "Fail", "data": []},
            ],
        }

    def test_has_all_seconds_a4_keys(self):
        payload = build_seconds_a4_payload(self.sample_kpis)
        expected = {
            "filter_options", "executive_summary", "weekly_trend",
            "sew_vs_fab", "by_style", "by_color", "by_line", "by_cut",
            "pass_fail_weekly",
        }
        self.assertEqual(set(payload.keys()), expected)

    def test_filter_options_passthrough(self):
        """filter_options is not serialized — raw dict is the contract."""
        payload = build_seconds_a4_payload(self.sample_kpis)
        self.assertEqual(payload["filter_options"]["year"], [2025])

    def test_executive_summary_passthrough(self):
        """executive_summary is not serialized — raw dict is the contract."""
        payload = build_seconds_a4_payload(self.sample_kpis)
        self.assertEqual(payload["executive_summary"]["totals"]["total_of_2ds"], 100)


class BuildSecondsGeneralPayloadTest(TestCase):
    """build_seconds_general_payload must match the live Seconds General contract."""

    def setUp(self):
        self.sample_kpis = {
            "filter_options": {
                "customer": ["A"], "style": ["ST-1"], "week": [1],
                "color": ["Red"], "size": ["M"], "team": [5],
            },
            "defects_by_customer": [{"label": "A", "value": 50}],
            "defects_by_style": [{"label": "ST-1", "value": 50}],
            "weekly_trend": [{"name": "Defects", "data": []}],
            "sewing_vs_fabric": [{"label": "Sewing", "value": 30}, {"label": "Fabric", "value": 20}],
            "production_totals": {"total_produced": 100, "total_fixed": 60, "total_definitive": 40},
            "top_sewing_defects": [{"label": "Picado", "value": 15}],
            "top_fabric_defects": [{"label": "Corrido", "value": 10}],
            "fix_vs_definitive": [{"name": "Fixed", "data": []}, {"name": "Definitive", "data": []}],
            "defects_by_color": [{"label": "Red", "value": 25}],
            "defects_by_size": [{"label": "M", "value": 25}],
            "defects_by_line": [{"label": "Line 5", "value": 50}],
        }

    def test_has_all_seconds_general_keys(self):
        payload = build_seconds_general_payload(self.sample_kpis)
        expected = {
            "filter_options", "defects_by_customer", "defects_by_style",
            "weekly_trend", "sewing_vs_fabric", "production_totals",
            "top_sewing_defects", "top_fabric_defects", "fix_vs_definitive",
            "defects_by_color", "defects_by_size", "defects_by_line",
        }
        self.assertEqual(set(payload.keys()), expected)

    def test_production_totals_passthrough(self):
        """production_totals is not serialized — raw dict is the contract."""
        payload = build_seconds_general_payload(self.sample_kpis)
        self.assertEqual(payload["production_totals"]["total_produced"], 100)

    def test_bar_kpis_serialized_correctly(self):
        payload = build_seconds_general_payload(self.sample_kpis)
        for key in ("defects_by_customer", "defects_by_style", "sewing_vs_fabric"):
            data = payload[key]
            self.assertIsInstance(data, list)
            if data:
                self.assertIn("label", data[0])
                self.assertIn("value", data[0])


class BuildQcfaPayloadTest(TestCase):
    """build_qcfa_payload must match the volatile 16-KPI contract."""

    def setUp(self):
        self.sample_kpis = {
            "aql_by_style": [{"label": "ST-A", "value": 2.5}],
            "aql_by_team": [{"label": "1", "value": 3.5}],
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

    def test_has_all_qcfa_keys(self):
        payload = build_qcfa_payload(self.sample_kpis)
        expected = {
            "aql_by_style", "aql_by_team", "aql_weekly", "audited_pieces",
            "ac_re_rate_by_line", "seconds_rework",
            "performance_by_customer", "performance_by_line",
            "top_defects", "fabric_defects", "defects_by_style_type",
            "pass_reject_distribution", "rejected_evolution",
            "containers_by_state", "defect_rate",
            "defect_composition", "defect_trend_top_3",
            "filter_options",
        }
        self.assertEqual(set(payload.keys()), expected)

    def test_defect_rate_uses_scalar_metric(self):
        payload = build_qcfa_payload(self.sample_kpis)
        self.assertEqual(payload["defect_rate"]["label"], "Defect Rate")
        self.assertEqual(payload["defect_rate"]["value"], 2.34)

    def test_containers_by_state_may_be_none(self):
        kpis = dict(self.sample_kpis)
        kpis["containers_by_state"] = None
        payload = build_qcfa_payload(kpis)
        self.assertIsNone(payload["containers_by_state"])
