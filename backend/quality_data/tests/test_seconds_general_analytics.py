"""
Tests for SecondsGeneral analytics endpoints (Phase 2 of refactor-multisheet-dashboard).

Verifies the 4 new analytics endpoints that use Django ORM aggregation on SecondsGeneral
and SecondsGeneralDefect data:

  - Defects by Customer: Group by SecondsGeneral.customer, SUM(SecondsGeneralDefect.amount)
  - Defects by Style: Group by SecondsGeneral.style, SUM(SecondsGeneralDefect.amount)
  - Weekly Trend: Group by SecondsGeneral.week, SUM(SecondsGeneralDefect.amount)
  - Sewing vs Fabric Mix: Split defects into sewing and fabric families using configured
    defect-type classifications (SECONDS_GENERAL_SEWING_DEFECTS / SECONDS_GENERAL_FABRIC_DEFECTS)

Each endpoint operates exclusively on SecondsGeneral sources (spec domain: seconds-general-analytics).
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status
from quality_data.models import (
    SecondsGeneral,
    SecondsGeneralDefectType,
    SecondsGeneralDefect,
)


class SecondsGeneralAnalyticsMixin:
    """
    Mixin that creates SecondsGeneral records with varied data
    across customer, style, week, and defect types (sewing + fabric families).
    Includes produced/fixed/definitive values for production-totals and fix-vs-definitive tests.
    """

    def setUp(self):
        self.client = APIClient()

        # ── Create defect types: sewing family (13 types) + fabric family (10 types) ──
        sewing_names = [
            "picado_aguja", "manchas_sucio", "grasa", "tono_tela", "fuera_medidas",
            "enganche", "costura_torcida_insegura", "hoyos_costura", "heat_transfer",
            "mal_corte", "trapo", "corrido", "otros",
        ]
        fabric_names = [
            "desgarre_def_tela", "contamination", "linea_de_tela", "mill_flaw",
            "hoyos", "manchas_tela",
            "corrido_2", "barre", "otros_3", "degradacion", "bordados",
        ]

        self.sewing_types = {}
        self.fabric_types = {}
        for name in sewing_names:
            self.sewing_types[name], _ = SecondsGeneralDefectType.objects.get_or_create(name=name)
        for name in fabric_names:
            self.fabric_types[name], _ = SecondsGeneralDefectType.objects.get_or_create(name=name)

        # ── Create SecondsGeneral records spread across 3 customers, 4 styles, 5 weeks ──
        self.customers = ["CUST_ALPHA", "CUST_BETA", "CUST_GAMMA"]
        self.styles = ["ST-100", "ST-200", "ST-300", "ST-400"]
        self.weeks = [1, 2, 3, 4, 5]

        # Record factory: creates parent + 3 defect rows (2 sewing + 1 fabric)
        # Each record also has produced/fixed/definitive with predictable values for aggregation tests.
        # Extended for V2: includes color, size, team for new endpoint tests.
        record_defs = [
            # (customer, style, week, produced, fixed, definitive, sewing_type, sewing_amount, fabric_type, fabric_amount, color, size, team)
            ("CUST_ALPHA", "ST-100", 1, 110, 55, 33, "picado_aguja", 10, "corrido_2", 20, "Red", "M", 1),
            ("CUST_ALPHA", "ST-100", 1, 120, 60, 36, "manchas_sucio", 5, "barre", 15, "Blue", "S", 1),
            ("CUST_BETA", "ST-200", 2, 130, 65, 39, "grasa", 8, "desgarre_def_tela", 12, "Red", "L", 2),
            ("CUST_BETA", "ST-200", 2, 140, 70, 42, "tono_tela", 3, "contamination", 7, "White", "M", 2),
            ("CUST_BETA", "ST-300", 3, 150, 75, 45, "fuera_medidas", 12, "linea_de_tela", 9, "Blue", "XL", 3),
            ("CUST_GAMMA", "ST-400", 4, 160, 80, 48, "enganche", 6, "mill_flaw", 14, "Red", "S", 4),
            ("CUST_GAMMA", "ST-400", 4, 170, 85, 51, "costura_torcida_insegura", 4, "hoyos", 18, "White", "M", 4),
            ("CUST_GAMMA", "ST-400", 5, 180, 90, 54, "hoyos_costura", 9, "manchas_tela", 11, "Red", "L", 5),
            ("CUST_ALPHA", "ST-300", 3, 190, 95, 57, "heat_transfer", 7, "degradacion", 3, "Blue", "XL", 3),
            ("CUST_ALPHA", "ST-200", 2, 200, 100, 60, "mal_corte", 11, "otros_3", 4, "Red", "M", 2),
        ]

        # Track expected totals for assertions
        self.expected_production_totals = {"total_produced": 0, "total_fixed": 0, "total_definitive": 0}
        # Track expected weekly fix vs definitive
        self.expected_weekly_fix_def = {}

        # Track expected color aggregations for new endpoint tests
        self.expected_color_totals = {}
        # Track expected size aggregations for new endpoint tests
        self.expected_size_totals = {}
        # Track expected team aggregations for line endpoint tests
        self.expected_team_totals = {}
        # Track expected line-code aggregations for line endpoint tests (dual lines)
        self.expected_line_code_totals = {}

        for cust, style, week, produced, fixed, definitive, sew_type, sew_amt, fab_type, fab_amt, color, size, team in record_defs:
            self.expected_production_totals["total_produced"] += produced
            self.expected_production_totals["total_fixed"] += fixed
            self.expected_production_totals["total_definitive"] += definitive

            if week not in self.expected_weekly_fix_def:
                self.expected_weekly_fix_def[week] = {"fixed": 0, "definitive": 0}
            self.expected_weekly_fix_def[week]["fixed"] += fixed
            self.expected_weekly_fix_def[week]["definitive"] += definitive

            # Track color aggregates (defect amounts)
            self.expected_color_totals[color] = self.expected_color_totals.get(color, 0) + sew_amt + fab_amt
            # Track size aggregates
            self.expected_size_totals[size] = self.expected_size_totals.get(size, 0) + sew_amt + fab_amt
            # Track team aggregates
            team_key = f"Team {team}"
            self.expected_team_totals[team_key] = self.expected_team_totals.get(team_key, 0) + sew_amt + fab_amt

            sg = SecondsGeneral.objects.create(
                customer=cust,
                style=style,
                week=week,
                date=f"2025-01-{10 + week:02d}",
                produced=produced,
                fixed=fixed,
                definitive=definitive,
                color=color,
                size=size,
                team=team,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.sewing_types[sew_type],
                amount=sew_amt,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.fabric_types[fab_type],
                amount=fab_amt,
            )


# ─────────────────────────────────────────────────────────
# 2.1 – Defects by Customer
# ─────────────────────────────────────────────────────────

class DefectsByCustomerTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/defects-by-customer/"""

    def test_returns_200_with_customer_groups(self):
        """Returns 200 with defect totals grouped by customer, sorted descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # 3 customers should appear
        customers_found = {item["label"] for item in response.data}
        self.assertEqual(customers_found, set(self.customers))

        # Each item must have label and value
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url)

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no SecondsGeneral records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


# ─────────────────────────────────────────────────────────
# 2.2 – Defects by Style
# ─────────────────────────────────────────────────────────

class DefectsByStyleTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/defects-by-style/"""

    def test_returns_200_with_style_groups(self):
        """Returns 200 with defect totals grouped by style."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-style")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        styles_found = {item["label"] for item in response.data}
        self.assertEqual(styles_found, set(self.styles))

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-style")
        response = self.client.get(url)

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-defects-by-style")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


# ─────────────────────────────────────────────────────────
# 2.3 – Weekly Trend
# ─────────────────────────────────────────────────────────

class WeeklyTrendTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/weekly-trend/"""

    def test_returns_200_with_weekly_series(self):
        """Returns 200 with weekly aggregated defect totals."""
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # Should return a single series: {name: "Defects", data: [...]}
        self.assertGreaterEqual(len(response.data), 1)
        series = response.data[0]
        self.assertEqual(series["name"], "Defects")
        self.assertIsInstance(series["data"], list)

        # Data points should have x (week) and y (total)
        for point in series["data"]:
            self.assertIn("x", point)
            self.assertIn("y", point)
            self.assertIsInstance(point["x"], int)
            self.assertIsInstance(point["y"], (int, float))

    def test_weekly_data_sorted_by_week_ascending(self):
        """Weekly trend data points are ordered by week ascending."""
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        response = self.client.get(url)

        series = response.data[0]
        weeks = [point["x"] for point in series["data"]]
        self.assertEqual(weeks, sorted(weeks))

    def test_week_filter_filters_by_exact_week(self):
        """Supports ?week=N query parameter."""
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        response = self.client.get(url, {"week": 1})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series = response.data[0]["data"]
        # Only week 1 data should be returned
        for point in series:
            self.assertEqual(point["x"], 1)

    def test_week_filter_invalid_value_returns_400(self):
        """Invalid week parameter returns 400."""
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        response = self.client.get(url, {"week": "not-a-number"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_date_range_filter_filters_by_date_bounds(self):
        """Supports ?date_range=YYYY-MM-DD,YYYY-MM-DD."""
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        # Only include records from week 2 onward (date>=2025-01-12)
        response = self.client.get(url, {"date_range": "2025-01-12,2025-01-15"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        if response.data and response.data[0]["data"]:
            weeks_in_response = {point["x"] for point in response.data[0]["data"]}
            # Week 1 (date=2025-01-11) should be excluded
            self.assertNotIn(1, weeks_in_response)

    def test_empty_dataset_returns_valid_empty_result(self):
        """Returns 200 with empty but valid result when no data exists."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-weekly-trend")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series = response.data[0]
        self.assertEqual(series["name"], "Defects")
        self.assertEqual(series["data"], [])


# ─────────────────────────────────────────────────────────
# 2.4 – Sewing vs Fabric Mix
# ─────────────────────────────────────────────────────────

class SewingVsFabricTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/sewing-vs-fabric/"""

    def test_returns_200_with_sewing_and_fabric_totals(self):
        """Returns 200 with both Sewing and Fabric totals."""
        url = reverse("quality_data:seconds-general-analytics-sewing-vs-fabric")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"Sewing", "Fabric"})

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertGreater(item["value"], 0,
                               msg=f"{item['label']} should have positive total with test data")

    def test_sewing_fabric_totals_match_expected_sums(self):
        """Sewing and Fabric values match the sum of respective defect amounts."""
        url = reverse("quality_data:seconds-general-analytics-sewing-vs-fabric")
        response = self.client.get(url)

        result = {item["label"]: item["value"] for item in response.data}

        # Compute expected totals from test data
        from django.db.models import Sum
        from excel_importer.sheet_configs import (
            SECONDS_GENERAL_SEWING_DEFECTS,
            SECONDS_GENERAL_FABRIC_DEFECTS,
        )

        sewing_total = (
            SecondsGeneralDefect.objects
            .filter(defect_type__name__in=SECONDS_GENERAL_SEWING_DEFECTS)
            .aggregate(total=Sum("amount"))["total"]
        )
        fabric_total = (
            SecondsGeneralDefect.objects
            .filter(defect_type__name__in=SECONDS_GENERAL_FABRIC_DEFECTS)
            .aggregate(total=Sum("amount"))["total"]
        )

        self.assertEqual(result["Sewing"], sewing_total)
        self.assertEqual(result["Fabric"], fabric_total)

    def test_empty_dataset_returns_zero_totals(self):
        """Returns 0 for both families when no SecondsGeneral records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-sewing-vs-fabric")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        result = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(result["Sewing"], 0)
        self.assertEqual(result["Fabric"], 0)

    def test_only_sewing_defects_returns_fabric_zero(self):
        """When only sewing defects exist, fabric returns 0."""
        # Delete all fabric-related defects
        from excel_importer.sheet_configs import SECONDS_GENERAL_FABRIC_DEFECTS
        SecondsGeneralDefect.objects.filter(
            defect_type__name__in=SECONDS_GENERAL_FABRIC_DEFECTS
        ).delete()

        url = reverse("quality_data:seconds-general-analytics-sewing-vs-fabric")
        response = self.client.get(url)

        result = {item["label"]: item["value"] for item in response.data}
        self.assertGreater(result["Sewing"], 0)
        self.assertEqual(result["Fabric"], 0)

    def test_only_fabric_defects_returns_sewing_zero(self):
        """When only fabric defects exist, sewing returns 0."""
        from excel_importer.sheet_configs import SECONDS_GENERAL_SEWING_DEFECTS
        SecondsGeneralDefect.objects.filter(
            defect_type__name__in=SECONDS_GENERAL_SEWING_DEFECTS
        ).delete()

        url = reverse("quality_data:seconds-general-analytics-sewing-vs-fabric")
        response = self.client.get(url)

        result = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(result["Sewing"], 0)
        self.assertGreater(result["Fabric"], 0)


# ─────────────────────────────────────────────────────────
# 2.5 – Production Totals
# ─────────────────────────────────────────────────────────

class ProductionTotalsTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/production-totals/"""

    def test_returns_200_with_production_totals(self):
        """Returns 200 with total_produced, total_fixed, total_definitive."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("total_produced", response.data)
        self.assertIn("total_fixed", response.data)
        self.assertIn("total_definitive", response.data)

    def test_totals_match_expected_sums(self):
        """Aggregated totals match expected sums from test data."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(
            response.data["total_produced"],
            self.expected_production_totals["total_produced"],
        )
        self.assertEqual(
            response.data["total_fixed"],
            self.expected_production_totals["total_fixed"],
        )
        self.assertEqual(
            response.data["total_definitive"],
            self.expected_production_totals["total_definitive"],
        )

    def test_all_totals_are_positive_with_test_data(self):
        """All three totals are greater than zero with seeded data."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url)

        self.assertGreater(response.data["total_produced"], 0)
        self.assertGreater(response.data["total_fixed"], 0)
        self.assertGreater(response.data["total_definitive"], 0)

    def test_empty_dataset_returns_zero_totals(self):
        """Returns zero for all totals when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["total_produced"], 0)
        self.assertEqual(response.data["total_fixed"], 0)
        self.assertEqual(response.data["total_definitive"], 0)


# ─────────────────────────────────────────────────────────
# 2.6 – Top Defects (Sewing & Fabric)
# ─────────────────────────────────────────────────────────

class TopSewingDefectsTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/top-defects/?type=sewing"""

    def test_returns_200_with_sewing_defect_totals(self):
        """Returns 200 with top sewing defect totals grouped by defect_type name."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "sewing"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "sewing"})

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_only_includes_sewing_defects(self):
        """Only sewing-family defects appear in results."""
        from excel_importer.sheet_configs import SECONDS_GENERAL_SEWING_DEFECTS

        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "sewing"})

        for item in response.data:
            self.assertIn(
                item["label"],
                SECONDS_GENERAL_SEWING_DEFECTS,
                f"{item['label']} is not a sewing defect",
            )

    def test_limited_to_top_10(self):
        """Returns at most 10 results."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "sewing"})

        self.assertLessEqual(len(response.data), 10)

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "sewing"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class TopFabricDefectsTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/top-defects/?type=fabric"""

    def test_returns_200_with_fabric_defect_totals(self):
        """Returns 200 with top fabric defect totals grouped by defect_type name."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "fabric"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "fabric"})

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_only_includes_fabric_defects(self):
        """Only fabric-family defects appear in results."""
        from excel_importer.sheet_configs import SECONDS_GENERAL_FABRIC_DEFECTS

        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "fabric"})

        for item in response.data:
            self.assertIn(
                item["label"],
                SECONDS_GENERAL_FABRIC_DEFECTS,
                f"{item['label']} is not a fabric defect",
            )

    def test_limited_to_top_10(self):
        """Returns at most 10 results."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "fabric"})

        self.assertLessEqual(len(response.data), 10)

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "fabric"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_missing_type_param_returns_400(self):
        """Returns 400 when type query parameter is missing."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_invalid_type_param_returns_400(self):
        """Returns 400 when type query parameter is invalid."""
        url = reverse("quality_data:seconds-general-analytics-top-defects")
        response = self.client.get(url, {"type": "invalid_type"})

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────
# 2.7 – Fix vs Definitive
# ─────────────────────────────────────────────────────────

class FixVsDefinitiveTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/fix-vs-definitive/"""

    def test_returns_200_with_two_series(self):
        """Returns 200 with 'Fixed' and 'Definitive' time series."""
        url = reverse("quality_data:seconds-general-analytics-fix-vs-definitive")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)

        series_names = {s["name"] for s in response.data}
        self.assertEqual(series_names, {"Fixed", "Definitive"})

    def test_series_have_weekly_data_points(self):
        """Each series contains data points with x (week) and y (value)."""
        url = reverse("quality_data:seconds-general-analytics-fix-vs-definitive")
        response = self.client.get(url)

        for series in response.data:
            self.assertIn("name", series)
            self.assertIn("data", series)
            self.assertIsInstance(series["data"], list)
            for point in series["data"]:
                self.assertIn("x", point)
                self.assertIn("y", point)
                self.assertIsInstance(point["x"], int)
                self.assertIsInstance(point["y"], (int, float))

    def test_weekly_totals_match_expected_data(self):
        """Weekly Fixed and Definitive values match expected sums from test data."""
        url = reverse("quality_data:seconds-general-analytics-fix-vs-definitive")
        response = self.client.get(url)

        result = {}
        for series in response.data:
            for point in series["data"]:
                week = point["x"]
                if week not in result:
                    result[week] = {}
                result[week][series["name"]] = point["y"]

        for week, expected in self.expected_weekly_fix_def.items():
            self.assertIn(week, result, f"Week {week} should be in results")
            self.assertEqual(
                result[week]["Fixed"],
                expected["fixed"],
                f"Week {week} Fixed total mismatch",
            )
            self.assertEqual(
                result[week]["Definitive"],
                expected["definitive"],
                f"Week {week} Definitive total mismatch",
            )

    def test_data_sorted_by_week_ascending(self):
        """Data points in each series are sorted by week ascending."""
        url = reverse("quality_data:seconds-general-analytics-fix-vs-definitive")
        response = self.client.get(url)

        for series in response.data:
            weeks = [point["x"] for point in series["data"]]
            self.assertEqual(weeks, sorted(weeks))

    def test_empty_dataset_returns_valid_empty_result(self):
        """Returns valid empty series when no data exists."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-fix-vs-definitive")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series_map = {s["name"]: s for s in response.data}
        self.assertIn("Fixed", series_map)
        self.assertIn("Definitive", series_map)
        self.assertEqual(series_map["Fixed"]["data"], [])
        self.assertEqual(series_map["Definitive"]["data"], [])


# ─────────────────────────────────────────────────────────
# V2 – Filter Tests
# ─────────────────────────────────────────────────────────

class SecondsGeneralFilterTestMixin(SecondsGeneralAnalyticsMixin):
    """
    Extends the base mixin with records that have line_code values
    for dual-line filter tests. Adds 4 dual-line records + 2 extra
    single-line records for robust filter testing.
    """

    def setUp(self):
        super().setUp()

        # ── Dual-line records (non-null line_code) ──
        dual_defs = [
            ("CUST_LINE_A", "ST-LINE-1", 10, "picado_aguja", 5, "contamination", 3, "Red", "M", 10, "L1"),
            ("CUST_LINE_B", "ST-LINE-2", 11, "grasa", 7, "linea_de_tela", 2, "Blue", "L", 11, "L2"),
            ("CUST_LINE_A", "ST-LINE-3", 12, "tono_tela", 4, "hoyos", 6, "White", "S", 12, "L3"),
            ("CUST_LINE_C", "ST-LINE-4", 13, "picado_aguja", 8, "corrido_2", 1, "Red", "XL", 13, "L4"),
        ]
        for cust, style, week, sew_type, sew_amt, fab_type, fab_amt, color, size, team, line_code in dual_defs:
            sg = SecondsGeneral.objects.create(
                customer=cust, style=style, week=week,
                date=f"2025-02-{10 + week:02d}",
                produced=100, fixed=50, definitive=25,
                color=color, size=size, team=team, line_code=line_code,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.sewing_types[sew_type],
                amount=sew_amt,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.fabric_types[fab_type],
                amount=fab_amt,
            )
            # Track expected totals for these dual-line records
            color_total = sew_amt + fab_amt
            self.expected_color_totals[color] = self.expected_color_totals.get(color, 0) + color_total
            size_total = sew_amt + fab_amt
            self.expected_size_totals[size] = self.expected_size_totals.get(size, 0) + size_total

        # ── Extra single-line records (null line_code) for team filter tests ──
        extra_defs = [
            ("CUST_EXTRA", "ST-EXTRA", 20, 200, 100, 50, "picado_aguja", 10, "corrido_2", 5, "Green", "M", 20),
            ("CUST_EXTRA", "ST-EXTRA", 21, 300, 150, 75, "grasa", 8, "barre", 3, "Yellow", "L", 21),
        ]
        for cust, style, week, produced, fixed, definitive, sew_type, sew_amt, fab_type, fab_amt, color, size, team in extra_defs:
            sg = SecondsGeneral.objects.create(
                customer=cust, style=style, week=week,
                date=f"2025-03-{10 + week:02d}",
                produced=produced, fixed=fixed, definitive=definitive,
                color=color, size=size, team=team,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.sewing_types[sew_type],
                amount=sew_amt,
            )
            SecondsGeneralDefect.objects.create(
                seconds_general=sg,
                defect_type=self.fabric_types[fab_type],
                amount=fab_amt,
            )
            self.expected_color_totals[color] = self.expected_color_totals.get(color, 0) + sew_amt + fab_amt
            self.expected_size_totals[size] = self.expected_size_totals.get(size, 0) + sew_amt + fab_amt


class SecondsGeneralFilterTest(SecondsGeneralFilterTestMixin, TestCase):
    """Tests for global filters via SecondsGeneralFilterMixin across all endpoints."""

    # ── date_range filter ──

    def test_date_range_filter_on_production_totals(self):
        """?date_range limits SecondsGeneral records used in aggregation."""
        # Production totals with no filter = sum of all 10 base records
        # With date_range covering only week 3-5, only those records' data is included
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"date_range": "2025-01-13,2025-01-15"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Weeks 3-5: produced=150+160+170+180+190=850, fixed=75+80+85+90+95=425, definitive=45+48+51+54+57=255
        self.assertEqual(response.data["total_produced"], 850)
        self.assertEqual(response.data["total_fixed"], 425)
        self.assertEqual(response.data["total_definitive"], 255)

    def test_date_range_excludes_weeks_outside_bounds(self):
        """Records outside date range are excluded."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"date_range": "2025-01-12,2025-01-15"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Week 1 has date 2025-01-11 → excluded. CUST_GAMMA only has week 4-5 → still included.
        # But totals are lower. Let's check: CUST_ALPHA appears in weeks 1,2,3.
        # Week 1 excluded means CUST_ALPHA total drops.
        cust_totals = {item["label"]: item["value"] for item in response.data}
        # Pre-filter: CUST_ALPHA total = (10+20)+(5+15)+(7+3)+(11+4) = 75 (weeks 1,2,3)
        # After filter (week 1 excluded): CUST_ALPHA = (7+3)+(11+4) = 25 (weeks 2,3 only)
        self.assertEqual(cust_totals["CUST_ALPHA"], 25)

    def test_date_range_invalid_format_returns_400(self):
        """Malformed date_range returns 400."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"date_range": "invalid"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    # ── week filter ──

    def test_week_filter_on_production_totals(self):
        """?week=N filters SecondsGeneral records by exact week."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"week": 2})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Week 2: produced=130+140+200=470, fixed=65+70+100=235, definitive=39+42+60=141
        self.assertEqual(response.data["total_produced"], 470)
        self.assertEqual(response.data["total_fixed"], 235)
        self.assertEqual(response.data["total_definitive"], 141)

    def test_week_filter_invalid_value_returns_400(self):
        """Invalid week param returns 400."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"week": "not-a-number"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    # ── customer filter ──

    def test_customer_filter_on_defects_by_customer(self):
        """?customer filters by customer exact match."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"customer": "CUST_ALPHA"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should only return CUST_ALPHA
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"CUST_ALPHA"})

    # ── style filter ──

    def test_style_filter_on_defects_by_customer(self):
        """?style filters SecondsGeneral by style, affecting defect aggregations."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"style": "ST-100"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # ST-100 has CUST_ALPHA records only
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"CUST_ALPHA"})

    # ── color filter ──

    def test_color_filter_on_defects_by_customer(self):
        """?color filters SecondsGeneral by color."""
        # 3 records have Blue: records 1, 4, 8 → customers CUST_ALPHA and CUST_BETA
        # Also CUST_LINE_B (dual-line) has Blue — requires include_dual_lines=true
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"color": "Blue", "include_dual_lines": "true"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"CUST_ALPHA", "CUST_BETA", "CUST_LINE_B"})

    # ── size filter ──

    def test_size_filter_on_defects_by_customer(self):
        """?size filters SecondsGeneral by size."""
        # XL records: index 4 (CUST_BETA, ST-300, week3), index 8 (CUST_ALPHA, ST-300, week3),
        # and dual-line CUST_LINE_C (ST-LINE-4, week 13) — requires include_dual_lines=true
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"size": "XL", "include_dual_lines": "true"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"CUST_BETA", "CUST_ALPHA", "CUST_LINE_C"})

    # ── team filter ──

    def test_team_filter_on_production_totals(self):
        """?team filters SecondsGeneral by team."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"team": 2})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Team 2: records 2 (cust=BETA), 3 (cust=BETA), 9 (cust=ALPHA)
        # produced=130+140+200=470, fixed=65+70+100=235, definitive=39+42+60=141
        self.assertEqual(response.data["total_produced"], 470)
        self.assertEqual(response.data["total_fixed"], 235)
        self.assertEqual(response.data["total_definitive"], 141)

    def test_team_filter_invalid_value_returns_400(self):
        """Invalid team param returns 400."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"team": "not-a-number"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    # ── line_code filter ──

    def test_line_code_filter_on_production_totals(self):
        """?line_code filters by exact line_code match."""
        # The dual-line records have line_code L1-L4. No base records have line_code.
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"line_code": "L1"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # L1 record: produced=100, fixed=50, definitive=25
        self.assertEqual(response.data["total_produced"], 100)
        self.assertEqual(response.data["total_fixed"], 50)
        self.assertEqual(response.data["total_definitive"], 25)

    # ── include_dual_lines toggle ──

    def test_include_dual_lines_false_excludes_dual_records(self):
        """"?include_dual_lines=false" excludes records with non-null line_code."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"include_dual_lines": "false"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only base records + extra single-line records should be counted
        # Base total: 1550 produced, 775 fixed, 465 definitive
        # Extra: 200+300=500 produced, 100+150=250 fixed, 50+75=125 definitive
        # Total: 2050 produced, 1025 fixed, 590 definitive
        self.assertEqual(response.data["total_produced"], 2050)
        self.assertEqual(response.data["total_fixed"], 1025)
        self.assertEqual(response.data["total_definitive"], 590)

    def test_include_dual_lines_true_includes_dual_records(self):
        """?include_dual_lines=true includes records with non-null line_code."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"include_dual_lines": "true"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # All records: base (1550) + extra (500) + dual (4*100=400) = 2450
        self.assertEqual(response.data["total_produced"], 2450)

    def test_include_dual_lines_false_with_explicit_line_code_includes_dual(self):
        """When explicit line_code is given, include_dual_lines is ignored and dual is included."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url, {"line_code": "L1"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # L1 record has produced=100
        self.assertEqual(response.data["total_produced"], 100)

    def test_default_excludes_dual_lines(self):
        """Default (no include_dual_lines param) excludes dual-line records
        — changing from old implicit-include to implicit-exclude."""
        url = reverse("quality_data:seconds-general-analytics-production-totals")
        response = self.client.get(url)  # no dual-line param
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Base (1550) + extra (500) = 2050; 4 dual records (400) excluded
        self.assertEqual(response.data["total_produced"], 2050)

    # ── Combined filters ──

    def test_combined_customer_and_week_filter(self):
        """Multiple filters combine with AND logic."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-customer")
        response = self.client.get(url, {"customer": "CUST_BETA", "week": 2})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # CUST_BETA, week 2: records 2 and 3 → total = (8+12)+(3+7) = 30
        cust_totals = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(cust_totals["CUST_BETA"], 30)


# ─────────────────────────────────────────────────────────
# V2 – New Endpoints
# ─────────────────────────────────────────────────────────

class DefectsByColorTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/defects-by-color/"""

    def test_returns_200_with_color_groups(self):
        """Returns 200 with defect totals grouped by color, sorted descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-color")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_color_totals_match_expected_values(self):
        """Color totals match expected sums from test data."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-color")
        response = self.client.get(url)

        result = {item["label"]: item["value"] for item in response.data}
        for color, expected_total in self.expected_color_totals.items():
            self.assertIn(color, result, f"Color '{color}' should be in results")
            self.assertEqual(result[color], expected_total, f"Color '{color}' total mismatch")

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-color")
        response = self.client.get(url)

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no SecondsGeneral records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-defects-by-color")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class DefectsBySizeTest(SecondsGeneralAnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/defects-by-size/"""

    def test_returns_200_with_size_groups(self):
        """Returns 200 with defect totals grouped by size."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-size")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_size_totals_match_expected_values(self):
        """Size totals match expected sums from test data."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-size")
        response = self.client.get(url)

        result = {item["label"]: item["value"] for item in response.data}
        for size, expected_total in self.expected_size_totals.items():
            self.assertIn(size, result, f"Size '{size}' should be in results")
            self.assertEqual(result[size], expected_total, f"Size '{size}' total mismatch")

    def test_sorted_descending_by_value(self):
        """Response is sorted by total defects descending."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-size")
        response = self.client.get(url)

        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-defects-by-size")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class DefectsByLineTest(SecondsGeneralFilterTestMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/defects-by-line/"""

    def test_returns_200_with_line_groups(self):
        """Returns 200 with defect totals grouped by team (and line_code if present)."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["label"], str)
            self.assertIsInstance(item["value"], (int, float))

    def test_line_totals_include_team_aggregates(self):
        """Each team appears with its aggregated defect total."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url)

        # Base data has teams 1-5. Filter mixin excludes dual records (include_dual_lines=false).
        # Extra records have teams 20, 21.
        result = {item["label"]: item["value"] for item in response.data}
        for team_label, expected_total in self.expected_team_totals.items():
            line_label = team_label.replace("Team ", "Line ")
            self.assertIn(line_label, result, f"Line '{line_label}' should be in results")
            self.assertEqual(result[line_label], expected_total, f"Line '{line_label}' total mismatch")

    def test_line_labels_are_sorted_naturally_when_dual_lines_are_enabled(self):
        """Mixed simple and dual lines should keep a stable natural line order."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url, {"include_dual_lines": "true"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data]
        self.assertLess(labels.index("Line 1"), labels.index("Line 2"))
        self.assertLess(labels.index("Line 2"), labels.index("L3"))
        self.assertLess(labels.index("L3"), labels.index("L4"))

    def test_include_dual_lines_true_shows_line_code_labels(self):
        """With include_dual_lines=true, line_code entries appear alongside team entries."""
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url, {"include_dual_lines": "true"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Dual-line records have line_codes L1-L4
        line_labels = {item["label"] for item in response.data}
        self.assertIn("L1", line_labels)
        self.assertIn("L2", line_labels)
        self.assertIn("L3", line_labels)
        self.assertIn("L4", line_labels)

    def test_empty_dataset_returns_empty_list(self):
        """Returns 200 with empty list when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_no_nan_labels_when_line_code_is_none(self):
        """When line_code is None, label falls back to 'Line {N}' — never 'nan' or 'None'."""
        # Create a record with line_code=None (a normal single-line record)
        sg = SecondsGeneral.objects.create(
            customer="NAN_TEST", style="ST-NAN", week=30,
            date="2025-06-01", produced=100, fixed=50, definitive=25,
            color="Red", size="M", team=99, line_code=None,
        )
        SecondsGeneralDefect.objects.create(
            seconds_general=sg,
            defect_type=self.sewing_types["picado_aguja"],
            amount=10,
        )
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            label = item["label"].lower()
            self.assertNotIn("nan", label, f"Label '{item['label']}' leaks NaN")
            self.assertNotIn("none", label, f"Label '{item['label']}' leaks None")
        # The new record's label should be "Line 99"
        result = {item["label"]: item["value"] for item in response.data}
        self.assertIn("Line 99", result)

    def test_unknown_label_when_team_and_line_code_missing(self):
        """Records with both team=None and line_code=None collapse to 'Unknown'."""
        sg = SecondsGeneral.objects.create(
            customer="UNKNOWN_TEST", style="ST-UNK", week=31,
            date="2025-06-02", produced=50, fixed=25, definitive=10,
            color="Blue", size="S", team=None, line_code=None,
        )
        SecondsGeneralDefect.objects.create(
            seconds_general=sg,
            defect_type=self.sewing_types["grasa"],
            amount=15,
        )
        url = reverse("quality_data:seconds-general-analytics-defects-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        result = {item["label"]: item["value"] for item in response.data}
        self.assertIn("Unknown", result)


# ─────────────────────────────────────────────────────────
# V2 – FilterOptions for SecondsGeneral
# ─────────────────────────────────────────────────────────

class SecondsGeneralFilterOptionsTest(SecondsGeneralFilterTestMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-general/filter-options/"""

    def test_returns_200_with_filter_options(self):
        """Returns 200 with distinct filter option arrays."""
        url = reverse("quality_data:seconds-general-analytics-filter-options")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("customer", response.data)
        self.assertIn("style", response.data)
        self.assertIn("color", response.data)
        self.assertIn("size", response.data)
        self.assertIn("team", response.data)
        self.assertIn("week", response.data)
        self.assertIn("line_code", response.data)
        self.assertIn("include_dual_lines_default", response.data)

    def test_filter_options_contain_expected_unique_values(self):
        """Each field contains distinct values from SecondsGeneral records."""
        url = reverse("quality_data:seconds-general-analytics-filter-options")
        response = self.client.get(url)

        # Base data: customers = CUST_ALPHA, CUST_BETA, CUST_GAMMA
        self.assertIn("CUST_ALPHA", response.data["customer"])
        self.assertIn("CUST_BETA", response.data["customer"])
        self.assertIn("CUST_GAMMA", response.data["customer"])

        # Base data: styles = ST-100, ST-200, ST-300, ST-400
        self.assertIn("ST-100", response.data["style"])
        self.assertIn("ST-200", response.data["style"])
        self.assertIn("ST-300", response.data["style"])
        self.assertIn("ST-400", response.data["style"])

        # Colors: Red, Blue, White, Green, Yellow
        self.assertIn("Red", response.data["color"])
        self.assertIn("Blue", response.data["color"])
        self.assertIn("White", response.data["color"])

        # Sizes: M, S, L, XL
        self.assertIn("M", response.data["size"])
        self.assertIn("S", response.data["size"])
        self.assertIn("L", response.data["size"])
        self.assertIn("XL", response.data["size"])

        # Teams: 1-5, 10-13, 20-21
        self.assertIn(1, response.data["team"])
        self.assertIn(2, response.data["team"])
        self.assertIn(20, response.data["team"])

        # Line codes (only non-null): L1-L4
        self.assertIn("L1", response.data["line_code"])
        self.assertIn("L2", response.data["line_code"])

    def test_include_dual_lines_default_true_when_line_codes_exist(self):
        """include_dual_lines_default is True when line_code records exist."""
        url = reverse("quality_data:seconds-general-analytics-filter-options")
        response = self.client.get(url)

        self.assertTrue(response.data["include_dual_lines_default"])

    def test_all_values_are_unique(self):
        """Each array contains no duplicates."""
        url = reverse("quality_data:seconds-general-analytics-filter-options")
        response = self.client.get(url)

        for field in ("customer", "style", "color", "size", "team", "week", "line_code"):
            values = response.data[field]
            self.assertEqual(len(values), len(set(values)),
                             f"Field '{field}' contains duplicate values")

    def test_empty_dataset_returns_empty_lists(self):
        """Returns empty arrays when no records exist."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:seconds-general-analytics-filter-options")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for field in ("customer", "style", "color", "size", "team", "week", "line_code"):
            self.assertEqual(response.data[field], [],
                             f"Field '{field}' should be empty")
