"""
Tests for dashboard_contracts.py — shared DTO contracts, bucket rules, and KPI registries.

Verifies:
  - Container state bucket labels match the canonical 4-bucket scheme
  - KPI registries contain the expected keys for each domain
  - Field names and constants match the live endpoint contract
"""

from django.test import TestCase
from quality_data import dashboard_contracts as contract


class ContainerStateBucketsTest(TestCase):
    """CONTAINER_STATE_BUCKET_LABELS must match the canonical 4-range scheme."""

    def test_has_four_buckets(self):
        self.assertEqual(len(contract.CONTAINER_STATE_BUCKET_LABELS), 4)

    def test_bucket_ids_are_1_to_4(self):
        self.assertEqual(set(contract.CONTAINER_STATE_BUCKET_LABELS.keys()), {1, 2, 3, 4})

    def test_bucket_labels_match_canonical_names(self):
        expected = {
            1: "< 80%",
            2: "80-90%",
            3: "90-95%",
            4: "> 95%",
        }
        self.assertEqual(contract.CONTAINER_STATE_BUCKET_LABELS, expected)

    def test_ordered_labels_matches_expected_order(self):
        self.assertEqual(contract.ALL_CONTAINER_STATE_BUCKET_LABELS, [
            "< 80%", "80-90%", "90-95%", "> 95%",
        ])


class DomainKpiKeysTest(TestCase):
    """Each domain KPI key set must contain the exact keys returned by live endpoints."""

    def test_container_kpi_keys(self):
        expected = {
            "executive_summary",
            "containers_by_state",
            "pass_rate_trend",
            "inspected_trend",
            "rejected_trend",
            "top_defects",
            "defect_composition",
            "worst_containers",
        }
        self.assertEqual(contract.CONTAINER_KPI_KEYS, expected)

    def test_seconds_a4_kpi_keys(self):
        expected = {
            "filter_options",
            "executive_summary",
            "weekly_trend",
            "sew_vs_fab",
            "by_style",
            "by_color",
            "by_line",
            "by_cut",
            "pass_fail_weekly",
        }
        self.assertEqual(contract.SECONDS_A4_KPI_KEYS, expected)

    def test_seconds_general_kpi_keys(self):
        expected = {
            "filter_options",
            "defects_by_customer",
            "defects_by_style",
            "weekly_trend",
            "sewing_vs_fabric",
            "production_totals",
            "top_sewing_defects",
            "top_fabric_defects",
            "fix_vs_definitive",
            "defects_by_color",
            "defects_by_size",
            "defects_by_line",
        }
        self.assertEqual(contract.SECONDS_GENERAL_KPI_KEYS, expected)

    def test_qcfa_kpi_keys(self):
        expected = {
            "aql_by_style",
            "aql_by_team",
            "aql_weekly",
            "audited_pieces",
            "ac_re_rate_by_line",
            "seconds_rework",
            "performance_by_customer",
            "performance_by_line",
            "top_defects",
            "fabric_defects",
            "defects_by_style_type",
            "pass_reject_distribution",
            "rejected_evolution",
            "containers_by_state",
            "defect_rate",
            "defect_composition",
            "defect_trend_top_3",
            "filter_options",
        }
        self.assertEqual(contract.QCFA_KPI_KEYS, expected)


class SharedConstantsTest(TestCase):
    """Verify shared constant values match expected semantics."""

    def test_container_executive_summary_labels(self):
        expected = [
            "Total Containers",
            "Average Pass Rate",
            "Total Palettes Inspected",
            "Total Rejected Palettes",
        ]
        self.assertEqual(contract.CONTAINER_EXECUTIVE_SUMMARY_LABELS, expected)

    def test_supported_dashboards(self):
        """The SUPPORTED_DASHBOARDS set must include all 4 domains."""
        self.assertEqual(
            contract.SUPPORTED_DASHBOARDS,
            {"qcfa", "container", "seconds_a4", "seconds_general"},
        )

    def test_container_kpi_registry_has_all_keys(self):
        """Container KPI registry must have an entry for every CONTAINER_KPI_KEYS."""
        registry_keys = {entry[0] for entry in contract.CONTAINER_KPI_REGISTRY}
        self.assertEqual(registry_keys, contract.CONTAINER_KPI_KEYS)

    def test_seconds_a4_kpi_registry_has_all_keys(self):
        registry_keys = {entry[0] for entry in contract.SECONDS_A4_KPI_REGISTRY}
        self.assertEqual(registry_keys, contract.SECONDS_A4_KPI_KEYS)

    def test_seconds_general_kpi_registry_has_all_keys(self):
        registry_keys = {entry[0] for entry in contract.SECONDS_GENERAL_KPI_REGISTRY}
        self.assertEqual(registry_keys, contract.SECONDS_GENERAL_KPI_KEYS)

    def test_qcfa_kpi_registry_has_all_keys(self):
        registry_keys = {entry[0] for entry in contract.QCFA_KPI_REGISTRY}
        self.assertEqual(registry_keys, contract.QCFA_KPI_KEYS)
