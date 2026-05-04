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
from rest_framework import exceptions as rest_framework_exceptions
from django.db.models import Sum
from unittest.mock import patch
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
        from quality_data.models import SecondsGeneralDefectType, SecondsGeneralDefect
        defect_types = {}
        for name in ["corrido_2", "barre", "otros_3", "degradacion", "bordados"]:
            defect_types[name], _ = SecondsGeneralDefectType.objects.get_or_create(name=name)

        for i in range(3):
            sg = SecondsGeneral.objects.create(
                week=i + 1,
                date=f"2025-01-{i + 10:02d}",
            )
            for name, amount_base in [
                ("corrido_2", 10), ("barre", 5), ("otros_3", 3),
                ("degradacion", 2), ("bordados", 1),
            ]:
                SecondsGeneralDefect.objects.create(
                    seconds_general=sg,
                    defect_type=defect_types[name],
                    amount=amount_base + i,
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

    def test_groups_by_style_with_unique_labels_and_correct_values(self):
        """Repeated styles are aggregated once with correct AQL."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=6,
            customer="TestCustomer",
            team=99,
            coord="COORD2",
            po=999,
            style="Style-0",  # Existing style to force grouping
            batch=999,
            color=self.color,
            qty=100,
            seconds=30,
            accepted=80,
            rejected=20,
            sample=50,
            defects_total=5,
            aql=0,
            pass_or_fail="REJECT",
        )

        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), len(set(labels)))  # unique labels only

        style_0 = next(item for item in response.data["data"] if item["label"] == "Style-0")
        # Original Style-0: defects=3, sample=100; new row: defects=5, sample=50
        # Expected AQL = (8/150)*100 = 5.33
        self.assertAlmostEqual(style_0["value"], 5.33, places=2)


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

    def test_returns_one_point_per_week_with_summed_sample(self):
        """Multiple records in same week collapse into single aggregated point."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-11",
            week=1,  # Existing week to force grouping
            customer="TestCustomer",
            team=10,
            coord="COORD3",
            po=111,
            style="Style-extra",
            batch=111,
            color=self.color,
            qty=100,
            seconds=50,
            accepted=40,
            rejected=10,
            sample=50,
            defects_total=2,
            aql=0,
            pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        points = response.data["data"][0]["data"]
        weeks = [point["x"] for point in points]
        self.assertEqual(len(weeks), len(set(weeks)))  # one point per week

        week_1 = next(point for point in points if point["x"] == 1)
        # Original week 1 sample=100 + new sample=50
        self.assertEqual(week_1["y"], 150)


class AqlDtoBoundaryTest(KpiTestMixin, TestCase):
    def test_aql_by_style_uses_dto_serializer_helpers(self):
        url = reverse("quality_data:kpi-aql-aql-by-style")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            with patch("quality_data.views._serialize_envelope", wraps=__import__("quality_data.views", fromlist=["_serialize_envelope"])._serialize_envelope) as serialize_envelope:
                response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreaterEqual(serialize_payload.call_count, 1)
        self.assertEqual(serialize_envelope.call_count, 1)

    def test_aql_weekly_uses_dto_serializer_helpers(self):
        url = reverse("quality_data:kpi-aql-aql-weekly")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            with patch("quality_data.views._serialize_envelope", wraps=__import__("quality_data.views", fromlist=["_serialize_envelope"])._serialize_envelope) as serialize_envelope:
                response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreaterEqual(serialize_payload.call_count, 2)
        self.assertEqual(serialize_envelope.call_count, 1)

    def test_audited_pieces_uses_dto_serializer_helpers(self):
        url = reverse("quality_data:kpi-aql-audited-pieces")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            with patch("quality_data.views._serialize_envelope", wraps=__import__("quality_data.views", fromlist=["_serialize_envelope"])._serialize_envelope) as serialize_envelope:
                response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreaterEqual(serialize_payload.call_count, 1)
        self.assertEqual(serialize_envelope.call_count, 1)


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


class RendimientoDtoBoundaryTest(KpiTestMixin, TestCase):
    def test_ac_re_rate_by_line_uses_dto_payload_serializer(self):
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)

    def test_seconds_rework_uses_dto_payload_serializer(self):
        url = reverse("quality_data:kpi-rendimiento-seconds-rework")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)

    def test_performance_by_customer_uses_dto_payload_serializer(self):
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)

    def test_performance_by_line_uses_dto_payload_serializer(self):
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)


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

    def test_top_defects_style_filter(self):
        """style filter applies to InspectionDefect via inspection__style."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?style=Style-0")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should return defect data (filtered by inspections with style containing "Style-0")
        self.assertTrue(len(response.data) > 0)

    def test_top_defects_style_filter_no_match(self):
        """style filter with non-existent style returns empty."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?style=NONEXISTENT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_top_defects_team_filter(self):
        """team filter applies via inspection__team."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)


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

    def test_defects_by_style_type_style_filter(self):
        """style filter applies via inspection__style."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(f"{url}?style=Style-0")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertIn("Style-0", item["x"])

    def test_defects_by_style_type_team_filter(self):
        """team filter applies via inspection__team."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)


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

    def test_from_date_to_date_filters_inclusive(self):
        container_a = Container.objects.get(container_number=200)
        container_b = Container.objects.get(container_number=201)
        container_c = Container.objects.get(container_number=202)
        container_a.date = "2025-01-10"
        container_b.date = "2025-01-11"
        container_c.date = "2025-01-12"
        container_a.save()
        container_b.save()
        container_c.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?from_date=2025-01-10&to_date=2025-01-11")

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)

    def test_date_filter_excludes_null_dates(self):
        dated_container = Container.objects.get(container_number=200)
        dated_container.date = "2025-01-10"
        dated_container.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?from_date=2025-01-01&to_date=2025-01-31")

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 1)

    def test_date_range_filters_inclusive(self):
        container_a = Container.objects.get(container_number=200)
        container_b = Container.objects.get(container_number=201)
        container_c = Container.objects.get(container_number=202)
        container_a.date = "2025-01-10"
        container_b.date = "2025-01-11"
        container_c.date = "2025-01-12"
        container_a.save()
        container_b.save()
        container_c.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=2025-01-10,2025-01-11")

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)

    def test_date_range_takes_precedence_over_from_to(self):
        container_a = Container.objects.get(container_number=200)
        container_b = Container.objects.get(container_number=201)
        container_a.date = "2025-01-10"
        container_b.date = "2025-01-12"
        container_a.save()
        container_b.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(
            f"{url}?date_range=2025-01-10,2025-01-10&from_date=2025-01-01&to_date=2025-01-31"
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 1)

    def test_blank_date_range_falls_back_to_from_to_filters(self):
        container_a = Container.objects.get(container_number=200)
        container_b = Container.objects.get(container_number=201)
        container_c = Container.objects.get(container_number=202)
        container_a.date = "2025-01-10"
        container_b.date = "2025-01-11"
        container_c.date = "2025-01-12"
        container_a.save()
        container_b.save()
        container_c.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(
            f"{url}?date_range=&from_date=2025-01-10&to_date=2025-01-11"
        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)

    def test_blank_date_range_without_legacy_filters_behaves_as_omitted(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=")

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 6)

    def test_partial_date_range_start_only_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=2025-01-10,")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_partial_date_range_end_only_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=,2025-01-10")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_comma_only_date_range_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=,")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_reversed_date_range_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=2025-01-12,2025-01-10")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_reversed_legacy_from_to_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?from_date=2025-01-12&to_date=2025-01-10")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("from_date", response.data)
        self.assertIn("to_date", response.data)

    def test_bucket_gt_95_excludes_exactly_95(self):
        container_95 = Container.objects.get(container_number=205)
        container_95.percentage_pass = 95.0
        container_95.percentage_reject = 5.0
        container_95.save()

        container_over_95 = Container.objects.get(container_number=204)
        container_over_95.percentage_pass = 95.1
        container_over_95.percentage_reject = 4.9
        container_over_95.save()

        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        counts = {item["name"]: item["value"] for item in response.data}
        self.assertEqual(counts["90-95%"], 2)
        self.assertEqual(counts["> 95%"], 1)

    def test_invalid_date_filters_return_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?from_date=10-01-2025&to_date=2025-01-31")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("from_date", response.data)

    def test_invalid_to_date_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?from_date=2025-01-01&to_date=31-01-2025")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("to_date", response.data)

    def test_invalid_date_range_format_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=2025-01-10")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_invalid_date_range_value_returns_400(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(f"{url}?date_range=2025-01-10,31-01-2025")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_no_date_filters_preserves_legacy_behavior(self):
        url = reverse("quality_data:kpi-containers-by-state")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 6)


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


class DefectOperationalDtoBoundaryTest(KpiTestMixin, TestCase):
    def _assert_route_uses_payload_serializer(self, route_name):
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(reverse(route_name))

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)

    def test_top_defects_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-top-defects")

    def test_fabric_defects_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-fabric-defects")

    def test_defects_by_style_type_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-defects-by-style-type")

    def test_pass_reject_distribution_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-pass-reject-distribution")

    def test_rejected_evolution_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-rejected-evolution")

    def test_containers_by_state_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-containers-by-state")

    def test_defect_rate_uses_dto_payload_serializer(self):
        self._assert_route_uses_payload_serializer("quality_data:kpi-defect-rate")

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

    def test_date_range_partial_value_returns_400_for_mixin_endpoint(self):
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?date_range=2025-01-10,")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)

    def test_date_range_reversed_bounds_returns_400_for_mixin_endpoint(self):
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?date_range=2025-01-11,2025-01-10")

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_range", response.data)


class KpiFilterRequiredDateBoundsHelperTest(TestCase):
    def test_parse_required_date_bounds_returns_iso_dates(self):
        from quality_data.views import KpiFilterMixin

        from_date, to_date = KpiFilterMixin.parse_required_date_bounds(
            {"date_from": "2025-01-01", "date_to": "2025-01-31"}
        )

        self.assertEqual(from_date.isoformat(), "2025-01-01")
        self.assertEqual(to_date.isoformat(), "2025-01-31")

    def test_parse_required_date_bounds_requires_both_fields(self):
        from quality_data.views import KpiFilterMixin

        with self.assertRaises(rest_framework_exceptions.ValidationError) as error_ctx:
            KpiFilterMixin.parse_required_date_bounds({"date_to": "2025-01-31"})

        self.assertIn("date_from", error_ctx.exception.detail)

        with self.assertRaises(rest_framework_exceptions.ValidationError) as error_ctx:
            KpiFilterMixin.parse_required_date_bounds({"date_from": "2025-01-01"})

        self.assertIn("date_to", error_ctx.exception.detail)

    def test_parse_required_date_bounds_rejects_invalid_iso_values(self):
        from quality_data.views import KpiFilterMixin

        with self.assertRaises(rest_framework_exceptions.ValidationError) as error_ctx:
            KpiFilterMixin.parse_required_date_bounds(
                {"date_from": "01-01-2025", "date_to": "2025-01-31"}
            )

        self.assertIn("date_from", error_ctx.exception.detail)

    def test_parse_required_date_bounds_rejects_reversed_order(self):
        from quality_data.views import KpiFilterMixin

        with self.assertRaises(rest_framework_exceptions.ValidationError) as error_ctx:
            KpiFilterMixin.parse_required_date_bounds(
                {"date_from": "2025-02-01", "date_to": "2025-01-31"}
            )

        self.assertIn("date_from", error_ctx.exception.detail)
        self.assertIn("date_to", error_ctx.exception.detail)


class KpiDtoHelperTest(TestCase):
    def test_serialize_payload_helper_returns_serializer_data(self):
        from quality_data.views import _serialize_payload
        from quality_data.serializers import KpiBarSerializer

        payload = [{"label": "Line 1", "value": 5}]
        serialized = _serialize_payload(KpiBarSerializer, payload, many=True)

        self.assertEqual(serialized, payload)

    def test_serialize_envelope_helper_wraps_data_key(self):
        from quality_data.views import _serialize_envelope
        from quality_data.serializers import KpiBarEnvelopeSerializer

        payload = [{"label": "Line 1", "value": 5}]
        serialized = _serialize_envelope(KpiBarEnvelopeSerializer, payload)

        self.assertEqual(serialized, {"data": payload})


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
        """customer filter (iexact) on performance-by-customer."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?customer=TestCustomer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        for item in response.data:
            self.assertIn("TestCustomer", item["label"])


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


# ─────────────────────────────────────────────────────────
# Filter Options Endpoint
# ─────────────────────────────────────────────────────────

class FilterOptionsViewTest(TestCase):
    """Tests for GET /quality/kpis/filter-options/"""

    def setUp(self):
        self.client = APIClient()
        self.color = Color.objects.create(name="blue", is_active=True)
        for i in range(3):
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1=f"2025-01-{i + 10:02d}",
                week=i + 1,
                customer="CustomerA" if i == 0 else "CustomerB",
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
                pass_or_fail="PASS",
            )

    def test_returns_200_with_filter_options(self):
        """Returns 200 with distinct values for each filter field."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("week", response.data)
        self.assertIn("team", response.data)
        self.assertIn("style", response.data)
        self.assertIn("color", response.data)
        self.assertIn("customer", response.data)
        self.assertIn("batch", response.data)

    def test_filter_options_contain_expected_values(self):
        """Returns distinct values from QualityQcFa records."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(url)
        self.assertEqual(set(response.data["week"]), {1, 2, 3})
        self.assertEqual(set(response.data["team"]), {1, 2, 3})
        self.assertEqual(set(response.data["style"]), {"Style-0", "Style-1", "Style-2"})
        self.assertEqual(set(response.data["customer"]), {"CustomerA", "CustomerB"})
        self.assertEqual(set(response.data["batch"]), {100, 101, 102})

    def test_filter_options_excludes_duplicates(self):
        """Each field's values are unique."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=4,  # New week
            customer="CustomerA",  # Duplicate customer
            team=1,  # Duplicate team
            coord="COORD2",
            po=200,
            style="Style-0",  # Duplicate style
            batch=100,  # Duplicate batch
            color=self.color,
            qty=100,
            seconds=50,
            accepted=90,
            rejected=10,
            sample=100,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(url)
        # Should still have unique values (no new unique values added, so counts same)
        self.assertEqual(len(response.data["week"]), 4)  # 1, 2, 3, 4 (but unique)
        self.assertEqual(len(response.data["style"]), 3)  # Style-0, Style-1, Style-2

    def test_filter_options_empty_db(self):
        """Returns empty lists when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["week"], [])
        self.assertEqual(response.data["team"], [])
        self.assertEqual(response.data["style"], [])
        self.assertEqual(response.data["customer"], [])
        self.assertEqual(response.data["batch"], [])

    def test_filter_options_uses_dto_serializer(self):
        url = reverse("quality_data:kpi-filter-options")
        with patch("quality_data.views._serialize_payload", wraps=__import__("quality_data.views", fromlist=["_serialize_payload"])._serialize_payload) as serialize_payload:
            response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(serialize_payload.call_count, 1)


class KpiContractParityTest(KpiTestMixin, TestCase):
    """Regression tests that lock public KPI response contracts."""

    def test_kpi_object_families_keep_expected_keys_and_types(self):
        cases = [
            ("quality_data:kpi-aql-aql-by-style", "data", {"label", "value"}),
            ("quality_data:kpi-rendimiento-ac-re-rate-by-line", None, {"label", "value"}),
            ("quality_data:kpi-rendimiento-performance-by-customer", None, {"label", "value"}),
            ("quality_data:kpi-rendimiento-performance-by-line", None, {"label", "value"}),
            ("quality_data:kpi-top-defects", None, {"label", "value"}),
            ("quality_data:kpi-fabric-defects", None, {"label", "value"}),
            ("quality_data:kpi-defects-by-style-type", None, {"x", "y", "value"}),
            ("quality_data:kpi-pass-reject-distribution", None, {"name", "value"}),
            ("quality_data:kpi-containers-by-state", None, {"name", "value"}),
            ("quality_data:kpi-defect-composition", None, {"name", "value"}),
        ]

        for route_name, wrapped_key, expected_keys in cases:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)

            payload = response.data[wrapped_key] if wrapped_key else response.data
            self.assertIsInstance(payload, list)

            if payload:
                self.assertEqual(set(payload[0].keys()), expected_keys)

    def test_series_kpis_keep_expected_shape_and_numeric_points(self):
        series_routes = [
            "quality_data:kpi-aql-aql-weekly",
            "quality_data:kpi-aql-audited-pieces",
            "quality_data:kpi-rendimiento-seconds-rework",
            "quality_data:kpi-rejected-evolution",
            "quality_data:kpi-defect-trend-top-3",
        ]

        for route_name in series_routes:
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)

            payload = response.data["data"] if route_name.startswith("quality_data:kpi-aql-") else response.data
            self.assertIsInstance(payload, list)

            for series in payload:
                self.assertEqual(set(series.keys()), {"name", "data"})
                self.assertIsInstance(series["data"], list)
                for point in series["data"]:
                    self.assertEqual(set(point.keys()), {"x", "y"})
                    self.assertIsInstance(point["y"], (int, float))

    def test_scalar_kpi_contract_is_stable(self):
        response = self.client.get(reverse("quality_data:kpi-defect-rate"))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"label", "value"})
        self.assertEqual(response.data["label"], "Defect Rate")
        self.assertIsInstance(response.data["value"], (int, float))

    def test_filter_options_contract_keeps_key_set_and_sorted_lists(self):
        response = self.client.get(reverse("quality_data:kpi-filter-options"))
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        self.assertEqual(
            list(response.data.keys()),
            ["week", "team", "style", "color", "customer", "batch"],
        )

        for key in ["week", "team", "style", "color", "customer", "batch"]:
            self.assertIsInstance(response.data[key], list)
            self.assertEqual(response.data[key], sorted(response.data[key]))


# ─────────────────────────────────────────────────────────
# QFA/QFC Exclusive Charts — New defect insight endpoints
# ─────────────────────────────────────────────────────────

class DefectCompositionTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/defect-composition/

    Contract: [{name: string, value: integer}]
    Sorted by value DESC, name ASC (stabilized tie-break).
    Excludes zero totals.
    Returns [] when no positive defect amounts remain.
    """

    def test_endpoint_returns_200(self):
        """GET /quality/kpis/defect-composition/ returns 200."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    # ── Shape contract ──────────────────────────────────

    def test_response_items_have_name_and_integer_value(self):
        """Every item has 'name' (string) and 'value' (integer)."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        for item in response.data:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    # ── Sorting ─────────────────────────────────────────

    def test_sorted_by_value_desc_then_name_asc(self):
        """Items are sorted by value DESC, with name ASC as tie-breaker."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        items = response.data
        self.assertGreaterEqual(len(items), 2)

        sorted_items = sorted(
            items,
            key=lambda x: (-x["value"], x["name"]),
        )
        self.assertEqual(items, sorted_items)

    # ── Zero exclusion ──────────────────────────────────

    def test_zeros_are_excluded(self):
        """Items with value=0 are excluded from results."""
        # Create a zero-amount defect
        zero_defect_type = DefectType.objects.create(name="zero-only", is_active=True)
        InspectionDefect.objects.create(
            inspection=QualityQcFa.objects.first(),
            defect_type=zero_defect_type,
            amount=0,
        )
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        names = {item["name"] for item in response.data}
        self.assertNotIn("zero-only", names)

    # ── Empty data ──────────────────────────────────────

    def test_empty_db_returns_empty_list(self):
        """When no InspectionDefect records exist, returns []."""
        InspectionDefect.objects.all().delete()
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: context (plant/customer) ────────────────

    def test_context_plant_returns_only_qfa_defects(self):
        """?context=plant returns only QFA (Plant) defects."""
        # Create QFC record with a distinct defect type
        qfc_defect_type = DefectType.objects.create(name="qfc-only-defect", is_active=True)
        qfc_record = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=1, customer="CustOnly",
            team=99, coord="C", po=999, style="QfcStyle", batch=999,
            color=self.color, qty=50, seconds=5, accepted=45, rejected=5,
            sample=50, defects_total=3, aql=2.0, pass_or_fail="PASS",
        )
        InspectionDefect.objects.create(
            inspection=qfc_record,
            defect_type=qfc_defect_type,
            amount=10,
        )

        url = reverse("quality_data:kpi-defect-composition")
        # With context=plant, we should NOT see qfc-only-defect
        response = self.client.get(f"{url}?context=plant")
        names = {item["name"] for item in response.data}
        self.assertNotIn("qfc-only-defect", names)

        # With context=customer, we SHOULD see qfc-only-defect
        response2 = self.client.get(f"{url}?context=customer")
        names2 = {item["name"] for item in response2.data}
        self.assertIn("qfc-only-defect", names2)

    # ── Filter: other params ────────────────────────────

    def test_style_filter_works(self):
        """?style= filter narrows to inspections with matching style."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?style=Style-0")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have data filtered to Style-0 only
        self.assertGreater(len(response.data), 0)

    def test_style_filter_no_match_returns_empty(self):
        """?style=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?style=NONEXISTENT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_team_filter_works(self):
        """?team=1 filters by inspection__team."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    # ── Triangulation ───────────────────────────────────

    def test_tie_break_by_name_asc_when_values_equal(self):
        """When two defect types have equal total, sort by name ASC."""
        # Create two defect types with same total
        dt_a = DefectType.objects.create(name="a-tie", is_active=True)
        dt_b = DefectType.objects.create(name="b-tie", is_active=True)
        record = QualityQcFa.objects.first()
        InspectionDefect.objects.create(inspection=record, defect_type=dt_a, amount=15)
        InspectionDefect.objects.create(inspection=record, defect_type=dt_b, amount=15)

        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(url)
        names = [item["name"] for item in response.data]
        # "a-tie" should come before "b-tie" when values are tied
        tie_idx_a = names.index("a-tie")
        tie_idx_b = names.index("b-tie")
        self.assertLess(tie_idx_a, tie_idx_b)


class DefectTrendTop3Test(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/defect-trend-top-3/

    Contract: [{name: string, data: [{x: integer, y: integer}]}]
    Up to 3 series (top 3 defect types by total amount).
    Every series includes every filtered week.
    Missing weeks have y: 0.
    x values are ascending.
    Returns [] when no positive defect amounts remain.
    """

    def test_endpoint_returns_200(self):
        """GET /quality/kpis/defect-trend-top-3/ returns 200."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    # ── Shape contract ──────────────────────────────────

    def test_response_is_list_of_series_with_name_and_data(self):
        """Each item is {name, data:[{x,y}]} with numeric x,y."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        self.assertIsInstance(response.data, list)
        self.assertLessEqual(len(response.data), 3)
        for series in response.data:
            self.assertIn("name", series)
            self.assertIn("data", series)
            self.assertIsInstance(series["data"], list)
            for point in series["data"]:
                self.assertIn("x", point)
                self.assertIn("y", point)
                self.assertIsInstance(point["x"], int)
                self.assertIsInstance(point["y"], (int, float))

    # ── Top-3 selection ─────────────────────────────────

    def test_top_3_defect_types_by_total_amount(self):
        """The 3 series correspond to the top 3 defect types by SUM(amount)."""
        # Create 4 defect types with distinct totals
        extras = []
        for i, (name, amount) in enumerate([
            ("type_a", 100),
            ("type_b", 80),
            ("type_c", 50),
            ("type_d", 30),
        ]):
            dt = DefectType.objects.create(name=name, is_active=True)
            InspectionDefect.objects.create(
                inspection=QualityQcFa.objects.first(),
                defect_type=dt,
                amount=amount,
            )
            extras.append(name)

        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        series_names = [s["name"] for s in response.data]
        self.assertEqual(len(series_names), 3)
        # Top 3: type_a (100), type_b (80), type_c (50)
        self.assertIn("type_a", series_names)
        self.assertIn("type_b", series_names)
        self.assertIn("type_c", series_names)
        self.assertNotIn("type_d", series_names)

    # ── Week ordering and zero-fill ─────────────────────

    def test_weeks_are_ascending(self):
        """x values (weeks) are in ascending order."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        for series in response.data:
            weeks = [point["x"] for point in series["data"]]
            self.assertEqual(weeks, sorted(weeks))

    def test_all_series_have_same_week_set(self):
        """Every series includes every filtered week (same week set)."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        if len(response.data) < 2:
            self.skipTest("Need at least 2 series to compare week sets")
        week_sets = [
            frozenset(point["x"] for point in series["data"])
            for series in response.data
        ]
        self.assertEqual(len(set(week_sets)), 1)

    def test_zero_fill_for_missing_weeks(self):
        """When a top-3 defect is absent in a week, y=0 for that week."""
        # Create a defect that appears only in week 1
        dt_sparse = DefectType.objects.create(name="sparse-defect", is_active=True)
        # Get a record with week=1
        wk1_record = QualityQcFa.objects.filter(week=1).first()
        InspectionDefect.objects.create(
            inspection=wk1_record,
            defect_type=dt_sparse,
            amount=20,  # High enough to be in top 3
        )

        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        for series in response.data:
            if series["name"] == "sparse-defect":
                # Find a week that's in other series but might be missing for this one
                points_by_week = {p["x"]: p["y"] for p in series["data"]}
                # Check weeks 2, 3, 4, 5 — the defect should have y=0 there
                missing_weeks_zero = [
                    points_by_week.get(w, "missing") == 0
                    for w in [2, 3, 4, 5]
                ]
                self.assertTrue(any(missing_weeks_zero))

    # ── Empty data ──────────────────────────────────────

    def test_empty_db_returns_empty_list(self):
        """When no InfectionDefect records, returns []."""
        InspectionDefect.objects.all().delete()
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_all_zero_amounts_returns_empty(self):
        """When all defect amounts are 0, returns []."""
        InspectionDefect.objects.all().update(amount=0)
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: context ─────────────────────────────────

    def test_context_customer_isolates_qfc_defects(self):
        """?context=customer returns only QFC defect trend data."""
        qfc_defect_type = DefectType.objects.create(name="qfc-trend-defect", is_active=True)
        qfc_record = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustTrend",
            team=99, coord="C", po=999, style="QfcTrend", batch=999,
            color=self.color, qty=50, seconds=5, accepted=45, rejected=5,
            sample=50, defects_total=3, aql=2.0, pass_or_fail="PASS",
        )
        InspectionDefect.objects.create(
            inspection=qfc_record,
            defect_type=qfc_defect_type,
            amount=25,
        )

        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        names = {s["name"] for s in response.data}
        self.assertIn("qfc-trend-defect", names)

    # ── Filter: other params ────────────────────────────

    def test_week_filter_works(self):
        """?week=1 filters to only that week's inspections."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for series in response.data:
            weeks = {p["x"] for p in series["data"]}
            self.assertTrue(weeks == {1} or series["data"] == [])

    # ── Triangulation ───────────────────────────────────

    def test_fewer_than_3_defect_types_returns_available_count(self):
        """When only 2 defect types have positive amounts, returns 2 series."""
        # Delete all existing defects, create only 2
        InspectionDefect.objects.all().delete()
        dt1 = DefectType.objects.create(name="only-a", is_active=True)
        dt2 = DefectType.objects.create(name="only-b", is_active=True)
        record = QualityQcFa.objects.first()
        InspectionDefect.objects.create(inspection=record, defect_type=dt1, amount=5)
        InspectionDefect.objects.create(inspection=record, defect_type=dt2, amount=8)

        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({s["name"] for s in response.data}, {"only-a", "only-b"})
