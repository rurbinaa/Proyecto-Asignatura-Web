"""
SecondsGeneral analytics endpoints (Phases 2 & 3 of refactor-multisheet-dashboard).

Uses Django ORM `.values().annotate()` to compute analytics exclusively
from SecondsGeneral and SecondsGeneralDefect data sources. All endpoints
support global filters via SecondsGeneralFilterMixin.

Endpoints:
  - defects-by-customer: Group by SecondsGeneral.customer, SUM(defect amounts)
  - defects-by-style:    Group by SecondsGeneral.style, SUM(defect amounts)
  - weekly-trend:        Group by SecondsGeneral.week, SUM(defect amounts)
  - sewing-vs-fabric:    Split defect sums into sewing and fabric families
  - production-totals:   Aggregate produced/fixed/definitive across all SG records
  - top-defects:         Top 10 defect types by sewing/fabric family
  - fix-vs-definitive:   Weekly aggregation of fixed vs definitive seconds
  - defects-by-color:    Group by SecondsGeneral.color, SUM(defect amounts)
  - defects-by-size:     Group by SecondsGeneral.size, SUM(defect amounts)
  - defects-by-line:     Group by SecondsGeneral.team (and line_code if present)
  - filter-options:      Available distinct filter values for dropdowns
"""

import math
import re

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status as http_status
from rest_framework import exceptions as rest_framework_exceptions
from django.db.models import Sum, F, Value, Case, When, Q
from django.db.models.functions import Coalesce, Cast

from quality_data.models import SecondsGeneral, SecondsGeneralDefect
from excel_importer.sheet_configs import (
    SECONDS_GENERAL_SEWING_DEFECTS,
    SECONDS_GENERAL_FABRIC_DEFECTS,
)
from quality_data.serializers import (
    KpiBarSerializer,
    KpiSeriesSerializer,
    FilterOptionsSerializer,
)


def _build_line_label(team, line_code):
    if line_code is not None and not (isinstance(line_code, float) and math.isnan(line_code)):
        return str(line_code)
    if team is not None and not (isinstance(team, float) and math.isnan(team)):
        return f"Line {team}"
    return "Unknown"


def _line_sort_key(label):
    if label == "Unknown":
        return (2, float("inf"), label)

    first_number = re.search(r"\d+", label)
    if first_number:
        return (0, int(first_number.group()), label)

    return (1, float("inf"), label)

# Valid defect type families for top-defects endpoint
VALID_DEFECT_FAMILIES = {"sewing", "fabric"}


class SecondsGeneralFilterMixin:
    """
    Mixin that provides SecondsGeneral queryset filtering from query parameters.

    Supported filters:
        - date_range: date__gte / date__lte (format: "YYYY-MM-DD,YYYY-MM-DD")
        - week: week__exact (integer)
        - customer: customer__exact (string)
        - style: style__exact (string)
        - color: color__exact (string)
        - size: size__exact (string)
        - team: team__exact (integer)
        - line_code: line_code__exact (string)
        - include_dual_lines: boolean toggle (default True)
    """

    def _get_filtered_sg_queryset(self, request):
        """
        Apply filters from request query params to a SecondsGeneral queryset.

        Returns a filtered QuerySet (or complete queryset if no filters applied).
        """
        qs = SecondsGeneral.objects.all()

        # ── date_range: "start_date,end_date" → date__gte, date__lte ──
        date_range = request.query_params.get("date_range")
        if date_range is not None:
            parts = [p.strip() for p in str(date_range).split(",")]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise rest_framework_exceptions.ValidationError({
                    "date_range": "Invalid date_range. Use YYYY-MM-DD,YYYY-MM-DD."
                })
            qs = qs.filter(date__gte=parts[0], date__lte=parts[1])

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

        # ── customer: exact string match ──
        customer = request.query_params.get("customer")
        if customer:
            qs = qs.filter(customer__exact=customer)

        # ── style: exact string match ──
        style = request.query_params.get("style")
        if style:
            qs = qs.filter(style__exact=style)

        # ── color: exact string match ──
        color = request.query_params.get("color")
        if color:
            qs = qs.filter(color__exact=color)

        # ── size: exact string match ──
        size = request.query_params.get("size")
        if size:
            qs = qs.filter(size__exact=size)

        # ── team: exact integer match ──
        team = request.query_params.get("team")
        if team is not None:
            try:
                team_int = int(team)
            except (ValueError, TypeError):
                raise rest_framework_exceptions.ValidationError({
                    "team": "Invalid value. It must be an integer."
                })
            qs = qs.filter(team__exact=team_int)

        # ── line_code: exact string match (takes precedence over include_dual_lines) ──
        line_code = request.query_params.get("line_code")
        explicit_line_code = False
        if line_code:
            qs = qs.filter(line_code__exact=line_code)
            explicit_line_code = True

        # ── include_dual_lines toggle ──
        # Default (no param): exclude dual-line records (rows with populated line_code).
        # Explicit "true" includes dual lines; explicit "false" excludes them.
        # Explicit line_code filter takes precedence over this toggle.
        include_raw = request.query_params.get("include_dual_lines", "false").strip().lower()
        include_dual_lines = include_raw == "true"
        if not include_dual_lines and not explicit_line_code:
            qs = qs.exclude(line_code__gt="")

        return qs

    def _get_filtered_defect_queryset(self, request):
        """
        Return SecondsGeneralDefect queryset filtered through the SG filter.

        Any record whose parent SecondsGeneral is excluded by the filter
        is also excluded from the defect queryset.
        """
        return SecondsGeneralDefect.objects.filter(
            seconds_general__in=self._get_filtered_sg_queryset(request)
        )


class SecondsGeneralAnalyticsViewSet(SecondsGeneralFilterMixin, ViewSet):
    """
    ViewSet for Seconds General analytics.

    All endpoints aggregate SecondsGeneralDefect rows exclusively —
    no QC FA or Container data is mixed in (spec: seconds-general-analytic-isolation).

    All endpoints support global filters via SecondsGeneralFilterMixin.

    Endpoints:
        - GET defects-by-customer/
        - GET defects-by-style/
        - GET weekly-trend/
        - GET sewing-vs-fabric/
        - GET production-totals/
        - GET top-defects/
        - GET fix-vs-definitive/
        - GET defects-by-color/
        - GET defects-by-size/
        - GET defects-by-line/
        - GET filter-options/
    """

    # ── Defects by Customer ──────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-customer")
    def defects_by_customer(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-customer/

        GROUP BY customer: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Response: [{"label": "CUST_ALPHA", "value": 75}, ...]
        """
        queryset = self._get_filtered_defect_queryset(request)

        aggregated = (
            queryset
            .exclude(seconds_general__customer__in=["", None])
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

    # ── Defects by Style ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-style")
    def defects_by_style(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-style/

        GROUP BY style: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Response: [{"label": "ST-100", "value": 120}, ...]
        """
        queryset = self._get_filtered_defect_queryset(request)

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

    # ── Weekly Trend ─────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="weekly-trend")
    def weekly_trend(self, request):
        """
        GET /quality/kpis/seconds-general/weekly-trend/

        GROUP BY week: SUM(SecondsGeneralDefect.amount)
        Ordered by week ascending.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [{"name": "Defects", "data": [{"x": 1, "y": 45}, ...]}]
        """
        defect_qs = self._get_filtered_defect_queryset(request)

        aggregated = (
            defect_qs
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

    # ── Sewing vs Fabric Mix ─────────────────────────────────

    @action(detail=False, methods=["get"], url_path="sewing-vs-fabric")
    def sewing_vs_fabric(self, request):
        """
        GET /quality/kpis/seconds-general/sewing-vs-fabric/

        Splits SecondsGeneralDefect totals into sewing and fabric families
        using configured classifications:
            - SECONDS_GENERAL_SEWING_DEFECTS (13 types)
            - SECONDS_GENERAL_FABRIC_DEFECTS (10 types)

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [{"label": "Sewing", "value": 234}, {"label": "Fabric", "value": 156}]
        """
        defect_qs = self._get_filtered_defect_queryset(request)

        sewing_total = (
            defect_qs
            .filter(defect_type__name__in=SECONDS_GENERAL_SEWING_DEFECTS)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        )
        fabric_total = (
            defect_qs
            .filter(defect_type__name__in=SECONDS_GENERAL_FABRIC_DEFECTS)
            .aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"]
        )

        result = [
            {"label": "Sewing", "value": sewing_total},
            {"label": "Fabric", "value": fabric_total},
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Production Totals ────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="production-totals")
    def production_totals(self, request):
        """
        GET /quality/kpis/seconds-general/production-totals/

        Aggregates total_produced, total_fixed, total_definitive
        across filtered SecondsGeneral records.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: {"total_produced": 1234, "total_fixed": 567, "total_definitive": 890}
        """
        sg_qs = self._get_filtered_sg_queryset(request)

        aggregated = sg_qs.aggregate(
            total_produced=Coalesce(Sum("produced"), Value(0)),
            total_fixed=Coalesce(Sum("fixed"), Value(0)),
            total_definitive=Coalesce(Sum("definitive"), Value(0)),
        )

        return Response(aggregated, status=http_status.HTTP_200_OK)

    # ── Top Specific Defects (Pareto) ────────────────────────

    @action(detail=False, methods=["get"], url_path="top-defects")
    def top_defects(self, request):
        """
        GET /quality/kpis/seconds-general/top-defects/?type=sewing
        GET /quality/kpis/seconds-general/top-defects/?type=fabric

        Groups SecondsGeneralDefect by defect_type__name, sums amount,
        filters by sewing or fabric family, sorts descending, limits to 10.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [{"label": "picado_aguja", "value": 75}, ...]
        """
        defect_family = request.query_params.get("type")

        if defect_family not in VALID_DEFECT_FAMILIES:
            return Response(
                {"detail": f"Invalid or missing 'type' parameter. Must be one of: {', '.join(sorted(VALID_DEFECT_FAMILIES))}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        defect_names = (
            SECONDS_GENERAL_SEWING_DEFECTS if defect_family == "sewing"
            else SECONDS_GENERAL_FABRIC_DEFECTS
        )

        defect_qs = self._get_filtered_defect_queryset(request)

        aggregated = (
            defect_qs
            .filter(defect_type__name__in=defect_names)
            .values(label=F("defect_type__name"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")[:10]
        )

        result = [
            {"label": item["label"], "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Fix vs Definitive Efficacy ───────────────────────────

    @action(detail=False, methods=["get"], url_path="fix-vs-definitive")
    def fix_vs_definitive(self, request):
        """
        GET /quality/kpis/seconds-general/fix-vs-definitive/

        Weekly aggregation of fixed vs definitive seconds quantities.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [
            {"name": "Fixed", "data": [{"x": 1, "y": 55}, ...]},
            {"name": "Definitive", "data": [{"x": 1, "y": 33}, ...]}
        ]
        """
        sg_qs = self._get_filtered_sg_queryset(request)

        fixed_data = (
            sg_qs
            .values(week_num=F("week"))
            .annotate(total=Coalesce(Sum("fixed"), Value(0)))
            .order_by("week_num")
        )

        definitive_data = (
            sg_qs
            .values(week_num=F("week"))
            .annotate(total=Coalesce(Sum("definitive"), Value(0)))
            .order_by("week_num")
        )

        result = [
            {
                "name": "Fixed",
                "data": [
                    {"x": item["week_num"], "y": item["total"]}
                    for item in fixed_data
                ],
            },
            {
                "name": "Definitive",
                "data": [
                    {"x": item["week_num"], "y": item["total"]}
                    for item in definitive_data
                ],
            },
        ]

        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── V2: Defects by Color ─────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-color")
    def defects_by_color(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-color/

        GROUP BY seconds_general__color: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [{"label": "Red", "value": 75}, ...]
        """
        defect_qs = self._get_filtered_defect_queryset(request)

        aggregated = (
            defect_qs
            .exclude(seconds_general__color__in=["", None])
            .values(color_name=F("seconds_general__color"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["color_name"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── V2: Defects by Size ──────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-size")
    def defects_by_size(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-size/

        GROUP BY seconds_general__size: SUM(SecondsGeneralDefect.amount)
        Sorted by total descending.

        Supports global filters via SecondsGeneralFilterMixin.

        Response: [{"label": "M", "value": 75}, ...]
        """
        defect_qs = self._get_filtered_defect_queryset(request)

        aggregated = (
            defect_qs
            .exclude(seconds_general__size__in=["", None])
            .values(size_name=F("seconds_general__size"))
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")
        )

        result = [
            {"label": item["size_name"] or "Unknown", "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── V2: Defects by Line ──────────────────────────────────

    @action(detail=False, methods=["get"], url_path="defects-by-line")
    def defects_by_line(self, request):
        """
        GET /quality/kpis/seconds-general/defects-by-line/

        GROUP BY seconds_general__team and optionally seconds_general__line_code.
        For records without line_code, displays as "Team {N}".
        For records with line_code (dual lines), displays the line_code.
        Sorted by total descending.

        Supports global filters via SecondsGeneralFilterMixin,
        including the include_dual_lines toggle.

        Response: [{"label": "Team 1", "value": 75}, {"label": "L1", "value": 25}, ...]
        """
        defect_qs = self._get_filtered_defect_queryset(request)

        aggregated = (
            defect_qs
            .values(
                team=F("seconds_general__team"),
                line_code=F("seconds_general__line_code"),
            )
            .annotate(total=Coalesce(Sum("amount"), Value(0)))
            .order_by("-total")
        )

        result = [
            {
                "label": _build_line_label(item["team"], item["line_code"]),
                "value": item["total"],
            }
            for item in aggregated
        ]
        result.sort(key=lambda item: _line_sort_key(item["label"]))

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── V2: Filter Options ───────────────────────────────────

    @action(detail=False, methods=["get"], url_path="filter-options")
    def filter_options(self, request):
        """
        GET /quality/kpis/seconds-general/filter-options/

        Returns distinct filter choices for customer, style, color, size,
        team, week, line_code from the SecondsGeneral table.
        Used to populate dynamic filter selects/datalists in the frontend.

        Response: {
            "customer": ["CUST_ALPHA", ...],
            "style": ["ST-100", ...],
            "color": ["Red", ...],
            "size": ["M", ...],
            "team": [1, 2, ...],
            "week": [1, 2, ...],
            "line_code": ["L1", ...],
            "include_dual_lines_default": true,
        }
        """
        base_qs = SecondsGeneral.objects.all()

        customers = list(
            base_qs.values_list("customer", flat=True)
            .distinct()
            .order_by("customer")
        )
        styles = list(
            base_qs.values_list("style", flat=True)
            .distinct()
            .order_by("style")
        )
        colors = list(
            base_qs.values_list("color", flat=True)
            .distinct()
            .order_by("color")
        )
        sizes = list(
            base_qs.values_list("size", flat=True)
            .distinct()
            .order_by("size")
        )
        teams = list(
            base_qs.values_list("team", flat=True)
            .distinct()
            .order_by("team")
        )
        weeks = list(
            base_qs.values_list("week", flat=True)
            .distinct()
            .order_by("week")
        )
        line_codes = list(
            base_qs.filter(line_code__isnull=False)
            .values_list("line_code", flat=True)
            .distinct()
            .order_by("line_code")
        )
        include_dual_lines_default = len(line_codes) > 0

        payload = {
            "customer": [c for c in customers if c],
            "style": [s for s in styles if s],
            "color": [c for c in colors if c],
            "size": [s for s in sizes if s],
            "team": [t for t in teams if t is not None],
            "week": [w for w in weeks if w is not None],
            "line_code": [lc for lc in line_codes if lc],
            "batch": [],
            "include_dual_lines_default": include_dual_lines_default,
        }

        serializer = FilterOptionsSerializer(payload, many=False)
        return Response(serializer.data, status=http_status.HTTP_200_OK)
