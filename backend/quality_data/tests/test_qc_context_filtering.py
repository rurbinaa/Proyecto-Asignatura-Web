"""
Tests for QC context filtering (Phase 1 of refactor-multisheet-dashboard).

Verifies that the `context` query parameter correctly isolates QFA (Plant)
vs QFC (Customer) data across all QualityQcFa-based KPI and filter endpoints.

Covers:
  - AQL endpoints (AqlKpiViewSet): aql-by-style, aql-weekly, audited-pieces
  - Rendimiento endpoints (KpiViewSet): ac-re-rate-by-line, performance-by-customer, performance-by-line
  - Defect endpoints: top-defects, defects-by-style-type (via InspectionDefect FK)
  - Operativos endpoints: pass-reject-distribution, rejected-evolution, defect-rate
  - Filter options endpoint
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status
from quality_data.models import (
    QualityQcFa,
    InspectionDefect,
    Color,
    DefectType,
)


class QcContextFilteringMixin:
    """Mixin that creates QFA and QFC test records for context isolation tests."""

    def setUp(self):
        self.client = APIClient()

        # Shared fixtures
        self.color = Color.objects.create(name="red", is_active=True)
        self.defect_type = DefectType.objects.create(name="loose thread", is_active=True)

        # Plant records (QFA) — 3 records
        for i in range(3):
            qc = QualityQcFa.objects.create(
                table_type="QFA",
                date_1=f"2025-01-{i + 10:02d}",
                week=i + 1,
                customer="PlantCustomer",
                team=10 + i,
                coord="COORD_PLANT",
                po=100 + i,
                style=f"Plant-Style-{i}",
                batch=100 + i,
                color=self.color,
                qty=100,
                seconds=50,
                accepted=90,
                rejected=10,
                sample=100,
                defects_total=3 + i,
                aql=2.5,
                pass_or_fail="PASS" if i % 2 == 0 else "REJECT",
            )
            InspectionDefect.objects.create(
                inspection=qc,
                defect_type=self.defect_type,
                amount=2,
            )

        # Customer records (QFC) — 2 records
        for i in range(2):
            qc = QualityQcFa.objects.create(
                table_type="QFC",
                date_1=f"2025-02-{i + 10:02d}",
                week=5 + i,
                customer="CustCustomer",
                team=20 + i,
                coord="COORD_CUST",
                po=200 + i,
                style=f"Cust-Style-{i}",
                batch=200 + i,
                color=self.color,
                qty=100,
                seconds=40,
                accepted=80,
                rejected=20,
                sample=100,
                defects_total=5 + i,
                aql=2.5,
                pass_or_fail="FAIL" if i % 2 == 0 else "PASS",
            )
            InspectionDefect.objects.create(
                inspection=qc,
                defect_type=self.defect_type,
                amount=3,
            )


# ─────────────────────────────────────────────────────────
# AQL endpoints — context filtering
# ─────────────────────────────────────────────────────────

class AqlByStyleContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/aql/aql-by-style/"""

    def test_context_plant_returns_only_qfa_styles(self):
        """?context=plant returns only Plant-Style-* entries."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 3)
        for label in labels:
            self.assertIn("Plant-Style", label)

    def test_context_customer_returns_only_qfc_styles(self):
        """?context=customer returns only Cust-Style-* entries."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 2)
        for label in labels:
            self.assertIn("Cust-Style", label)

    def test_default_no_context_returns_plant_data(self):
        """When context is omitted, default to plant (QFA) — backward compat."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 3)
        for label in labels:
            self.assertIn("Plant-Style", label)


class AqlWeeklyContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/aql/aql-weekly/"""

    def test_context_customer_returns_only_qfc_weeks(self):
        """?context=customer returns only QFC week data (weeks 5-6)."""
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        aql_series = response.data["data"][0]["data"]
        weeks = {point["x"] for point in aql_series}
        self.assertEqual(weeks, {5, 6})

    def test_context_plant_returns_only_qfa_weeks(self):
        """?context=plant returns only QFA week data (weeks 1-3)."""
        url = reverse("quality_data:kpi-aql-aql-weekly")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        aql_series = response.data["data"][0]["data"]
        weeks = {point["x"] for point in aql_series}
        self.assertEqual(weeks, {1, 2, 3})


class AuditedPiecesContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/aql/audited-pieces/"""

    def test_context_customer_isolates_qfc_only(self):
        """?context=customer sums sample only from QFC records."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        pieces_data = response.data["data"][0]["data"]
        weeks = {point["x"] for point in pieces_data}
        self.assertEqual(weeks, {5, 6})


class AqlByTeamContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/aql/aql-by-team/"""

    def test_context_plant_returns_only_qfa_teams(self):
        """?context=plant returns only QFA team data (teams 10-12)."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 3)
        for label in labels:
            self.assertIn(label, {"10", "11", "12"})

    def test_context_customer_returns_only_qfc_teams(self):
        """?context=customer returns only QFC team data (teams 20-21)."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 2)
        for label in labels:
            self.assertIn(label, {"20", "21"})

    def test_default_no_context_returns_plant_data(self):
        """When context is omitted, default to plant (QFA) data."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        self.assertEqual(len(labels), 3)
        for label in labels:
            self.assertIn(label, {"10", "11", "12"})

    def test_context_customer_excludes_qfa_only_teams(self):
        """?context=customer must NOT include QFA-only teams."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        # QFA teams (10, 11, 12) should be absent
        for label in labels:
            self.assertNotIn(label, {"10", "11", "12"})

    def test_invalid_context_returns_400(self):
        """An invalid context value returns HTTP 400 for aql-by-team."""
        url = reverse("quality_data:kpi-aql-aql-by-team")
        response = self.client.get(f"{url}?context=invalid")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("context", response.data)


# ─────────────────────────────────────────────────────────
# Rendimiento endpoints — context filtering
# ─────────────────────────────────────────────────────────

class AcReRateByLineContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/rendimiento/ac-re-rate-by-line/"""

    def test_context_customer_returns_only_qfc_teams(self):
        """?context=customer only returns teams from QFC records."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        teams = {int(item["label"].split(" - ")[0]) for item in response.data}
        self.assertEqual(teams, {20, 21})

    def test_context_plant_returns_only_qfa_teams(self):
        """?context=plant only returns teams from QFA records."""
        url = reverse("quality_data:kpi-rendimiento-ac-re-rate-by-line")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        teams = {int(item["label"].split(" - ")[0]) for item in response.data}
        self.assertEqual(teams, {10, 11, 12})


class PerformanceByCustomerContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/rendimiento/performance-by-customer/"""

    def test_context_customer_returns_only_qfc_customers(self):
        """?context=customer returns only CustCustomer."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        customers = {item["label"] for item in response.data}
        self.assertEqual(customers, {"CustCustomer"})

    def test_context_plant_returns_only_qfa_customers(self):
        """?context=plant returns only PlantCustomer."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-customer")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        customers = {item["label"] for item in response.data}
        self.assertEqual(customers, {"PlantCustomer"})


class PerformanceByLineContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/rendimiento/performance-by-line/"""

    def test_context_customer_isolates_qfc_lines(self):
        """?context=customer only shows team 20 and 21."""
        url = reverse("quality_data:kpi-rendimiento-performance-by-line")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        teams = {item["label"] for item in response.data}
        self.assertEqual(teams, {"20", "21"})


# ─────────────────────────────────────────────────────────
# Defectos endpoints — context filtering (via InspectionDefect FK)
# ─────────────────────────────────────────────────────────

class TopDefectsContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/top-defects/ (InspectionDefect-based)."""

    def test_context_customer_returns_only_qfc_defects(self):
        """?context=customer returns only defects from QFC inspections."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFC has 2 records × amount=3 = 6 total for "loose thread"
        total_value = sum(item["value"] for item in response.data)
        self.assertEqual(total_value, 6)

    def test_context_plant_returns_only_qfa_defects(self):
        """?context=plant returns only defects from QFA inspections."""
        url = reverse("quality_data:kpi-top-defects")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFA has 3 records × amount=2 = 6 total for "loose thread"
        total_value = sum(item["value"] for item in response.data)
        self.assertEqual(total_value, 6)


class DefectsByStyleTypeContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/defects-by-style-type/ (InspectionDefect-based)."""

    def test_context_customer_returns_only_qfc_defects(self):
        """?context=customer returns only QFC inspection defects."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertIn("Cust-Style", item["x"])

    def test_context_plant_returns_only_qfa_defects(self):
        """?context=plant returns only QFA inspection defects."""
        url = reverse("quality_data:kpi-defects-by-style-type")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertIn("Plant-Style", item["x"])


# ─────────────────────────────────────────────────────────
# Operativos endpoints — context filtering
# ─────────────────────────────────────────────────────────

class PassRejectDistributionContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/pass-reject-distribution/"""

    def test_context_customer_returns_only_qfc_counts(self):
        """?context=customer counts only QFC pass/reject records."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 2)  # Only 2 QFC records

    def test_default_returns_qfa_data(self):
        """Without context, returns QFA (plant) data — backward compat."""
        url = reverse("quality_data:kpi-pass-reject-distribution")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        total = sum(item["value"] for item in response.data)
        self.assertEqual(total, 3)  # Only 3 QFA records


class RejectedEvolutionContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/rejected-evolution/"""

    def test_context_customer_isolates_qfc_weeks(self):
        """?context=customer returns only QFC week data."""
        url = reverse("quality_data:kpi-rejected-evolution")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.data[0]["data"]
        weeks = {point["x"] for point in data}
        self.assertEqual(weeks, {5, 6})


class DefectRateContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/defect-rate/"""

    def test_context_customer_calculates_from_qfc_only(self):
        """?context=customer computes defect rate from QFC records only."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFC: defects=(5+6)=11, sample=(100+100)=200 → rate = 5.5%
        self.assertEqual(response.data["value"], 5.5)

    def test_context_plant_calculates_from_qfa_only(self):
        """?context=plant computes defect rate from QFA records only."""
        url = reverse("quality_data:kpi-defect-rate")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFA: defects=(3+4+5)=12, sample=(100+100+100)=300 → rate = 4.0%
        self.assertEqual(response.data["value"], 4.0)


class DefectCompositionContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /quality/kpis/defect-composition/"""

    def test_context_plant_returns_only_qfa_defect_types(self):
        """?context=plant returns defect composition from QFA inspections only."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFA data: 3 records × 2 amount = 6 total for "loose thread"
        names = {item["name"] for item in response.data}
        self.assertIn("loose thread", names)

    def test_context_customer_returns_only_qfc_defect_types(self):
        """?context=customer returns defect composition from QFC inspections only."""
        url = reverse("quality_data:kpi-defect-composition")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # QFC data: 2 records × 3 amount = 6 total for "loose thread"
        names = {item["name"] for item in response.data}
        self.assertIn("loose thread", names)

    def test_context_plant_isolates_from_customer(self):
        """Plant and customer compositions are fully isolated."""
        url = reverse("quality_data:kpi-defect-composition")

        plant_response = self.client.get(f"{url}?context=plant")
        plant_values = {item["name"]: item["value"] for item in plant_response.data}
        plant_loose = plant_values.get("loose thread", 0)

        cust_response = self.client.get(f"{url}?context=customer")
        cust_values = {item["name"]: item["value"] for item in cust_response.data}
        cust_loose = cust_values.get("loose thread", 0)

        # QFA: 3 records × 2 = 6
        # QFC: 2 records × 3 = 6
        # They happen to be equal in this test, but they come from different records
        self.assertEqual(plant_loose, 6)
        self.assertEqual(cust_loose, 6)


class DefectTrendTop3ContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /quality/kpis/defect-trend-top-3/"""

    def test_context_plant_returns_only_qfa_weeks(self):
        """?context=plant returns trend data with only QFA weeks (1-3)."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for series in response.data:
            weeks = {point["x"] for point in series["data"]}
            self.assertTrue(weeks.issubset({1, 2, 3}))

    def test_context_customer_returns_only_qfc_weeks(self):
        """?context=customer returns trend data with only QFC weeks (5-6)."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for series in response.data:
            weeks = {point["x"] for point in series["data"]}
            self.assertTrue(weeks.issubset({5, 6}))

    def test_context_customer_no_qfa_weeks(self):
        """?context=customer does not include any QFA week data."""
        url = reverse("quality_data:kpi-defect-trend-top-3")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for series in response.data:
            weeks = {point["x"] for point in series["data"]}
            # QFA weeks 1,2,3 should NOT be in customer data
            self.assertFalse({1, 2, 3} & weeks)


# ─────────────────────────────────────────────────────────
# Filter Options — context filtering
# ─────────────────────────────────────────────────────────

class FilterOptionsContextTest(QcContextFilteringMixin, TestCase):
    """Tests context filtering on GET /api/kpis/filter-options/"""

    def test_context_customer_returns_only_qfc_filter_options(self):
        """?context=customer returns filter options from QFC records only."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=customer")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("style", response.data)
        qfc_styles = [s for s in response.data["style"] if "Cust-Style" in s]
        self.assertEqual(len(qfc_styles), 2)
        # Should not contain Plant styles
        plant_styles = [s for s in response.data["style"] if "Plant-Style" in s]
        self.assertEqual(len(plant_styles), 0)

    def test_context_plant_returns_only_qfa_filter_options(self):
        """?context=plant returns filter options from QFA records only."""
        url = reverse("quality_data:kpi-filter-options")
        response = self.client.get(f"{url}?context=plant")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        styles = response.data["style"]
        plant_styles = [s for s in styles if "Plant-Style" in s]
        self.assertEqual(len(plant_styles), 3)
        cust_styles = [s for s in styles if "Cust-Style" in s]
        self.assertEqual(len(cust_styles), 0)


# ─────────────────────────────────────────────────────────
# Context combined with other filters — composition
# ─────────────────────────────────────────────────────────

class ContextWithWeekFilterTest(QcContextFilteringMixin, TestCase):
    """Tests context + week filter composition."""

    def test_context_plant_and_week_filter_compose(self):
        """?context=plant&week=1 returns only QFA week 1 data."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?context=plant&week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.data["data"][0]["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["x"], 1)

    def test_context_customer_and_week_filter_compose(self):
        """?context=customer&week=5 returns only QFC week 5 data."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?context=customer&week=5")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        data = response.data["data"][0]["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["x"], 5)

    def test_context_customer_and_non_matching_week_returns_empty(self):
        """?context=customer&week=1 returns empty — QFC has no week 1."""
        url = reverse("quality_data:kpi-aql-audited-pieces")
        response = self.client.get(f"{url}?context=customer&week=1")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])


# ─────────────────────────────────────────────────────────
# Invalid context — validation
# ─────────────────────────────────────────────────────────

class InvalidContextTest(TestCase):
    """Tests that invalid context values are rejected with validation errors."""

    def setUp(self):
        self.client = APIClient()

    def test_invalid_context_value_returns_400(self):
        """An unsupported context value returns 400 Bad Request."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=invalid")
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("context", response.data)

    def test_empty_context_value_is_treated_as_default_plant(self):
        """Empty context string falls back to plant (QFA)."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should not crash — treats empty as default

    def test_context_is_case_insensitive(self):
        """?context=PLANT (uppercase) is normalized to lowercase and accepted."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=PLANT")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should still return QFA data (plant)
        labels = [item["label"] for item in response.data["data"]]
        for label in labels:
            self.assertIn("Plant-Style", label)

    def test_context_customer_uppercase_normalized(self):
        """?context=CUSTOMER (mixed case) is normalized and returns QFC data."""
        url = reverse("quality_data:kpi-aql-aql-by-style")
        response = self.client.get(f"{url}?context=CUSTOMER")
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = [item["label"] for item in response.data["data"]]
        for label in labels:
            self.assertIn("Cust-Style", label)
