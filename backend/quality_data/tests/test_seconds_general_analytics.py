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
        record_defs = [
            # (customer, style, week, sewing_type, sewing_amount, fabric_type, fabric_amount)
            ("CUST_ALPHA", "ST-100", 1, "picado_aguja", 10, "corrido_2", 20),
            ("CUST_ALPHA", "ST-100", 1, "manchas_sucio", 5, "barre", 15),
            ("CUST_BETA", "ST-200", 2, "grasa", 8, "desgarre_def_tela", 12),
            ("CUST_BETA", "ST-200", 2, "tono_tela", 3, "contamination", 7),
            ("CUST_BETA", "ST-300", 3, "fuera_medidas", 12, "linea_de_tela", 9),
            ("CUST_GAMMA", "ST-400", 4, "enganche", 6, "mill_flaw", 14),
            ("CUST_GAMMA", "ST-400", 4, "costura_torcida_insegura", 4, "hoyos", 18),
            ("CUST_GAMMA", "ST-400", 5, "hoyos_costura", 9, "manchas_tela", 11),
            ("CUST_ALPHA", "ST-300", 3, "heat_transfer", 7, "degradacion", 3),
            ("CUST_ALPHA", "ST-200", 2, "mal_corte", 11, "otros_3", 4),
        ]

        for cust, style, week, sew_type, sew_amt, fab_type, fab_amt in record_defs:
            sg = SecondsGeneral.objects.create(
                customer=cust,
                style=style,
                week=week,
                date=f"2025-01-{10 + week:02d}",
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
