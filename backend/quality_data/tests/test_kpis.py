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


    def test_aql_by_style_qfc_uses_accepted_plus_rejected(self):
        """AQL by style uses accepted+rejected for QFC when it differs from sample."""
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustQFC",
            team=1, coord="C", po=100, style="QfcStyle", batch=1,
            color=self.color, qty=50, seconds=20, accepted=80, rejected=20,
            sample=200,
            defects_total=5, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        # 5 / (80+20) * 100 = 5.0  (not 5/200*100 = 2.5)
        self.assertAlmostEqual(response.data["data"][0]["value"], 5.0, places=2)

    def test_aql_by_style_qfa_preserves_sample(self):
        """AQL by style uses sample for QFA even when accepted+rejected differs."""
        QualityQcFa.objects.all().delete()
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustQFA",
            team=1, coord="C", po=100, style="QfaStyle", batch=1,
            color=self.color, qty=50, seconds=20, accepted=30, rejected=20,
            sample=100,
            defects_total=10, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)  # default context=plant
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        # 10 / 100 * 100 = 10.0  (must use sample, not 10/50*100)
        self.assertAlmostEqual(response.data["data"][0]["value"], 10.0, places=2)


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

    def test_aql_weekly_qfc_uses_accepted_plus_rejected(self):
        """AQL weekly uses accepted+rejected for QFC when it differs from sample."""
        QualityQcFa.objects.all().delete()
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustQFC",
            team=1, coord="C", po=100, style="S1", batch=1,
            color=self.color, qty=50, seconds=20, accepted=80, rejected=20,
            sample=200,
            defects_total=5, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        aql_series = response.data["data"][0]
        self.assertEqual(aql_series["name"], "AQL")
        # 5 / (80+20) * 100 = 5.0
        self.assertAlmostEqual(aql_series["data"][0]["y"], 5.0, places=2)

    def test_aql_weekly_qfa_preserves_sample(self):
        """AQL weekly uses sample for QFA even when accepted+rejected differs."""
        QualityQcFa.objects.all().delete()
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustQFA",
            team=1, coord="C", po=100, style="S1", batch=1,
            color=self.color, qty=50, seconds=20, accepted=30, rejected=20,
            sample=100,
            defects_total=10, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(url)  # default context=plant
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        aql_series = response.data["data"][0]
        self.assertEqual(aql_series["name"], "AQL")
        # 10 / 100 * 100 = 10.0  (must use sample)
        self.assertAlmostEqual(aql_series["data"][0]["y"], 10.0, places=2)


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


class AqlByTeamTest(KpiTestMixin, TestCase):
    """Tests for GET /quality/kpis/aql/aql-by-team/"""

    def test_returns_200_with_data_envelope(self):
        """Returns 200 with {data:[{label,value}]} envelope."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertIsInstance(response.data["data"], list)
        # 5 teams (1-5), one record each
        self.assertEqual(len(response.data["data"]), 5)

    def test_empty_db_returns_empty_data(self):
        """Returns 200 with {data:[]} when no QualityQcFa records."""
        QualityQcFa.objects.all().delete()
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])

    def test_response_items_have_label_and_value(self):
        """Each item has 'label' (team as string) and 'value' (float AQL %)."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        for item in response.data["data"]:
            self.assertIn("label", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], float)

    def test_aggregates_repeated_team_rows(self):
        """Multiple rows for same team sum defects_total and sample before AQL."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=6,
            customer="TestCustomer",
            team=1,  # Existing team 1 to force aggregation
            coord="COORD2",
            po=999,
            style="Style-Extra",
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

        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # Verify unique labels only
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), len(set(labels)))

        # Team 1: original (defects=3, sample=100) + new (defects=5, sample=50)
        # Expected: (3+5)/(100+50) * 100 = 8/150 * 100 = 5.33
        team_1 = next(item for item in response.data["data"] if item["label"] == "1")
        self.assertAlmostEqual(team_1["value"], 5.33, places=2)

    def test_zero_sample_team_returns_zero(self):
        """A team with SUM(sample)=0 returns value=0.0 and does not crash."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=6,
            customer="TestCustomer",
            team=99,
            coord="COORD2",
            po=999,
            style="Style-Zero",
            batch=999,
            color=self.color,
            qty=0,
            seconds=0,
            accepted=0,
            rejected=0,
            sample=0,
            defects_total=0,
            aql=0,
            pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        team_99 = next(
            (item for item in response.data["data"] if item["label"] == "99"),
            None,
        )
        self.assertIsNotNone(team_99)
        self.assertEqual(team_99["value"], 0.0)

    def test_week_filter_narrows_results(self):
        """?week=1 returns only team(s) from that week."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Only team 1 has week=1 in the base fixture
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(labels, ["1"])

    def test_team_filter_narrows_results(self):
        """?team=2 returns only team 2 data."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?team=2")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(labels, ["2"])

    def test_combined_context_customer_week_team_filter(self):
        """?context=customer&week=...&team=... composes filters correctly."""
        # Create a QFC record to test combined context + week + team filter
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-02-01",
            week=6,
            customer="CustFilter",
            team=20,
            coord="COORD_C",
            po=200,
            style="CustStyle",
            batch=200,
            color=self.color,
            qty=100,
            seconds=40,
            accepted=80,
            rejected=20,
            sample=200,
            defects_total=10,
            aql=2.5,
            pass_or_fail="FAIL",
        )

        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer&week=6&team=20")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["label"], "20")
        # QFC: defects / (accepted + rejected) * 100 = 10 / 100 * 100 = 10.0
        self.assertAlmostEqual(response.data["data"][0]["value"], 10.0, places=2)

    def test_aql_by_team_qfc_uses_accepted_plus_rejected(self):
        """AQL by team uses accepted+rejected for QFC when it differs from sample."""
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustQFC",
            team=5, coord="C", po=100, style="S1", batch=1,
            color=self.color, qty=50, seconds=20, accepted=80, rejected=20,
            sample=200,
            defects_total=5, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer&team=5")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        # 5 / (80+20) * 100 = 5.0  (not 5/200*100 = 2.5)
        self.assertAlmostEqual(response.data["data"][0]["value"], 5.0, places=2)

    def test_aql_by_team_qfa_preserves_sample(self):
        """AQL by team still uses sample for QFA even when accepted+rejected differs."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustQFA",
            team=6, coord="C", po=101, style="S2", batch=2,
            color=self.color, qty=50, seconds=20, accepted=30, rejected=20,
            sample=100,
            defects_total=10, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=plant&team=6")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        # 10 / 100 * 100 = 10.0  (must use sample, not 10/50*100)
        self.assertAlmostEqual(response.data["data"][0]["value"], 10.0, places=2)


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

    def test_aql_by_team_uses_dto_serializer_helpers(self):
        url = reverse("quality_data:kpi-aql-aql-by-team")
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
        """Returns 200 with global defect rate: SUM(defects_total)/SUM(accepted+rejected)*100."""
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
        """value equals SUM(defects_total) / SUM(accepted + rejected) * 100 for plant."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(url)
        agg = QualityQcFa.objects.aggregate(
            total_defects=Sum("defects_total"),
            total_accepted=Sum("accepted"),
            total_rejected=Sum("rejected"),
        )
        total_inspected = (agg["total_accepted"] or 0) + (agg["total_rejected"] or 0)
        expected = (
            round((agg["total_defects"] / total_inspected) * 100, 2)
            if total_inspected > 0
            else 0
        )
        self.assertEqual(response.data["value"], expected)

    def test_defect_rate_qfc_uses_accepted_plus_rejected(self):
        """QFC defect rate uses (accepted + rejected), not sample, as denominator."""
        # Create QFC record where accepted+rejected (100) differs from sample (200)
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustQFC",
            team=1, coord="C", po=100, style="S1", batch=1,
            color=self.color, qty=50, seconds=20, accepted=80, rejected=20,
            sample=200,  # sample differs from accepted+rejected=100
            defects_total=5, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Formula: defects / (accepted + rejected) * 100 = 5/100 * 100 = 5.0
        # Old (buggy) would be: 5/200 * 100 = 2.5
        self.assertEqual(response.data["value"], 5.0)

    def test_defect_rate_qfc_zero_denominator(self):
        """QFC with accepted+rejected=0 returns 0.0 without division error."""
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="CustQFCZero",
            team=2, coord="C", po=101, style="S2", batch=2,
            color=self.color, qty=0, seconds=0, accepted=0, rejected=0,
            sample=100,
            defects_total=3, aql=2.5, pass_or_fail="FAIL",
        )

        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 0.0)

    def test_defect_rate_qfa_uses_accepted_plus_rejected(self):
        """QFA plant records now use accepted+rejected as denominator for parity with QFC."""
        # Isolate test: remove existing QFA fixtures so aggregation is predictable
        QualityQcFa.objects.all().delete()

        # Create QFA record where accepted+rejected (50) differs from sample (100)
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustQFA",
            team=3, coord="C", po=102, style="S3", batch=3,
            color=self.color, qty=50, seconds=20, accepted=30, rejected=20,
            sample=100,  # sample=100, accepted+rejected=50
            defects_total=10, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-defect-rate")
        # Default context=plant for QFA
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Must use accepted+rejected (50), NOT sample (100)
        # Expected: 10/50 * 100 = 20.0
        self.assertAlmostEqual(response.data["value"], 20.0, places=2)


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
            ("quality_data:kpi-aql-aql-by-team", "data", {"label", "value"}),
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
            set(response.data.keys()),
            {"week", "team", "line_code", "style", "color", "size", "customer", "batch", "include_dual_lines_default"},
        )

        for key in ["week", "team", "style", "color", "size", "customer", "batch", "line_code"]:
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

    # ── Filter: date_range ───────────────────────────────

    def test_date_range_filter_works(self):
        """?date_range= filters defects by inspection date_1 range."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(
            f"{url}?date_range=2025-01-10,2025-01-11"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should narrow results to 2 records (weeks 1-2)
        self.assertGreater(len(response.data), 0)

    def test_date_range_filter_no_match_returns_empty(self):
        """?date_range=NONMATCHING returns empty list."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(
            f"{url}?date_range=2020-01-01,2020-01-02"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: week ─────────────────────────────────────

    def test_week_filter_works(self):
        """?week=1 filters to that inspection week only."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    # ── Filter: color ────────────────────────────────────

    def test_color_filter_no_match_returns_empty(self):
        """?color=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?color=purple")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: customer ─────────────────────────────────

    def test_customer_filter_works(self):
        """?customer=TestCustomer filters to matching customer records."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?customer=TestCustomer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_customer_filter_no_match_returns_empty(self):
        """?customer=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?customer=NONEXISTENT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: batch ────────────────────────────────────

    def test_batch_filter_works(self):
        """?batch=100 filters to matching inspection batch."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?batch=100")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_batch_filter_no_match_returns_empty(self):
        """?batch=99999 (non-existent) returns empty list."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?batch=99999")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


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

    # ── Filter: date_range ───────────────────────────────

    def test_date_range_filter_works(self):
        """?date_range= narrows trend data to matching date range."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(
            f"{url}?date_range=2025-01-10,2025-01-11"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_date_range_filter_no_match_returns_empty(self):
        """?date_range=NONMATCHING returns empty list."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(
            f"{url}?date_range=2020-01-01,2020-01-02"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: style ────────────────────────────────────

    def test_style_filter_works(self):
        """?style=Style-0 narrows to matching inspection style."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?style=Style-0")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_style_filter_no_match_returns_empty(self):
        """?style=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?style=NONEXISTENT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: team ─────────────────────────────────────

    def test_team_filter_works(self):
        """?team=1 filters to matching inspection team."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?team=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    # ── Filter: color ────────────────────────────────────

    def test_color_filter_no_match_returns_empty(self):
        """?color=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?color=purple")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: customer ─────────────────────────────────

    def test_customer_filter_works(self):
        """?customer=TestCustomer filters to matching customer."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?customer=TestCustomer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_customer_filter_no_match_returns_empty(self):
        """?customer=NONEXISTENT returns empty list."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?customer=NONEXISTENT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # ── Filter: batch ────────────────────────────────────

    def test_batch_filter_works(self):
        """?batch=100 filters to matching inspection batch."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?batch=100")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_batch_filter_no_match_returns_empty(self):
        """?batch=99999 (non-existent) returns empty list."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?batch=99999")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 3.1: Corrected acceptance-rate formula
# ─────────────────────────────────────────────────────────

class AcceptanceRateFormulaTest(TestCase):
    """Tests proving acceptance uses accepted/(accepted+rejected)*100, NOT sample."""

    def setUp(self):
        self.client = APIClient()
        self.color = Color.objects.create(name="formula_test", is_active=True)

    def test_performance_by_customer_uses_accepted_plus_rejected_denominator(self):
        """When sample differs from accepted+rejected, formula uses the latter."""
        # Create records where sample=100 but accepted+rejected=50
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustA",
            team=1, coord="C", po=100, style="S1", batch=1,
            color=self.color, qty=50, seconds=20, accepted=8, rejected=2,
            sample=100,  # sample is much larger than accepted+rejected
            defects_total=2, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        item = response.data[0]
        # Correct: 8/(8+2)*100 = 80.0
        # Buggy (old): 8/100*100 = 8.0
        self.assertEqual(item["value"], 80.0)

    def test_performance_by_line_uses_accepted_plus_rejected_denominator(self):
        """When sample differs from accepted+rejected, line formula uses the latter."""
        # Create records where sample=50 but accepted+rejected=30
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustB",
            team=5, coord="C", po=100, style="S2", batch=1,
            color=self.color, qty=30, seconds=15, accepted=9, rejected=1,
            sample=50,  # sample differs from accepted+rejected
            defects_total=1, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        item = response.data[0]
        # Correct: 9/(9+1)*100 = 90.0
        # Buggy (old): 9/50*100 = 18.0
        self.assertEqual(item["value"], 90.0)

    def test_performance_by_line_zero_denominator_safe(self):
        """When accepted+rejected=0, returns 0 without error."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustC",
            team=10, coord="C", po=100, style="S3", batch=1,
            color=self.color, qty=0, seconds=0, accepted=0, rejected=0,
            sample=0,
            defects_total=0, aql=0.0, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        item = response.data[0]
        self.assertEqual(item["value"], 0)

    def test_performance_by_customer_zero_denominator_safe(self):
        """When accepted+rejected=0 in customer endpoint, returns 0."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustD",
            team=10, coord="C", po=100, style="S4", batch=1,
            color=self.color, qty=0, seconds=0, accepted=0, rejected=0,
            sample=0,
            defects_total=0, aql=0.0, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        item = response.data[0]
        self.assertEqual(item["value"], 0)


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 3.2: Line sanitization in live endpoints
# ─────────────────────────────────────────────────────────

class LineSanitizationLiveTest(TestCase):
    """Tests proving out-of-range teams are handled in live line-based KPIs.

    Design: canonicalize 60→6, filter out 0 and out-of-range, keep 1..36.
    """

    def setUp(self):
        self.client = APIClient()
        self.color = Color.objects.create(name="sanitize_live", is_active=True)

    def test_performance_by_line_canonicalizes_60_to_6(self):
        """Team=60 maps to line 6; 0 excluded; valid 1,36 preserved."""
        for team in [1, 0, 36, 60]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="CustX",
                team=team, coord="C", po=100, style="SX", batch=1,
                color=self.color, qty=50, seconds=20, accepted=40, rejected=10,
                sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        teams = {item["label"] for item in response.data}
        self.assertEqual(teams, {"1", "6", "36"})
        self.assertNotIn("0", teams)
        self.assertNotIn("60", teams)

    def test_performance_by_line_all_valid_teams_preserved(self):
        """When all teams are valid (1..36), none are filtered out."""
        for team in [5, 15, 25]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="CustY",
                team=team, coord="C", po=100, style="SY", batch=1,
                color=self.color, qty=50, seconds=20, accepted=40, rejected=10,
                sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_performance_by_line_60_contributes_to_line_6_rate(self):
        """Team=60's accepted/rejected rolls into line 6's acceptance rate."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="Cust60",
            team=6, coord="C", po=100, style="S6", batch=1,
            color=self.color, qty=50, seconds=20, accepted=80, rejected=20,
            sample=100,
            defects_total=5, aql=2.5, pass_or_fail="PASS",
        )
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="Cust60",
            team=60, coord="C", po=101, style="S60", batch=2,
            color=self.color, qty=30, seconds=10, accepted=15, rejected=5,
            sample=20,
            defects_total=2, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        line_6 = next(item for item in response.data if item["label"] == "6")
        # Combined: accepted=80+15=95, rejected=20+5=25
        # Rate = 95/(95+25)*100 = 79.17
        self.assertAlmostEqual(line_6["value"], 79.17, places=1)

    def test_performance_by_customer_not_affected_by_team_sanitization(self):
        """performance_by_customer should NOT filter by team range — metric-scoped only."""
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01", week=10, customer="CustZ",
            team=60,  # invalid team — but customer endpoint shouldn't filter it
            coord="C", po=100, style="SZ", batch=1,
            color=self.color, qty=50, seconds=20, accepted=8, rejected=2,
            sample=100,
            defects_total=2, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        # Customer endpoint groups by customer, not team. Invalid teams should
        # NOT be filtered from customer views — sanitization is metric-scoped.
        self.assertGreaterEqual(len(response.data), 1)

    def test_performance_by_line_context_customer_excludes_0(self):
        """QFC context + team=0: excluded from line output (empty result)."""
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=10, customer="QCust",
            team=0,  # invalid — should be excluded from line output
            coord="C", po=100, style="SZ", batch=1,
            color=self.color, qty=50, seconds=20, accepted=40, rejected=10,
            sample=50,
            defects_total=2, aql=2.5, pass_or_fail="PASS",
        )

        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        teams = {item["label"] for item in response.data}
        self.assertNotIn("0", teams)

    def test_ac_re_rate_by_line_canonicalizes_60_to_6(self):
        """ac_re_rate_by_line: team=60 contributes to line 6, team=0 excluded."""
        import random
        for team, pof in [(1, "PASS"), (0, "PASS"), (60, "REJECT"), (60, "PASS"), (36, "PASS")]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="CustAC",
                team=team, coord="C1", po=random.randint(200, 999),
                style="SAC", batch=random.randint(1, 10),
                color=self.color, qty=50, seconds=20,
                accepted=40, rejected=10, sample=50,
                defects_total=2, aql=2.5, pass_or_fail=pof,
            )

        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"]: item["value"] for item in response.data}
        # Team 1 → "1 - PASS"
        self.assertIn("1 - PASS", labels)
        # Team 60 (2 records) → "6 - REJECT" and "6 - PASS"
        self.assertIn("6 - REJECT", labels)
        self.assertIn("6 - PASS", labels)
        # Team 0 excluded
        zero_labels = [l for l in labels if l.startswith("0 -")]
        self.assertEqual(zero_labels, [])
        # Team 60 never appears raw
        sixty_labels = [l for l in labels if l.startswith("60 -")]
        self.assertEqual(sixty_labels, [])

    def test_ac_re_rate_aggregates_60_and_6_into_same_bucket(self):
        """Line 6 aggregates both team=6 and canonicalized team=60 records."""
        import random
        # team=6 PASS, team=60 PASS → both contribute to "6 - PASS"
        for team in [6, 60]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="CustAC",
                team=team, coord="C1", po=random.randint(200, 999),
                style="SAC", batch=random.randint(1, 10),
                color=self.color, qty=50, seconds=20,
                accepted=40, rejected=10, sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"]: item["value"] for item in response.data}
        # Both records contribute to "6 - PASS" → count should be 2
        self.assertEqual(labels["6 - PASS"], 2)


# ─────────────────────────────────────────────────────────
# Slice 2: Dual-Line KPI + Filter Contract Tests
# ─────────────────────────────────────────────────────────

class DualLineTestMixin:
    """Mixin that creates QFC records with simple and dual lines for dual-line KPI tests."""

    def setUp(self):
        self.client = APIClient()
        self.color = Color.objects.create(name="dual_test", is_active=True)

        # Simple QFC line 35
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=12, customer="DualCust",
            team=35, coord="C", po=100, style="DualStyle", batch=10,
            color=self.color, qty=50, seconds=20, accepted=40, rejected=10,
            sample=50, defects_total=3, aql=2.5, pass_or_fail="PASS",
            line_code=None,
        )

        # Dual QFC line 35-36
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=12, customer="DualCust",
            team=35, coord="C", po=101, style="DualStyle", batch=11,
            color=self.color, qty=50, seconds=20, accepted=30, rejected=20,
            sample=50, defects_total=5, aql=2.5, pass_or_fail="REJECT",
            line_code="35-36",
        )

        # Another simple QFC line 20 (unrelated)
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=12, customer="DualCust",
            team=20, coord="C", po=200, style="OtherStyle", batch=20,
            color=self.color, qty=50, seconds=20, accepted=45, rejected=5,
            sample=50, defects_total=2, aql=2.5, pass_or_fail="PASS",
            line_code=None,
        )

        # Dual line 15-16
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-03-01", week=12, customer="DualCust",
            team=15, coord="C", po=150, style="DualStyle2", batch=15,
            color=self.color, qty=50, seconds=20, accepted=35, rejected=15,
            sample=50, defects_total=4, aql=2.5, pass_or_fail="REJECT",
            line_code="15-16",
        )


class DualLinePerformanceByLineTest(DualLineTestMixin, TestCase):
    """Tests dual-line behavior in performance-by-line endpoint."""

    def test_default_excludes_dual_lines(self):
        """Without include_dual_lines, only simple lines appear (backward compat)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        # Simple lines: 35 (team=35, line_code=NULL) and 20 (team=20)
        self.assertIn("35", labels)
        self.assertIn("20", labels)
        # Dual lines excluded
        self.assertNotIn("35-36", labels)
        self.assertNotIn("15-16", labels)

    def test_explicit_false_excludes_dual_lines(self):
        """include_dual_lines=false explicitly hides dual lines."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=false")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        self.assertNotIn("35-36", labels)
        self.assertNotIn("15-16", labels)
        self.assertIn("35", labels)
        self.assertIn("20", labels)

    def test_include_dual_lines_shows_dual_labels(self):
        """include_dual_lines=true includes dual lines with exact labels."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        self.assertIn("35-36", labels)
        self.assertIn("15-16", labels)
        self.assertIn("35", labels)
        self.assertIn("20", labels)

    def test_dual_and_simple_are_separate_buckets(self):
        """Simple line 35 and dual line 35-36 are independent entries."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        lookup = {item["label"]: item["value"] for item in response.data}
        # Simple 35: accepted=40, rejected=10 → 40/50*100 = 80.0
        self.assertAlmostEqual(lookup["35"], 80.0, places=1)
        # Dual 35-36: accepted=30, rejected=20 → 30/50*100 = 60.0
        self.assertAlmostEqual(lookup["35-36"], 60.0, places=1)
        # They must be distinct entries
        self.assertIn("35", lookup)
        self.assertIn("35-36", lookup)

    def test_dual_line_exact_label(self):
        """Dual line label is exactly the line_code value, not team number."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        # Exact imported label, not derived from team
        self.assertIn("15-16", labels)
        self.assertIn("35-36", labels)


class DualLineAcReRateTest(DualLineTestMixin, TestCase):
    """Tests dual-line behavior in ac-re-rate-by-line endpoint."""

    def test_default_excludes_dual_lines(self):
        """Without include_dual_lines, only simple lines appear in ac-re-rate."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        # Simple lines only
        self.assertIn("35 - PASS", labels)
        self.assertIn("20 - PASS", labels)
        # No dual lines
        dual_labels = [l for l in labels if "35-36" in l or "15-16" in l]
        self.assertEqual(dual_labels, [])

    def test_include_dual_lines_shows_dual_entries(self):
        """include_dual_lines=true shows dual lines with exact labels + pof."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"]: item["value"] for item in response.data}
        self.assertIn("35-36 - REJECT", labels)
        self.assertIn("15-16 - REJECT", labels)
        self.assertIn("35 - PASS", labels)


class DualLineAqlByTeamTest(DualLineTestMixin, TestCase):
    """Tests dual-line behavior in aql-by-team endpoint."""

    def test_default_excludes_dual_lines(self):
        """Without include_dual_lines, aql-by-team only shows simple lines."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data["data"]}
        self.assertIn("35", labels)
        self.assertIn("20", labels)
        self.assertNotIn("35-36", labels)
        self.assertNotIn("15-16", labels)

    def test_include_dual_lines_shows_dual_labels(self):
        """include_dual_lines=true includes dual-line AQL entries."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data["data"]}
        self.assertIn("35-36", labels)
        self.assertIn("15-16", labels)
        self.assertIn("35", labels)


class DualLineNonLineKpiParityTest(DualLineTestMixin, TestCase):
    """Tests that non-line-grouped QualityQcFa KPIs now respect the global dual-line toggle.

    Before the global filter was centralized, these tests asserted *no change*
    between OFF and ON.  After centralization the toggle is a queryset-level
    semantic filter, so the OFF variant excludes dual-line rows from KPI
    calculations and the ON variant includes them.
    """

    # ── Pass/Reject Distribution ────────────────────────

    def test_pass_reject_changes_with_include_dual_lines(self):
        """OFF vs ON produce different pass/reject counts when dual rows exist."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        off = self.client.get(f"{url}?context=customer")
        on = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        off_total = sum(item["value"] for item in off.data)
        on_total = sum(item["value"] for item in on.data)
        self.assertNotEqual(off_total, on_total)

    def test_pass_reject_off_excludes_dual_rows(self):
        """OFF: only simple-line rows contribute (2 records)."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)
        by_name = {item["name"]: item["value"] for item in response.data}
        self.assertEqual(by_name.get("PASS", 0), 2)
        self.assertEqual(by_name.get("REJECT", 0), 0)

    def test_pass_reject_on_includes_dual_rows(self):
        """ON: all 4 rows contribute, including dual REJECT rows."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 4)
        by_name = {item["name"]: item["value"] for item in response.data}
        self.assertEqual(by_name.get("PASS", 0), 2)
        self.assertEqual(by_name.get("REJECT", 0), 2)

    # ── Performance by Customer ─────────────────────────

    def test_performance_by_customer_changes_with_include_dual_lines(self):
        """OFF vs ON produce different customer acceptance rates."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        off = self.client.get(f"{url}?context=customer")
        on = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        self.assertNotEqual(off.data, on.data)

    def test_performance_by_customer_off_excludes_dual_contributions(self):
        """OFF: rate computed from simple rows only (acc=85, rej=15 → 85.0%)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertAlmostEqual(response.data[0]["value"], 85.0, places=1)

    def test_performance_by_customer_on_includes_dual_contributions(self):
        """ON: rate includes dual rows (acc=150, rej=50 → 75.0%)."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertAlmostEqual(response.data[0]["value"], 75.0, places=1)

    # ── Defect Rate ─────────────────────────────────────

    def test_defect_rate_changes_with_include_dual_lines(self):
        """OFF vs ON produce different global defect rates."""
        url = reverse("quality_data:kpi-defect-rate")
        off = self.client.get(f"{url}?context=customer")
        on = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        self.assertNotEqual(off.data["value"], on.data["value"])

    def test_defect_rate_off_excludes_dual_rows(self):
        """OFF: defects=5 / sample=100 → 5.0% (simple rows only)."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 5.0)

    def test_defect_rate_on_includes_dual_rows(self):
        """ON: defects=14 / sample=200 → 7.0% (all rows)."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 7.0)

    # ── Explicit line_code still works ──────────────────

    def test_line_code_param_does_not_break_defect_rate(self):
        """Explicit line_code returns a valid scalar response (no 500)."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer&line_code=35-36")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("value", response.data)
        # When line_code=35-36 the explicit filter overrides the global default,
        # so only the single dual row 35-36 contributes.
        # defects=5, sample=50 → 10.0%
        self.assertEqual(response.data["value"], 10.0)


class DualLineFilterOptionsTest(DualLineTestMixin, TestCase):
    """Tests that filter-options endpoint exposes dual-line metadata."""

    def test_filter_options_includes_line_code_field(self):
        """Filter options response includes line_code key."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("line_code", response.data)

    def test_filter_options_includes_include_dual_lines_default(self):
        """Filter options response includes include_dual_lines_default metadata."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("include_dual_lines_default", response.data)
        # Default should be true (available) when dual lines exist
        self.assertIsInstance(response.data["include_dual_lines_default"], bool)

    def test_team_only_has_simple_numeric_lines(self):
        """team field in filter options contains only simple numeric lines — no dual labels."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        teams = response.data["team"]
        # Only valid 1..36 simple lines
        for t in teams:
            self.assertIsInstance(t, int)
            self.assertGreaterEqual(t, 1)
            self.assertLessEqual(t, 36)

    def test_line_code_contains_dual_labels(self):
        """line_code field contains dual-line labels like '15-16' and '35-36'."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        line_codes = response.data["line_code"]
        self.assertIsInstance(line_codes, list)
        self.assertIn("15-16", line_codes)
        self.assertIn("35-36", line_codes)

    def test_line_code_empty_when_no_dual_data(self):
        """line_code is empty list when no dual lines exist in context."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        line_codes = response.data["line_code"]
        self.assertEqual(line_codes, [])

    def test_include_dual_lines_default_true_when_duals_exist(self):
        """include_dual_lines_default is true when dual lines exist in context."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(response.data["include_dual_lines_default"])

    def test_include_dual_lines_default_false_when_no_duals(self):
        """include_dual_lines_default is false when no dual lines exist."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertFalse(response.data["include_dual_lines_default"])


class DualLineFilterParamTest(DualLineTestMixin, TestCase):
    """Tests line_code filter parameter for exact dual-line matching."""

    def test_line_code_filter_returns_only_matching_dual(self):
        """?line_code=35-36 returns only the dual line with that exact code."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(
            f"{url}?context=customer&include_dual_lines=true&line_code=35-36"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"35-36"})

    def test_line_code_filter_combines_with_team_filter(self):
        """line_code filter coexists with other filters."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(
            f"{url}?context=customer&include_dual_lines=true&team=35&line_code=35-36"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # team=35 + line_code=35-36 filters to the dual row with team=35 AND line_code=35-36
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"35-36"})

    def test_line_code_filter_no_match_returns_empty(self):
        """?line_code=NONEXISTENT returns empty results."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(
            f"{url}?context=customer&include_dual_lines=true&line_code=99-100"
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [])


# ─────────────────────────────────────────────────────────
# Phase 3 — Global Dual-Line Toggle Contract Verification
# ─────────────────────────────────────────────────────────

class DualLineToggleContractTest(DualLineTestMixin, TestCase):
    """Backward-compatible toggle semantics and edge cases (Tasks 3.1, 3.2)."""

    # ── Malformed / missing toggle defaults to OFF ──────

    def test_missing_toggle_defaults_to_off(self):
        """When include_dual_lines is omitted, dual-line rows are excluded."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)  # Only simple lines

    def test_empty_toggle_defaults_to_off(self):
        """include_dual_lines= (empty) defaults to OFF."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)

    def test_false_toggle_excludes_dual_rows(self):
        """include_dual_lines=false explicitly excludes dual rows."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=false")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)

    def test_truthy_but_not_true_defaults_to_off(self):
        """include_dual_lines=1 or =yes defaults to OFF (only 'true' enables)."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        for bogus in ("1", "yes", "YES", "on"):
            response = self.client.get(
                f"{url}?context=customer&include_dual_lines={bogus}"
            )
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            total = sum(item["value"] for item in response.data)
            self.assertEqual(total, 2, f"bogus value '{bogus}' should default to OFF")

    def test_true_enables_dual_rows(self):
        """Only include_dual_lines=true includes dual rows."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 4)

    # ── No-op when no dual-line rows exist ──────────────

    def test_non_line_kpi_noop_when_no_dual_rows(self):
        """OFF == ON when the scoped dataset has zero dual-line rows."""
        # Create a pure simple-line customer dataset
        from quality_data.models import Color as ColorModel
        c = ColorModel.objects.create(name="noop_dual", is_active=True)
        for i in range(3):
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1=f"2025-06-{i + 10:02d}",
                week=30 + i,
                customer="NoDualCust",
                team=i + 1,
                coord="C",
                po=300 + i,
                style=f"NoDualStyle-{i}",
                batch=300 + i,
                color=c,
                qty=50,
                seconds=20,
                accepted=40,
                rejected=10,
                sample=50,
                defects_total=2,
                aql=2.5,
                pass_or_fail="PASS" if i % 2 == 0 else "REJECT",
                line_code=None,  # no dual rows
            )

        url = reverse("quality_data:kpi-pass-reject-distribution")
        off = self.client.get(f"{url}?customer=NoDualCust")
        on = self.client.get(f"{url}?customer=NoDualCust&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        self.assertEqual(off.data, on.data)

    def test_non_line_kpi_noop_defect_rate_when_no_duals(self):
        """Defect rate OFF == ON when dataset has no dual-line rows."""
        url = reverse("quality_data:kpi-defect-rate")
        off = self.client.get(f"{url}?customer=NoDualCust")
        on = self.client.get(f"{url}?customer=NoDualCust&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        self.assertEqual(off.data["value"], on.data["value"])


class DualLineGlobalToggleLineGroupedTest(DualLineTestMixin, TestCase):
    """Prove line-grouped endpoints still honor OFF/ON through the shared filter (Task 3.3)."""

    def test_line_grouped_excludes_dual_when_off_through_shared_filter(self):
        """OFF → get_filtered_queryset excludes dual rows before grouping."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertNotIn("35-36", labels)
        self.assertNotIn("15-16", labels)
        self.assertIn("35", labels)
        self.assertIn("20", labels)

    def test_line_grouped_includes_dual_when_on_through_shared_filter(self):
        """ON → get_filtered_queryset keeps dual rows; display labels them correctly."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertIn("35-36", labels)
        self.assertIn("15-16", labels)
        self.assertIn("35", labels)

    def test_ac_re_rate_honors_global_toggle_off(self):
        """ac-re-rate-by-line OFF excludes dual entries via shared filter."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        dual_labels = [item["label"] for item in response.data if "-" in item["label"].split(" - ")[0]]
        # Only simple labels like "35 - PASS"; no "35-36 - REJECT"
        self.assertEqual(dual_labels, [])

    def test_ac_re_rate_honors_global_toggle_on(self):
        """ac-re-rate-by-line ON includes dual entries via shared filter."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data]
        self.assertIn("35-36 - REJECT", labels)
        self.assertIn("15-16 - REJECT", labels)

    def test_aql_by_team_honors_global_toggle(self):
        """aql-by-team OFF vs ON differ via shared filter."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        off = self.client.get(f"{url}?context=customer")
        on = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(off.status_code, http_status.HTTP_200_OK)
        self.assertEqual(on.status_code, http_status.HTTP_200_OK)
        off_labels = {item["label"] for item in off.data["data"]}
        on_labels = {item["label"] for item in on.data["data"]}
        self.assertNotIn("35-36", off_labels)
        self.assertIn("35-36", on_labels)


class DualLineInspectionDefectToggleTest(DualLineTestMixin, TestCase):
    """Prove the global toggle also filters prefixed InspectionDefect querysets."""

    def setUp(self):
        super().setUp()
        # Create InspectionDefect records linked to the dual-line QFC rows
        self.defect_type = DefectType.objects.create(name="dual-defect", is_active=True)
        for qc in QualityQcFa.objects.filter(
            table_type="QFC", customer="DualCust", week=12
        ):
            InspectionDefect.objects.create(
                inspection=qc,
                defect_type=self.defect_type,
                amount=3 if qc.line_code else 2,
            )

    def test_top_defects_off_excludes_dual_inspections(self):
        """OFF → inspection__line_code IS NULL → only simple-line defects."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        # 2 simple rows × amount=2 = 4
        self.assertEqual(total, 4)

    def test_top_defects_on_includes_dual_inspections(self):
        """ON → dual-line inspection defects are included."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?context=customer&include_dual_lines=true")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        # 4 rows: 2 simple × 2 + 2 dual × 3 = 10
        self.assertEqual(total, 10)
