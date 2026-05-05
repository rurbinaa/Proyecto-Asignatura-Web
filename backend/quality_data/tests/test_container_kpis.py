"""
Tests for Container KPI endpoints under /quality/kpis/container/*.

Covers:
  - ContainerFilterMixin: precedence, inclusive dates, null-date handling, 400s, customer
  - Executive summary contract
  - Containers-by-state DTO shape
  - Trend KPIs (pass-rate, inspected, rejected) DTO shapes
  - Defect KPIs (top-defects, defect-composition) DTO shapes
  - Worst-containers ordering and DTO shape
"""

import datetime
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status

from quality_data.models import Container, ContainerDefectType, ContainerInspectionDefect


# ─────────────────────────────────────────────────────────
# Shared fixture helpers
# ─────────────────────────────────────────────────────────


class ContainerKpiTestMixin:
    """Mixin that provides shared setup for Container KPI tests."""

    def setUp(self):
        self.client = APIClient()

        # ContainerDefectType records for defect-related KPIs
        self.defect_type_a = ContainerDefectType.objects.create(name="Broken Seal")
        self.defect_type_b = ContainerDefectType.objects.create(name="Dented Wall")
        self.defect_type_c = ContainerDefectType.objects.create(name="Rust Spot")

        # Container records with varied dates, customers, and pass rates
        self.c1 = Container.objects.create(
            container_number=100,
            date="2025-01-10",
            customer="AlphaCorp",
            total_palette=20,
            total_palette_pass=18,
            total_palette_rejected=2,
            percentage_pass=90.0,
            percentage_reject=10.0,
        )
        self.c2 = Container.objects.create(
            container_number=101,
            date="2025-01-11",
            customer="AlphaCorp",
            total_palette=30,
            total_palette_pass=15,
            total_palette_rejected=15,
            percentage_pass=50.0,
            percentage_reject=50.0,
        )
        self.c3 = Container.objects.create(
            container_number=102,
            date="2025-01-12",
            customer="BetaInc",
            total_palette=10,
            total_palette_pass=7,
            total_palette_rejected=3,
            percentage_pass=70.0,
            percentage_reject=30.0,
        )
        self.c4 = Container.objects.create(
            container_number=103,
            date=None,
            customer="AlphaCorp",
            total_palette=40,
            total_palette_pass=39,
            total_palette_rejected=1,
            percentage_pass=97.5,
            percentage_reject=2.5,
        )
        # Container with 95.0 exactly (boundary for > 95% bucket)
        self.c5 = Container.objects.create(
            container_number=104,
            date="2025-01-13",
            customer="BetaInc",
            total_palette=15,
            total_palette_pass=14,
            total_palette_rejected=1,
            percentage_pass=95.0,
            percentage_reject=5.0,
        )
        # Container with 95.1 (> 95% bucket)
        self.c6 = Container.objects.create(
            container_number=105,
            date="2025-01-14",
            customer="GammaLtd",
            total_palette=25,
            total_palette_pass=24,
            total_palette_rejected=1,
            percentage_pass=96.0,
            percentage_reject=4.0,
        )
        # Container for 80% boundary (80-90% bucket)
        self.c7 = Container.objects.create(
            container_number=106,
            date="2025-01-10",
            customer="AlphaCorp",
            total_palette=12,
            total_palette_pass=10,
            total_palette_rejected=2,
            percentage_pass=80.0,
            percentage_reject=20.0,
        )

        # ContainerInspectionDefect records
        ContainerInspectionDefect.objects.create(
            container=self.c1, defect_type=self.defect_type_a, amount=5,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c1, defect_type=self.defect_type_b, amount=3,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c2, defect_type=self.defect_type_a, amount=7,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c2, defect_type=self.defect_type_c, amount=2,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c3, defect_type=self.defect_type_b, amount=4,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c4, defect_type=self.defect_type_a, amount=1,
        )


# ─────────────────────────────────────────────────────────
# Task 2.1 — Filter tests
# ─────────────────────────────────────────────────────────


class ContainerDateRangeFilterTest(ContainerKpiTestMixin, TestCase):
    """Tests for ContainerFilterMixin date filtering behavior."""

    def test_date_range_inclusive_bounds(self):
        """date_range=2025-01-10,2025-01-11 should include both dates."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-11")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # c1 (Jan 10), c2 (Jan 11), c7 (Jan 10) → 3 containers dated in range
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        self.assertEqual(total, 3)

    def test_date_range_excludes_null_dates(self):
        """Container c4 has date=None and must be excluded when dates are filtered."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=2025-01-01,2025-01-31")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        # c4 (null date) excluded; c1,c2,c3,c5,c6,c7 included = 6
        self.assertEqual(total, 6)

    def test_date_range_takes_precedence_over_from_to(self):
        """date_range narrows to one day; broader from/to should be ignored."""
        url = reverse("quality_data:kpi-container-containers-by-state")
        params = "date_range=2025-01-11,2025-01-11&from_date=2025-01-01&to_date=2025-01-31"
        response = self.client.get(f"{url}?{params}")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        # Only c2 has date=2025-01-11
        self.assertEqual(total, 1)

    def test_blank_date_range_falls_back_to_from_to(self):
        """Empty date_range param should fall back to from_date/to_date."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(
            f"{url}?date_range=&from_date=2025-01-10&to_date=2025-01-11"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        self.assertEqual(total, 3)

    def test_partial_date_range_start_only_returns_400(self):
        """date_range=2025-01-10, should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=2025-01-10,")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_partial_date_range_end_only_returns_400(self):
        """date_range=,2025-01-10 should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_comma_only_date_range_returns_400(self):
        """date_range=, should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=,")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_reversed_date_range_returns_400(self):
        """date_range=2025-01-12,2025-01-10 should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?date_range=2025-01-12,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_reversed_from_to_returns_400(self):
        """from_date=2025-01-12&to_date=2025-01-10 should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?from_date=2025-01-12&to_date=2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("from_date", response.data)
        self.assertIn("to_date", response.data)

    def test_invalid_date_format_returns_400(self):
        """from_date=10-01-2025 should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?from_date=10-01-2025&to_date=2025-01-31")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("from_date", response.data)

    def test_invalid_to_date_format_returns_400(self):
        """to_date=31-01-2025 should return 400."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?from_date=2025-01-01&to_date=31-01-2025")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("to_date", response.data)

    def test_from_date_only_filters_gte(self):
        """from_date without to_date filters date >= from_date."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?from_date=2025-01-13")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        # c5 (Jan 13), c6 (Jan 14) = 2 dated containers; c4 excluded (null)
        self.assertEqual(total, 2)

    def test_to_date_only_filters_lte(self):
        """to_date without from_date filters date <= to_date."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?to_date=2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        # c1 (Jan 10), c7 (Jan 10) = 2; null-date c4 excluded
        self.assertEqual(total, 2)


class ContainerCustomerFilterTest(ContainerKpiTestMixin, TestCase):
    """Tests for Container customer filtering."""

    def test_customer_filter_exact_match(self):
        """customer=AlphaCorp returns only AlphaCorp containers."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?customer=AlphaCorp")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        # c1, c2, c4, c7 are AlphaCorp
        self.assertEqual(total, 4)

    def test_customer_filter_case_sensitive(self):
        """customer=alphacorp (lowercase) returns 0 because field is exact match."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(f"{url}?customer=alphacorp")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        self.assertEqual(total, 0)

    def test_customer_filter_combined_with_date_range(self):
        """Customer and date_range filters combine (AND logic)."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(
            f"{url}?customer=AlphaCorp&date_range=2025-01-10,2025-01-10"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = next(item["value"] for item in response.data if item["label"] == "Total Containers")
        # c1 (Jan 10, AlphaCorp), c7 (Jan 10, AlphaCorp) = 2
        self.assertEqual(total, 2)


# ─────────────────────────────────────────────────────────
# Task 2.2 — Contract tests (DTO shapes)
# ─────────────────────────────────────────────────────────


class ContainerExecutiveSummaryContractTest(ContainerKpiTestMixin, TestCase):
    """Contract tests for GET /quality/kpis/container/executive-summary/"""

    def test_returns_200_with_expected_structure(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_response_contains_all_expected_labels(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        labels = {item["label"] for item in response.data}
        expected = {
            "Total Containers",
            "Average Pass Rate",
            "Total Palettes Inspected",
            "Total Rejected Palettes",
        }
        self.assertEqual(labels, expected)

    def test_each_item_has_label_and_value(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_total_containers_matches_unfiltered_count(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        total = next(
            item["value"] for item in response.data if item["label"] == "Total Containers"
        )
        self.assertEqual(total, Container.objects.count())

    def test_average_pass_rate_is_mean_of_percentage_pass(self):
        """Average pass rate computed as AVG of percentage_pass across all containers."""
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        avg_pass = next(
            item["value"] for item in response.data if item["label"] == "Average Pass Rate"
        )
        expected_avg = round(
            sum(c.percentage_pass for c in Container.objects.all()) / Container.objects.count(), 2
        )
        self.assertAlmostEqual(avg_pass, expected_avg)

    def test_total_palettes_inspected_is_sum(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        total_palettes = next(
            item["value"] for item in response.data if item["label"] == "Total Palettes Inspected"
        )
        expected = sum(c.total_palette for c in Container.objects.all())
        self.assertEqual(total_palettes, expected)

    def test_total_rejected_palettes_is_sum(self):
        url = reverse("quality_data:kpi-container-executive-summary")
        response = self.client.get(url)
        rejected = next(
            item["value"] for item in response.data if item["label"] == "Total Rejected Palettes"
        )
        expected = sum(c.total_palette_rejected for c in Container.objects.all())
        self.assertEqual(rejected, expected)


class ContainerStateKpiContractTest(ContainerKpiTestMixin, TestCase):
    """Contract tests for GET /quality/kpis/container/containers-by-state/"""

    def test_returns_200_with_four_buckets(self):
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        names = {item["name"] for item in response.data}
        self.assertEqual(names, {"< 80%", "80-90%", "90-95%", "> 95%"})

    def test_each_item_has_name_and_value(self):
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    def test_total_matches_container_count(self):
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, Container.objects.count())

    def test_bucket_boundary_80_included_in_80_90(self):
        """Container with exactly 80% pass rate falls in 80-90% bucket."""
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        counts = {item["name"]: item["value"] for item in response.data}
        # c7 has 80.0% → 80-90% bucket
        self.assertGreaterEqual(counts["80-90%"], 1)

    def test_bucket_boundary_95_excluded_from_gt_95(self):
        """Container with exactly 95% falls in 90-95%, NOT > 95%."""
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        counts = {item["name"]: item["value"] for item in response.data}
        # c5 has 95.0% → 90-95% bucket (NOT > 95%)
        self.assertGreaterEqual(counts["90-95%"], 1)

    def test_bucket_gt_95_includes_above_95(self):
        """Container with 96% falls in > 95% bucket."""
        url = reverse("quality_data:kpi-container-containers-by-state")
        response = self.client.get(url)
        counts = {item["name"]: item["value"] for item in response.data}
        # c4 (97.5%), c6 (96.0%) → > 95%
        self.assertGreaterEqual(counts["> 95%"], 2)


class ContainerTrendKpisContractTest(ContainerKpiTestMixin, TestCase):
    """Contract tests for trend endpoints: pass-rate-trend, inspected-trend, rejected-trend."""

    def test_pass_rate_trend_returns_series_structure(self):
        url = reverse("quality_data:kpi-container-pass-rate-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        series = response.data[0]
        self.assertIn("name", series)
        self.assertIn("data", series)
        self.assertIsInstance(series["data"], list)
        if series["data"]:
            point = series["data"][0]
            self.assertIn("x", point)
            self.assertIn("y", point)

    def test_inspected_trend_returns_series_structure(self):
        url = reverse("quality_data:kpi-container-inspected-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        series = response.data[0]
        self.assertIn("name", series)
        self.assertIn("data", series)

    def test_rejected_trend_returns_series_structure(self):
        url = reverse("quality_data:kpi-container-rejected-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        series = response.data[0]
        self.assertIn("name", series)
        self.assertIn("data", series)

    def test_trend_data_sorted_by_date_ascending(self):
        """Trend x-values (dates) must be chronological."""
        url = reverse("quality_data:kpi-container-pass-rate-trend")
        response = self.client.get(url)
        series = response.data[0]
        dates = [point["x"] for point in series["data"]]
        self.assertEqual(dates, sorted(dates))

    def test_pass_rate_trend_excludes_null_dates(self):
        """Containers with null date should not appear in trend data."""
        url = reverse("quality_data:kpi-container-pass-rate-trend")
        response = self.client.get(url)
        series = response.data[0]
        dates = [point["x"] for point in series["data"]]
        self.assertNotIn(None, dates)

    def test_trend_respects_date_range_filter(self):
        """Trend endpoints honor date_range filtering."""
        url = reverse("quality_data:kpi-container-rejected-trend")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series = response.data[0]
        # Only c1 and c7 have date 2025-01-10
        self.assertEqual(len(series["data"]), 1)


class ContainerDefectKpisContractTest(ContainerKpiTestMixin, TestCase):
    """Contract tests for top-defects and defect-composition endpoints."""

    def test_top_defects_returns_bar_structure(self):
        url = reverse("quality_data:kpi-container-top-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if response.data:
            item = response.data[0]
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_top_defects_sorted_by_value_desc(self):
        url = reverse("quality_data:kpi-container-top-defects")
        response = self.client.get(url)
        if len(response.data) > 1:
            values = [item["value"] for item in response.data]
            for i in range(len(values) - 1):
                self.assertGreaterEqual(values[i], values[i + 1])

    def test_defect_composition_returns_donut_structure(self):
        url = reverse("quality_data:kpi-container-defect-composition")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if response.data:
            item = response.data[0]
            self.assertIn("name", item)
            self.assertIn("value", item)

    def test_defect_composition_excludes_zero_totals(self):
        url = reverse("quality_data:kpi-container-defect-composition")
        response = self.client.get(url)
        for item in response.data:
            self.assertGreater(item["value"], 0)

    def test_defect_kpis_respect_filter(self):
        """Defect endpoints should filter by container's date/customer."""
        url = reverse("quality_data:kpi-container-top-defects")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only defects from c1 and c7 (both on Jan 10)
        # c1: defect_a=5, defect_b=3; c7: no defects in setup
        # Total should be 8 (5+3 from c1)
        total_defects = sum(item["value"] for item in response.data)
        self.assertEqual(total_defects, 8)

    def test_total_defects_excluded_from_top_defects(self):
        """
        RED TEST: 'total_defects' must NOT appear in top-defects response
        even when defect records exist for that type.
        """
        # Create a ContainerDefectType for total_defects
        total_def_type = ContainerDefectType.objects.create(name="total_defects")
        # Add total_defects records to existing containers
        ContainerInspectionDefect.objects.create(
            container=self.c1, defect_type=total_def_type, amount=100,
        )
        ContainerInspectionDefect.objects.create(
            container=self.c2, defect_type=total_def_type, amount=200,
        )
        url = reverse("quality_data:kpi-container-top-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertNotIn("total_defects", labels,
                         "total_defects must be excluded from top-defects chart data")

    def test_total_defects_excluded_from_defect_composition(self):
        """
        RED TEST: 'total_defects' must NOT appear in defect-composition response
        even when defect records exist for that type.
        """
        total_def_type = ContainerDefectType.objects.create(name="total_defects")
        ContainerInspectionDefect.objects.create(
            container=self.c1, defect_type=total_def_type, amount=150,
        )
        url = reverse("quality_data:kpi-container-defect-composition")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        names = {item["name"] for item in response.data}
        self.assertNotIn("total_defects", names,
                         "total_defects must be excluded from defect-composition chart data")

    def test_total_defects_exclusion_does_not_remove_other_defects(self):
        """
        RED TEST: Excluding total_defects must preserve other valid defect types.
        """
        total_def_type = ContainerDefectType.objects.create(name="total_defects")
        ContainerInspectionDefect.objects.create(
            container=self.c1, defect_type=total_def_type, amount=999,
        )
        url = reverse("quality_data:kpi-container-top-defects")
        response = self.client.get(url)
        labels = {item["label"] for item in response.data}
        # Original defect types should still be present
        self.assertIn("Broken Seal", labels)
        self.assertIn("Dented Wall", labels)
        self.assertIn("Rust Spot", labels)


# ─────────────────────────────────────────────────────────
# Task 2.3 — Worst-container ordering and DTO shape
# ─────────────────────────────────────────────────────────


class WorstContainersOrderingTest(ContainerKpiTestMixin, TestCase):
    """Tests for worst-containers endpoint ordering and DTO shape."""

    def test_returns_200_with_expected_dto_shape(self):
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        if response.data:
            row = response.data[0]
            self.assertIn("containerNumber", row)
            self.assertIn("customer", row)
            self.assertIn("passRate", row)
            self.assertIn("rejectedPalettes", row)
            self.assertIn("inspectionDate", row)

    def test_ordering_lowest_pass_rate_first(self):
        """Worst containers ordered by percentage_pass ASC (worst first)."""
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(url)
        pass_rates = [item["passRate"] for item in response.data]
        self.assertEqual(pass_rates, sorted(pass_rates))

    def test_ordering_tiebreaker_by_container_number_asc(self):
        """When two containers have the same pass rate, use container_number ASC."""
        # Make c1 and c7 have the same pass rate
        c1_before = Container.objects.get(container_number=100)
        c1_before.percentage_pass = 80.0
        c1_before.save()
        # c7 already has 80.0%; c1 has container_number=100, c7 has 106
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(url)
        # Find items with passRate 80.0
        items_80 = [item for item in response.data if item["passRate"] == 80.0]
        self.assertEqual(len(items_80), 2)
        self.assertLess(items_80[0]["containerNumber"], items_80[1]["containerNumber"])

    def test_worst_containers_respects_filters(self):
        """Worst-containers endpoint should respect customer and date filters."""
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(f"{url}?customer=AlphaCorp")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        customers = {item["customer"] for item in response.data}
        self.assertEqual(customers, {"AlphaCorp"})

    def test_worst_containers_dto_field_types(self):
        """Verify field value types in worst-container rows."""
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(url)
        if response.data:
            row = response.data[0]
            self.assertIsInstance(row["containerNumber"], int)
            self.assertIsInstance(row["customer"], str)
            self.assertIsInstance(row["passRate"], (int, float))
            self.assertIsInstance(row["rejectedPalettes"], int)
            self.assertIsInstance(row["inspectionDate"], str)

    def test_null_date_renders_as_none_or_null(self):
        """Container with null date should include inspectionDate as None/null."""
        url = reverse("quality_data:kpi-container-worst-containers")
        # Use top=10 to ensure c4 (null date, high pass rate) is included in results
        response = self.client.get(f"{url}?top=10")
        c4_row = next(
            (item for item in response.data if item["containerNumber"] == 103), None
        )
        self.assertIsNotNone(c4_row)
        self.assertIsNone(c4_row["inspectionDate"])

    def test_default_top_5(self):
        """
        RED TEST: Without 'top' param, worst-containers returns at most 5 items.
        """
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(url)
        # 7 containers exist in fixtures, default top=5 should return 5
        self.assertLessEqual(len(response.data), 5)

    def test_explicit_top_returns_requested_count(self):
        """
        RED TEST: top=3 returns only 3 worst containers.
        """
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(f"{url}?top=3")
        self.assertEqual(len(response.data), 3)

    def test_explicit_top_preserves_ordering(self):
        """
        RED TEST: After top-N slicing, items remain ordered worst-first.
        """
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(f"{url}?top=3")
        pass_rates = [item["passRate"] for item in response.data]
        self.assertEqual(pass_rates, sorted(pass_rates))

    def test_invalid_top_falls_back_to_default(self):
        """
        RED TEST: Non-numeric 'top' value falls back to default limit of 5.
        """
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(f"{url}?top=abc")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 5)

    def test_negative_top_falls_back_to_default(self):
        """
        RED TEST: Negative 'top' value falls back to default limit of 5.
        """
        url = reverse("quality_data:kpi-container-worst-containers")
        response = self.client.get(f"{url}?top=-1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 5)
