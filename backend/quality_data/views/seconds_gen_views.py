"""
SecondsGeneral analytics endpoints (Phase 2 of refactor-multisheet-dashboard).

Uses Django ORM `.values().annotate()` to compute 4 analytics exclusively
from SecondsGeneral and SecondsGeneralDefect data sources:

  - defects-by-customer: Group by SecondsGeneral.customer, SUM(defect amounts)
  - defects-by-style:    Group by SecondsGeneral.style, SUM(defect amounts)
  - weekly-trend:        Group by SecondsGeneral.week, SUM(defect amounts)
  - sewing-vs-fabric:    Split defect sums into sewing and fabric families
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status as http_status
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce

from quality_data.models import SecondsGeneral, SecondsGeneralDefect
from excel_importer.sheet_configs import (
    SECONDS_GENERAL_SEWING_DEFECTS,
    SECONDS_GENERAL_FABRIC_DEFECTS,
)
from quality_data.serializers import (
    KpiBarSerializer,
    KpiSeriesSerializer,
)


class SecondsGeneralAnalyticsViewSet(ViewSet):
    """
    ViewSet for Seconds General analytics.

    All endpoints aggregate SecondsGeneralDefect rows exclusively —
    no QC FA or Container data is mixed in (spec: seconds-general-analytic-isolation).

    Endpoints:
        - GET defects-by-customer/
        - GET defects-by-style/
        - GET weekly-trend/
        - GET sewing-vs-fabric/
    """

    @staticmethod
    def _base_defect_queryset():
        """Return base SecondsGeneralDefect queryset for .values().annotate() aggregation."""
        return SecondsGeneralDefect.objects.all()

    # ── 2.3: Defects by Customer ──────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-customer")
    def defects_by_customer(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-customer/

        GROUP BY customer: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Response: [{"label": "CUST_ALPHA", "value": 75}, ...]
        """
        queryset = self._base_defect_queryset()

        aggregated = (
            queryset
            .values(customer_name=F("seconds_general__customer"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["customer_name"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2.3: Defects by Style ─────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-style")
    def defects_by_style(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-style/

        GROUP BY style: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Response: [{"label": "ST-100", "value": 120}, ...]
        """
        queryset = self._base_defect_queryset()

        aggregated = (
            queryset
            .values(style_name=F("seconds_general__style"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["style_name"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2.2: Weekly Trend ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="weekly-trend")
    def weekly_trend(self, request):
        """
        GET /quality/kpis/seconds-general/weekly-trend/

        GROUP BY week: SUM(SecondsGeneralDefect.amount)
        Ordered by week ascending.

        Supports filters:
            - week:      ?week=1          (exact integer match)
            - date_range: ?date_range=YYYY-MM-DD,YYYY-MM-DD

        Response: [{"name": "Defects", "data": [{"x": 1, "y": 45}, ...]}]
        """
        base_qs = SecondsGeneral.objects.all()

        # ── date_range filter ──
        date_range = request.query_params.get("date_range")
        if date_range is not None:
            parts = [p.strip() for p in str(date_range).split(",")]
            if len(parts) == 2 and parts[0] and parts[1]:
                base_qs = base_qs.filter(date__gte=parts[0], date__lte=parts[1])

        # ── week filter ──
        week = request.query_params.get("week")
        if week is not None:
            try:
                week_int = int(week)
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid 'week' parameter. It must be an integer."},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            base_qs = base_qs.filter(week__exact=week_int)

        # Aggregate defects per filtered SecondsGeneral records
        aggregated = (
            SecondsGeneralDefect.objects
            .filter(seconds_general__in=base_qs)
            .values(week_num=F("seconds_general__week"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("week_num")
        )

        data_points = [
            {"x": item["week_num"], "y": item["total"]}
            for item in aggregated
        ]

        result = [{"name": "Defects", "data": data_points}]
        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2.2: Sewing vs Fabric Mix ─────────────────────────────

    @action(detail=False, methods=["get"], url_path="sewing-vs-fabric")
    def sewing_vs_fabric(self, request):
        """
        GET /quality/kpis/seconds-general/sewing-vs-fabric/

        Splits SecondsGeneralDefect totals into sewing and fabric families
        using configured classifications:
            - SECONDS_GENERAL_SEWING_DEFECTS (13 types)
            - SECONDS_GENERAL_FABRIC_DEFECTS (10 types)

        Response: [{"label": "Sewing", "value": 234}, {"label": "Fabric", "value": 156}]
        """
        sewing_total = (
            SecondsGeneralDefect.objects
            .filter(defect_type__name__in=SECONDS_GENERAL_SEWING_DEFECTS)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        )
        fabric_total = (
            SecondsGeneralDefect.objects
            .filter(defect_type__name__in=SECONDS_GENERAL_FABRIC_DEFECTS)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        )

        result = [
            {"label": "Sewing", "value": sewing_total},
            {"label": "Fabric", "value": fabric_total},
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)
