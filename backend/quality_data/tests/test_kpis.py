"""
Tests for KPI endpoints (14 total).

Covers:
  Grupo 1 - AQL KPIs (AqlKpiViewSet):
    - GET /quality/kpis/aql-by-style/
    - GET /quality/kpis/aql-weekly/
    - GET /quality/kpis/audited-pieces/

  Grupo 2 - Rendimiento KPIs (KpiViewSet):
    - GET /quality/kpis/ac-re-rate-by-line/
    - GET /quality/kpis/seconds-rework/
    - GET /quality/kpis/performance-by-customer/
    - GET /quality/kpis/performance-by-line/

  Grupo 3 - Defectos KPIs:
    - GET /quality/kpis/top-defects/
    - GET /quality/kpis/fabric-defects/
    - GET /quality/kpis/defects-by-style-type/

  Grupo 4 - Operativos KPIs:
    - GET /quality/kpis/pass-reject-distribution/
    - GET /quality/kpis/rejected-evolution/
    - GET /quality/kpis/containers-by-state/
    - GET /quality/kpis/defect-rate/
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status
from django.db.models import Sum
from quality_data.models import (
    QualityQcFa,
    SecondsA4,
    SecondsGeneral,
    Container,
    Color,
    DefectType,
    InspectionDefect,
)


class KpiTestMixin:
    """Mixin that provides common setup for KPI tests."""

    def setUp(self):
        self.client = APIClient()
        # Create shared test fixtures
        self.color = Color.objects.create(name="red", is_active=True)
        self.defect_type = DefectType.objects.create(name="loose thread", is_active=True)
        self.defect_type_2 = DefectType.objects.create(name="stain", is_active=True)
        self.defect_type_3 = DefectType.objects.create(name="tear", is_active=True)

        # QualityQcFa records
        for i in range(5):
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1=f"2025-01-{i + 10:02d}",
                week=i + 1,
                customer="TestCustomer",
                team=i + 1,
                coord="COORD1",
                po=100 + i,
                style=f"Style-{i}",
                batch=100 + i,
                color=self.color,
                qty=100,
                seconds=50,
                accepted=95 - i,
                rejected=5 + i,
                sample=100,
                defects_total=3 + i,
                aql=2.5,
                pass_or_fail="PASS" if i % 2 == 0 else "REJECT",
            )

        # InspectionDefect records linked to QualityQcFa
        for qc in QualityQcFa.objects.all():
            InspectionDefect.objects.create(
                inspection=qc,
                defect_type=self.defect_type,
                amount=2,
            )
            InspectionDefect.objects.create(
                inspection=qc,
                defect_type=self.defect_type_2,
                amount=1,
            )

        # SecondsA4 records
        for i in range(3):
            SecondsA4.objects.create(
                year=2025,
                week=i + 1,
                date=f"2025-01-{i + 10:02d}",
                cut_num=i,
                style=f"Style-{i}",
                cut_qty=100,
                color=self.color,
                first_quality_qty_sewing=95,
                sample=100,
                pass_field=90,
                fail_field=10,
                sew_def=3,
                fab_def=2,
                accepted=95,
                rejected=5,
                total_of_2ds=5,
                percentage_of_2ds=5.0,
                line=f"{i + 1}",
                seconds_by_sew=12 + i,
                seconds_by_fab=8 + i,
                seconds_sew_a4=5,
                seconds_fab_a4=3,
            )

        # SecondsGeneral records
        for i in range(3):
            SecondsGeneral.objects.create(
                week=i + 1,
                date=f"2025-01-{i + 10:02d}",
                corrido_2=10 + i,
                barre=5 + i,
                otros_3=3 + i,
                degradacion=2 + i,
                bordados=1 + i,
                total_de_tela=21 + i * 5,
            )

        # Container records — 6 containers distributed across percentage ranges
        pct_values = [75.0, 85.0, 87.0, 92.0, 93.0, 97.0]
        for i, pct_pass in enumerate(pct_values):
            Container.objects.create(
                container_number=200 + i,
                customer="TestCustomer",
                transfer_of_container=1,
                total_palette=10,
                total_palette_pass=8 + i,
                total_palette_rejected=2 - i if i < 2 else i - 1,
                percentage_pass=pct_pass,
                percentage_reject=100 - pct_pass,
            )


# ─────────────────────────────────────────────────────────
# Grupo 1 — AQL KPIs
# ─────────────────────────────────────────────────────────

class AqlByStyleTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/aql-by-style/"""

    def test_returns_200_with_data(self):
        """Returns 200 with AQL percentages grouped by style."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("data", response.data)
        # We have 5 styles (Style-0 to Style-4)
        self.assertEqual(len(response.data["data"]), 5)

    def test_aql_by_style_empty_db(self):
        """Returns 200 with empty list when no QualityQcFa records exist."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_response_contains_label_and_value(self):
        """Each item has 'label' (style) and 'value' (AQL %)."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        for item in response.data["data"]:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], float)

    def test_sorted_by_value_descending(self):
        """Results are sorted by value descending."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        values = [item["value"] for item in response.data["data"]]
        self.assertEqual(values, sorted(values, reverse=True))


class AqlWeeklyTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/aql-weekly/"""

    def test_returns_200_with_series(self):
        """Returns 200 with AQL series and Trend series."""
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("data", response.data)
        # Should have AQL and Trend series
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["data"][0]["name"], "AQL")
        self.assertEqual(response.data["data"][1]["name"], "Trend")

    def test_aql_weekly_empty_db(self):
        """Returns 200 with empty list when no data."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_aql_weekly_with_week_filter(self):
        """GET ?week=1 returns only week 1 data."""
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only week 1 in filtered results
        aql_data = response.data["data"][0]["data"]
        self.assertEqual(len(aql_data), 1)
        self.assertEqual(aql_data[0]["x"], 1)

    def test_series_data_has_x_and_y(self):
        """Each data point has 'x' (week) and 'y' (AQL value)."""
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(url)
        for series in response.data["data"]:
            for point in series["data"]:
                self.assertIn("x", point)
                self.assertIn("y", point)


class AuditedPiecesTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/audited-pieces/"""

    def test_returns_200_with_series(self):
        """Returns 200 with SUM(sample) per week."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Pieces")

    def test_audited_pieces_empty_db(self):
        """Returns 200 with empty list when no data."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_audited_pieces_sum_is_correct(self):
        """Each week's y-value equals SUM(sample) for that week."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(url)
        pieces_data = response.data["data"][0]["data"]
        for point in pieces_data:
            week = point["x"]
            y_value = point["y"]
            expected = QualityQcFa.objects.filter(week=week).aggregate(
                total=Sum("sample")
            )["total"]
            self.assertEqual(y_value, expected)


# ─────────────────────────────────────────────────────────
# Grupo 2 — Rendimiento KPIs
# ─────────────────────────────────────────────────────────

class AcReRateByLineTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/ac-re-rate-by-line/"""

    def test_returns_200_with_counts(self):
        """Returns 200 with counts grouped by team × pass_or_fail."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # 5 teams × 1 pass_or_fail each = 5 unique combinations
        self.assertEqual(len(response.data), 5)

    def test_ac_re_rate_by_line_empty_db(self):
        """Returns empty list when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_label_value(self):
        """Each item has 'label' (team - pass_or_fail) and 'value' (count)."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            # Label format: "1 - PASS" or "2 - REJECT"
            parts = item["label"].split(" - ")
            self.assertEqual(len(parts), 2)


class SecondsReworkTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-rework/"""

    def test_returns_200_with_dual_series(self):
        """Returns 200 with Sewing and Fabric series by week."""
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = {s["name"] for s in response.data}
        self.assertEqual(names, {"Sewing", "Fabric"})

    def test_seconds_rework_empty_db(self):
        """Returns empty Sewing/Fabric series when no SecondsA4 records."""
        SecondsA4.objects.all().delete()
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]["data"]), 0)
        self.assertEqual(len(response.data[1]["data"]), 0)

    def test_seconds_rework_date_filter(self):
        """date_range filter applies to SecondsA4 queryset."""
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only week 1 should appear
        weeks = {point["x"] for s in response.data for point in s["data"]}
        self.assertEqual(weeks, {1})

    def test_sewing_and_fabric_have_data(self):
        """Both Sewing and Fabric series return non-empty data."""
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        response = self.client.get(url)
        sew_data = response.data[0]["data"]
        fab_data = response.data[1]["data"]
        self.assertTrue(len(sew_data) > 0)
        self.assertTrue(len(fab_data) > 0)


class PerformanceByCustomerTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/performance-by-customer/"""

    def test_returns_200_with_rates(self):
        """Returns 200 with acceptance rate per customer."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_performance_by_customer_empty_db(self):
        """Returns empty list when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_label_value(self):
        """Each item has 'label' (customer) and 'value' (acceptance rate %)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], float)

    def test_acceptance_rate_calculation(self):
        """Value equals SUM(accepted) / SUM(sample) * 100."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        for item in response.data:
            customer = item["label"]
            agg = QualityQcFa.objects.filter(customer=customer, sample__gt=0).aggregate(
                total_accepted=Sum("accepted"),
                total_sample=Sum("sample"),
            )
            if agg["total_sample"]:
                expected = round(
                    (agg["total_accepted"] / agg["total_sample"]) * 100, 2
                )
                self.assertAlmostEqual(item["value"], expected, places=1)


class PerformanceByLineTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/performance-by-line/"""

    def test_returns_200_with_rates(self):
        """Returns 200 with acceptance rate per team (line)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_performance_by_line_empty_db(self):
        """Returns empty list when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_label_value(self):
        """Each item has 'label' (team) and 'value' (acceptance rate %)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)


# ─────────────────────────────────────────────────────────
# Grupo 3 — Defectos KPIs
# ─────────────────────────────────────────────────────────

class TopDefectsTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/top-defects/"""

    def test_returns_200_with_defects(self):
        """Returns 200 with top 10 defect types by total amount."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(len(response.data) <= 10)

    def test_top_defects_empty_db(self):
        """Returns 200 with empty list when no InspectionDefect records."""
        InspectionDefect.objects.all().delete()
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_label_value(self):
        """Each item has 'label' (defect_type name) and 'value' (total amount)."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_top_defects_sorted_by_value_descending(self):
        """Results are sorted by value descending."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(url)
        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))


class FabricDefectsTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/fabric-defects/"""

    def test_returns_200_with_fabric_defects(self):
        """Returns 200 with SUM of each fabric defect column."""
        url = reverse("quality_data:kpi-fabric-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have 5 defect types: Corrido, Barre, Otros, Degradación, Bordados
        self.assertEqual(len(response.data), 5)

    def test_fabric_defects_empty_db(self):
        """Returns 200 with zeros when no SecondsGeneral records."""
        SecondsGeneral.objects.all().delete()
        url = reverse("quality_data:kpi-fabric-defects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["value"], 0)

    def test_response_format_label_value(self):
        """Each item has 'label' and 'value' (SUM)."""
        url = reverse("quality_data:kpi-fabric-defects")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    def test_fabric_defects_week_filter(self):
        """week filter applies to SecondsGeneral queryset."""
        url = reverse("quality_data:kpi-fabric-defects")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only week 1 data should be aggregated

    def test_fabric_defects_date_range_filter(self):
        """date_range filter applies to SecondsGeneral queryset."""
        url = reverse("quality_data:kpi-fabric-defects")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)


class DefectsByStyleTypeTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/defects-by-style-type/"""

    def test_returns_200_with_heatmap_data(self):
        """Returns 200 with style × defect_type heatmap data."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_defects_by_style_type_empty_db(self):
        """Returns 200 with empty list when no InspectionDefect records."""
        InspectionDefect.objects.all().delete()
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_x_y_value(self):
        """Each item has 'x' (style), 'y' (defect_type), 'value' (amount)."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("x", item)
            self.assertIn("y", item)
            self.assertIn("value", item)


# ─────────────────────────────────────────────────────────
# Grupo 4 — Operativos KPIs
# ─────────────────────────────────────────────────────────

class PassRejectDistributionTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/pass-reject-distribution/"""

    def test_returns_200_with_distribution(self):
        """Returns 200 with COUNT grouped by pass_or_fail."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have PASS and REJECT entries
        names = {item["name"] for item in response.data}
        self.assertEqual(names, {"PASS", "REJECT"})

    def test_pass_reject_distribution_empty_db(self):
        """Returns empty list when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_format_name_value(self):
        """Each item has 'name' (PASS/REJECT) and 'value' (count)."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    def test_count_matches_actual_records(self):
        """value equals actual COUNT for each pass_or_fail."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(url)
        for item in response.data:
            expected = QualityQcFa.objects.filter(
                pass_or_fail=item["name"]
            ).count()
            self.assertEqual(item["value"], expected)


class RejectedEvolutionTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/rejected-evolution/"""

    def test_returns_200_with_series(self):
        """Returns 200 with SUM(rejected) per week."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Rejected")
        self.assertTrue(len(response.data[0]["data"]) > 0)

    def test_rejected_evolution_empty_db(self):
        """Returns 200 with empty data when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data[0]["data"], [])

    def test_rejected_evolution_week_filter(self):
        """week filter returns only that week's data."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.data[0]["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["x"], 1)

    def test_data_point_format_x_y(self):
        """Each data point has 'x' (week) and 'y' (SUM rejected)."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(url)
        for point in response.data[0]["data"]:
            self.assertIn("x", point)
            self.assertIn("y", point)

    def test_rejected_sum_matches_actual(self):
        """y-value equals SUM(rejected) for that week."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(url)
        for point in response.data[0]["data"]:
            week = point["x"]
            expected = QualityQcFa.objects.filter(week=week).aggregate(
                total=Sum("rejected")
            )["total"]
            self.assertEqual(point["y"], expected or 0)


class ContainersByStateTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/containers-by-state/"""

    def test_returns_200_with_ranges(self):
        """Returns 200 with container counts per percentage_pass range."""
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have all 4 ranges: < 80%, 80-90%, 90-95%, > 95%
        self.assertEqual(len(response.data), 4)
        ranges = {item["name"] for item in response.data}
        self.assertEqual(
            ranges, {"< 80%", "80-90%", "90-95%", "> 95%"}
        )

    def test_containers_by_state_empty_db(self):
        """Returns all zeros when no Container records."""
        Container.objects.all().delete()
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["value"], 0)

    def test_response_format_name_value(self):
        """Each item has 'name' (range) and 'value' (count)."""
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)
        for item in response.data:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    def test_total_matches_container_count(self):
        """Sum of all range values equals total Container count."""
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, Container.objects.count())


class DefectRateTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/defect-rate/"""

    def test_returns_200_with_global_rate(self):
        """Returns 200 with global defect rate: SUM(defects_total)/SUM(sample)*100."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("label", response.data)
        self.assertIn("value", response.data)
        self.assertEqual(response.data["label"], "Defect Rate")

    def test_defect_rate_empty_db(self):
        """Returns 200 with value 0 when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 0)

    def test_defect_rate_calculation(self):
        """value equals SUM(defects_total) / SUM(sample) * 100."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(url)
        agg = QualityQcFa.objects.aggregate(
            total_defects=Sum("defects_total"),
            total_sample=Sum("sample"),
        )
        expected = (
            round((agg["total_defects"] / agg["total_sample"]) * 100, 2)
            if agg["total_sample"] and agg["total_sample"] > 0
            else 0
        )
        self.assertEqual(response.data["value"], expected)

    def test_defect_rate_week_filter(self):
        """week filter applies to defect rate calculation."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        agg = QualityQcFa.objects.filter(week=1).aggregate(
            total_defects=Sum("defects_total"),
            total_sample=Sum("sample"),
        )
        expected = (
            round((agg["total_defects"] / agg["total_sample"]) * 100, 2)
            if agg["total_sample"] and agg["total_sample"] > 0
            else 0
        )
        self.assertEqual(response.data["value"], expected)


# ─────────────────────────────────────────────────────────
# Filter Tests — KpiFilterMixin
# ─────────────────────────────────────────────────────────

class KpiFilterDateRangeTest(KpiTestMixin, TestCase):
    """Tests for date_range filter on KPI endpoints that use KpiFilterMixin."""

    def test_date_range_filter_audited_pieces(self):
        """date_range filter limits QualityQcFa-based KPIs to date range."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only week 1 (2025-01-10) should appear
        data = response.data["data"][0]["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["x"], 1)

    def test_date_range_filter_seconds_rework(self):
        """date_range filter limits SecondsA4-based KPIs to date range."""
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-10")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        weeks = {point["x"] for s in response.data for point in s["data"]}
        self.assertEqual(weeks, {1})


class KpiFilterTeamTest(KpiTestMixin, TestCase):
    """Tests for team filter on KPI endpoints that use KpiFilterMixin."""

    def test_team_filter_performance_by_line(self):
        """team filter limits results to specific team."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertEqual(item["label"], "1")

    def test_team_filter_ac_re_rate_by_line(self):
        """team filter limits ac-re-rate-by-line to specific team."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertTrue(item["label"].startswith("1 - "))


class KpiFilterCustomerTest(KpiTestMixin, TestCase):
    """Tests for customer filter on KPI endpoints."""

    def test_customer_filter_containers_by_state(self):
        """customer filter limits containers to matching customer."""
        Container.objects.create(
            container_number=300,
            customer="OtherCustomer",
            transfer_of_container=1,
            total_palette=10,
            total_palette_pass=9,
            total_palette_rejected=1,
            percentage_pass=90.0,
            percentage_reject=10.0,
        )
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?customer=TestCustomer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        # Only TestCustomer containers (6) should be included
        self.assertEqual(total, 6)

    def test_customer_filter_performance_by_customer(self):
        """customer filter (icontains) on performance-by-customer."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?customer=Test")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        for item in response.data:
            self.assertIn("Test", item["label"])


class KpiFilterWeekTest(KpiTestMixin, TestCase):
    """Tests for week filter on KpiFilterMixin endpoints."""

    def test_week_filter_aql_by_style(self):
        """week filter limits aql-by-style to specific week."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_week_filter_rejected_evolution(self):
        """week filter limits rejected-evolution to specific week."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.data[0]["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["x"], 1)

    def test_week_filter_pass_reject_distribution(self):
        """week filter limits pass-reject-distribution to specific week."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# Edge Cases
# ─────────────────────────────────────────────────────────

class KpiEdgeCasesTest(TestCase):
    """Edge case tests for KPI endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.color = Color.objects.create(name="blue", is_active=True)

    def test_zero_sample_does_not_crash_performance_by_line(self):
        """QualityQcFa with sample=0 should not crash performance calculation."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-01",
            week=1,
            customer="ZeroSample",
            team=1,
            coord="C",
            po=1,
            style="ZeroStyle",
            batch=1,
            color=self.color,
            qty=0,
            seconds=0,
            accepted=0,
            rejected=0,
            sample=0,  # Zero sample!
            defects_total=0,
            aql=0,
            pass_or_fail="PASS",
        )
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_zero_sample_does_not_crash_performance_by_customer(self):
        """QualityQcFa with sample=0 should not crash customer performance calc."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-01",
            week=1,
            customer="ZeroSampleCust",
            team=1,
            coord="C",
            po=1,
            style="ZeroStyle2",
            batch=1,
            color=self.color,
            qty=0,
            seconds=0,
            accepted=0,
            rejected=0,
            sample=0,  # Zero sample!
            defects_total=0,
            aql=0,
            pass_or_fail="PASS",
        )
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_zero_sample_does_not_crash_defect_rate(self):
        """QualityQcFa with sample=0 should not crash defect rate."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-01",
            week=1,
            customer="ZeroSampleCust2",
            team=1,
            coord="C",
            po=1,
            style="ZeroStyle3",
            batch=1,
            color=self.color,
            qty=0,
            seconds=0,
            accepted=0,
            rejected=0,
            sample=0,
            defects_total=5,
            aql=0,
            pass_or_fail="PASS",
        )
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should handle division by zero gracefully
        self.assertEqual(response.data["value"], 0)

    def test_empty_date_range_returns_no_data(self):
        """date_range with no matching data returns empty results."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?date_range=2030-01-01,2030-01-31")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])
