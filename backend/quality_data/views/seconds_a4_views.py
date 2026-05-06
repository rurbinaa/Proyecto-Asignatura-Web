"""
SecondsA4 analytics endpoints.

Uses Django ORM `.values().annotate()` to compute analytics exclusively
from SecondsA4 data sources. All endpoints support filters via
SecondsA4FilterMixin.

Endpoints (Phase 1):
  - filter-options: Available distinct filter values for dropdowns

Endpoints (Phase 2):
  - executive-summary: Aggregated totals and percentage gating
  - weekly-trend: Weekly total_of_2ds series
  - sew-vs-fab: Split seconds_by_sew vs seconds_by_fab
  - by-style: 2DS grouped by style, desc
  - by-color: 2DS grouped by color, desc
  - by-line: 2DS grouped by line, desc
  - by-cut: 2DS grouped by cut number, desc
  - pass-fail-weekly: Weekly pass vs fail series
"""

from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status as http_status
from rest_framework import exceptions as rest_framework_exceptions
from quality_data.models import SecondsA4
from quality_data.serializers import (
    SecondsA4FilterOptionsSerializer,
    KpiBarSerializer,
    KpiSeriesSerializer,
)


class SecondsA4FilterMixin:
    """
    Mixin that provides SecondsA4 queryset filtering from query parameters.

    Supported filters:
        - year: year__exact (integer)
        - week: week__exact (integer)
        - date: date__gte / date__lte via date_range
        - style: style__exact (string)
        - color: color__name__exact (string, traverses FK)
        - line: line__exact (string)
        - cut_num: cut_num__exact (integer)
    """

    def _get_filtered_a4_queryset(self, request):
        """
        Apply filters from request query params to a SecondsA4 queryset.

        Returns a filtered QuerySet (or complete queryset if no filters applied).
        """
        qs = SecondsA4.objects.all()

        # ── year: exact integer match ──
        year = request.query_params.get("year")
        if year is not None:
            try:
                year_int = int(year)
            except (ValueError, TypeError):
                raise rest_framework_exceptions.ValidationError({
                    "year": "Invalid value. It must be an integer."
                })
            qs = qs.filter(year__exact=year_int)

        # ── week: exact integer match ──
        week = request.query_params.get("week")
        if week is not None:
            try:
                week_int = int(week)
            except (ValueError, TypeError):
                raise rest_framework_exceptions.ValidationError({
                    "week": "Invalid value. It must be an integer."
                })
            qs = qs.filter(week__exact=week_int)

        # ── style: exact string match ──
        style = request.query_params.get("style")
        if style:
            qs = qs.filter(style__exact=style)

        # ── color: FK traversal via color__name ──
        color = request.query_params.get("color")
        if color:
            qs = qs.filter(color__name__exact=color)

        # ── line: exact string match ──
        line = request.query_params.get("line")
        if line:
            qs = qs.filter(line__exact=line)

        # ── cut_num: exact integer match ──
        cut_num = request.query_params.get("cut_num")
        if cut_num is not None:
            try:
                cut_num_int = int(cut_num)
            except (ValueError, TypeError):
                raise rest_framework_exceptions.ValidationError({
                    "cut_num": "Invalid value. It must be an integer."
                })
            qs = qs.filter(cut_num__exact=cut_num_int)

        return qs


class SecondsA4AnalyticsViewSet(SecondsA4FilterMixin, ViewSet):
    """
    ViewSet for Seconds A4 analytics.

    All endpoints aggregate SecondsA4 rows exclusively — no QC FA or
    Seconds General data is mixed in.

    All endpoints support filters via SecondsA4FilterMixin.

    Endpoints:
        - GET filter-options/
        - GET executive-summary/
        - GET weekly-trend/
        - GET sew-vs-fab/
        - GET by-style/
        - GET by-color/
        - GET by-line/
        - GET by-cut/
        - GET pass-fail-weekly/
    """

    # ── Filter Options ───────────────────────────────────

    @action(detail=False, methods=["get"], url_path="filter-options")
    def filter_options(self, request):
        """
        GET /quality/kpis/seconds-a4/filter-options/

        Returns distinct filter choices for year, week, line, cut_num,
        style, and color from the SecondsA4 table.

        When filter params are present (e.g. ?color=Red), the returned
        option lists are narrowed to the filtered queryset — including
        year itself.

        Response: {
            "year": [2025, 2026, ...],
            "week": [1, 2, ...],
            "line": ["L1", ...],
            "cut_num": [101, ...],
            "style": ["STYLE-A", ...],
            "color": ["Red", ...],
        }
        """
        qs = self._get_filtered_a4_queryset(request)

        # All fields are derived from the filtered queryset.
        # When a filter param is active (e.g. ?color=Red), the returned
        # option lists are narrowed — including year itself.
        years = list(
            qs.values_list("year", flat=True)
            .distinct()
            .order_by("year")
        )
        weeks = list(
            qs.values_list("week", flat=True)
            .distinct()
            .order_by("week")
        )
        lines = list(
            qs.values_list("line", flat=True)
            .distinct()
            .order_by("line")
        )
        cut_nums = list(
            qs.values_list("cut_num", flat=True)
            .distinct()
            .order_by("cut_num")
        )
        styles = list(
            qs.values_list("style", flat=True)
            .distinct()
            .order_by("style")
        )
        colors = list(
            qs.values_list("color__name", flat=True)
            .distinct()
            .order_by("color__name")
        )

        payload = {
            "year": [y for y in years if y is not None],
            "week": [w for w in weeks if w is not None],
            "line": [l for l in lines if l],
            "cut_num": [c for c in cut_nums if c is not None],
            "style": [s for s in styles if s],
            "color": [c for c in colors if c],
        }

        serializer = SecondsA4FilterOptionsSerializer(payload, many=False)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Executive Summary ────────────────────────────────

    @action(detail=False, methods=["get"], url_path="executive-summary")
    def executive_summary(self, request):
        """
        GET /quality/kpis/seconds-a4/executive-summary/

        Aggregates all KPI totals from the filtered SecondsA4 queryset.
        Percentages are shipped as an empty array for MVP — no metric
        registry is validated yet (see the design's open question).

        Response:
            {
                "totals": {
                    "total_of_2ds": <int>,
                    "seconds_by_sew": <int>,
                    "seconds_by_fab": <int>,
                    "seconds_sew_a4": <int>,
                    "seconds_fab_a4": <int>,
                    "accepted": <int>,
                    "rejected": <int>,
                },
                "percentages": []
            }
        """
        qs = self._get_filtered_a4_queryset(request)

        aggregated = qs.aggregate(
            total_of_2ds=Coalesce(Sum("total_of_2ds"), Value(0)),
            seconds_by_sew=Coalesce(Sum("seconds_by_sew"), Value(0)),
            seconds_by_fab=Coalesce(Sum("seconds_by_fab"), Value(0)),
            seconds_sew_a4=Coalesce(Sum("seconds_sew_a4"), Value(0)),
            seconds_fab_a4=Coalesce(Sum("seconds_fab_a4"), Value(0)),
            accepted=Coalesce(Sum("accepted"), Value(0)),
            rejected=Coalesce(Sum("rejected"), Value(0)),
        )

        payload = {
            "totals": aggregated,
            "percentages": [],
        }

        return Response(payload, status=http_status.HTTP_200_OK)

    # ── Weekly Trend ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="weekly-trend")
    def weekly_trend(self, request):
        """
        GET /quality/kpis/seconds-a4/weekly-trend/

        Groups filtered SecondsA4 records by week and sums total_of_2ds.
        Sorted by week ascending.

        Response:
            [{"name": "2DS", "data": [{"x": "2025-W1", "y": <sum>}, ...]}]
        """
        qs = self._get_filtered_a4_queryset(request)

        data_points = [
            {"x": f'{item["year"]}-W{item["week"]}', "y": item["total"]}
            for item in qs.values("year", "week")
            .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
            .order_by("year", "week")
        ]

        result = [{"name": "2DS", "data": data_points}]
        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Sew vs Fab Split ─────────────────────────────────

    @action(detail=False, methods=["get"], url_path="sew-vs-fab")
    def sew_vs_fab(self, request):
        """
        GET /quality/kpis/seconds-a4/sew-vs-fab/

        Splits into Sew and Fab totals using seconds_by_sew and
        seconds_by_fab fields from the filtered SecondsA4 records.

        Response:
            [{"label": "Sew", "value": <int>}, {"label": "Fabric", "value": <int>}]
        """
        qs = self._get_filtered_a4_queryset(request)

        aggregated = qs.aggregate(
            sew=Coalesce(Sum("seconds_by_sew"), Value(0)),
            fab=Coalesce(Sum("seconds_by_fab"), Value(0)),
        )

        result = [
            {"label": "Sew", "value": aggregated["sew"]},
            {"label": "Fabric", "value": aggregated["fab"]},
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2DS by Line ──────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="by-line")
    def by_line(self, request):
        """GET /quality/kpis/seconds-a4/by-line/"""
        qs = self._get_filtered_a4_queryset(request)

        aggregated = (
            qs.values("line")
            .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["line"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2DS by Cut ───────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="by-cut")
    def by_cut(self, request):
        """GET /quality/kpis/seconds-a4/by-cut/"""
        qs = self._get_filtered_a4_queryset(request)

        aggregated = (
            qs.values("cut_num")
            .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": f'Cut {item["cut_num"]}', "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Pass vs Fail Weekly ──────────────────────────────

    @action(detail=False, methods=["get"], url_path="pass-fail-weekly")
    def pass_fail_weekly(self, request):
        """GET /quality/kpis/seconds-a4/pass-fail-weekly/"""
        qs = self._get_filtered_a4_queryset(request)

        aggregated = list(
            qs.values("year", "week")
            .annotate(
                total_pass=Coalesce(Sum("pass_field"), Value(0)),
                total_fail=Coalesce(Sum("fail_field"), Value(0)),
            )
            .order_by("year", "week")
        )

        pass_series = {
            "name": "Pass",
            "data": [
                {"x": f'{item["year"]}-W{item["week"]}', "y": item["total_pass"]}
                for item in aggregated
            ],
        }
        fail_series = {
            "name": "Fail",
            "data": [
                {"x": f'{item["year"]}-W{item["week"]}', "y": item["total_fail"]}
                for item in aggregated
            ],
        }

        serializer = KpiSeriesSerializer([pass_series, fail_series], many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2DS by Style ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="by-style")
    def by_style(self, request):
        """
        GET /quality/kpis/seconds-a4/by-style/

        Groups filtered SecondsA4 records by style and sums total_of_2ds.
        Sorted descending by total.

        Response:
            [{"label": "STYLE-A", "value": <int>}, ...]
        """
        qs = self._get_filtered_a4_queryset(request)

        aggregated = (
            qs.values("style")
            .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["style"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── 2DS by Color ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="by-color")
    def by_color(self, request):
        """
        GET /quality/kpis/seconds-a4/by-color/

        Groups filtered SecondsA4 records by color (FK traversal via
        color__name) and sums total_of_2ds. Sorted descending by total.

        Response:
            [{"label": "Red", "value": <int>}, ...]
        """
        qs = self._get_filtered_a4_queryset(request)

        aggregated = (
            qs.values("color__name")
            .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["color__name"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)
