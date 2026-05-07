"""
SecondsA4 analytics endpoints.

Uses Django ORM `.values().annotate()` to compute analytics exclusively
from SecondsA4 data sources. All endpoints support filters via
SecondsA4FilterMixin and response caching via Redis.

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

import hashlib
import json
import logging

from django.core.cache import cache
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

logger = logging.getLogger(__name__)

SECONDS_A4_CACHE_PREFIX = "seconds_a4"
SECONDS_A4_CACHE_VERSION = "v1"
SECONDS_A4_CACHE_TTL_DEFAULT = 120
SECONDS_A4_CACHE_TTLS = {
    "filter_options": 300,
}

SECONDS_A4_FILTER_KEYS = ("year", "week", "style", "color", "line", "cut_num")
SECONDS_A4_NUMERIC_FILTER_KEYS = ("year", "week", "cut_num")


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

        def _compute():
            qs = self._get_filtered_a4_queryset(request)

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
            return serializer.data

        return _seconds_a4_cached_action(request, "filter_options", _compute)

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

        def _compute():
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

            return {
                "totals": aggregated,
                "percentages": [],
            }

        return _seconds_a4_cached_action(request, "executive_summary", _compute)

    @action(detail=False, methods=["get"], url_path="weekly-trend")
    def weekly_trend(self, request):
        """
        GET /quality/kpis/seconds-a4/weekly-trend/

        Groups filtered SecondsA4 records by week and sums total_of_2ds.
        Sorted by week ascending.

        Response:
            [{"name": "2DS", "data": [{"x": "2025-W1", "y": <sum>}, ...]}]
        """

        def _compute():
            qs = self._get_filtered_a4_queryset(request)

            data_points = [
                {"x": f'{item["year"]}-W{item["week"]}', "y": item["total"]}
                for item in qs.values("year", "week")
                .annotate(total=Coalesce(Sum("total_of_2ds"), Value(0)))
                .order_by("year", "week")
            ]

            result = [{"name": "2DS", "data": data_points}]
            serializer = KpiSeriesSerializer(result, many=True)
            return serializer.data

        return _seconds_a4_cached_action(request, "weekly_trend", _compute)

    @action(detail=False, methods=["get"], url_path="sew-vs-fab")
    def sew_vs_fab(self, request):
        """
        GET /quality/kpis/seconds-a4/sew-vs-fab/

        Splits into Sew and Fab totals using seconds_by_sew and
        seconds_by_fab fields from the filtered SecondsA4 records.

        Response:
            [{"label": "Sew", "value": <int>}, {"label": "Fabric", "value": <int>}]
        """

        def _compute():
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
            return serializer.data

        return _seconds_a4_cached_action(request, "sew_vs_fab", _compute)

    @action(detail=False, methods=["get"], url_path="by-cut")
    def by_cut(self, request):
        """GET /quality/kpis/seconds-a4/by-cut/"""

        def _compute():
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
            return serializer.data

        return _seconds_a4_cached_action(request, "by_cut", _compute)

    @action(detail=False, methods=["get"], url_path="pass-fail-weekly")
    def pass_fail_weekly(self, request):
        """GET /quality/kpis/seconds-a4/pass-fail-weekly/"""

        def _compute():
            qs = self._get_filtered_a4_queryset(request).filter(
                year__gt=0,
                week__gte=1,
                week__lte=53,
            )

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
            return serializer.data

        return _seconds_a4_cached_action(request, "pass_fail_weekly", _compute)

    @action(detail=False, methods=["get"], url_path="by-color")
    def by_color(self, request):
        """
        GET /quality/kpis/seconds-a4/by-color/

        Groups filtered SecondsA4 records by color (FK traversal via
        color__name) and sums total_of_2ds. Sorted descending by total.

        Response:
            [{"label": "Red", "value": <int>}, ...]
        """

        def _compute():
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
            return serializer.data

        return _seconds_a4_cached_action(request, "by_color", _compute)
