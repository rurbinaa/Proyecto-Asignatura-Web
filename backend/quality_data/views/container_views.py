"""
Container KPI endpoints under /quality/kpis/container/*.

Provides:
  - ContainerFilterMixin: shared filter logic for Container querysets
  - ContainerKpiViewSet: ViewSet with @action endpoints for all Container KPIs

Filter contract (Container-specific, does NOT reuse QFA filter surface):
  - customer         : exact match on Container.customer
  - date_range       : "YYYY-MM-DD,YYYY-MM-DD" → inclusive bounds on Container.date
  - from_date        : single lower bound (used when date_range is absent/blank)
  - to_date          : single upper bound (used when date_range is absent/blank)

Precedence: date_range > from_date/to_date.
Null dates are always excluded when ANY date filter is active.
Invalid/reversed dates return 400.
"""

import datetime
from django.db.models import Sum, Count, Avg, Case, When, F, IntegerField
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status as http_status
from rest_framework import exceptions as rest_framework_exceptions

from quality_data.models import Container, ContainerInspectionDefect
from quality_data.serializers import (
    KpiBarSerializer,
    KpiSeriesSerializer,
    KpiDonutSerializer,
    ScalarMetricSerializer,
    WorstContainerSerializer,
)


# ─────────────────────────────────────────────────────────
# ContainerFilterMixin
# ─────────────────────────────────────────────────────────


class ContainerFilterMixin:
    """
    Mixin that filters Container querysets based on Container-specific query params.

    Supported filters:
        - customer:   Container.customer exact match
        - date_range: "YYYY-MM-DD,YYYY-MM-DD" (takes precedence over from/to)
        - from_date:  Container.date >= from_date (used when date_range absent/blank)
        - to_date:    Container.date <= to_date (used when date_range absent/blank)

    Null dates are excluded when ANY date filtering is active.
    Invalid format or reversed dates → 400 Bad Request.
    """

    @staticmethod
    def _parse_date_param(raw_value, field_name):
        if raw_value is None:
            return None

        value = str(raw_value).strip()
        if not value:
            return None

        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            raise rest_framework_exceptions.ValidationError({
                field_name: "Invalid date. Use YYYY-MM-DD."
            })

    @staticmethod
    def _parse_date_range_param(raw_value, field_name="date_range"):
        value = (raw_value or "").strip()
        if not value:
            return None, None

        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise rest_framework_exceptions.ValidationError({
                field_name: "Invalid date_range. Use YYYY-MM-DD,YYYY-MM-DD."
            })

        from_date = ContainerFilterMixin._parse_date_param(parts[0], field_name)
        to_date = ContainerFilterMixin._parse_date_param(parts[1], field_name)
        ContainerFilterMixin._validate_date_order(from_date, to_date, field_name)
        return from_date, to_date

    @staticmethod
    def _validate_date_order(from_date, to_date, field_name="date_range"):
        if from_date and to_date and from_date > to_date:
            raise rest_framework_exceptions.ValidationError({
                field_name: "Invalid date range. Start date must be on or before end date."
            })

    def get_filtered_container_queryset(self, queryset=None):
        """
        Apply Container-specific filters from query params to the given queryset.

        Args:
            queryset: Base Container QuerySet (defaults to Container.objects.all())

        Returns:
            Filtered QuerySet with date and customer filters applied.
        """
        if queryset is None:
            queryset = Container.objects.all()

        request = self.request

        # ── customer filter ──
        customer = request.query_params.get("customer")
        if customer:
            queryset = queryset.filter(customer__exact=customer)

        # ── date filtering ──
        date_range_raw = request.query_params.get("date_range")
        from_date = None
        to_date = None

        if date_range_raw is not None and date_range_raw.strip():
            # date_range takes precedence
            from_date, to_date = self._parse_date_range_param(date_range_raw, "date_range")
        else:
            # Fall back to from_date / to_date
            from_date = self._parse_date_param(
                request.query_params.get("from_date"), "from_date"
            )
            to_date = self._parse_date_param(
                request.query_params.get("to_date"), "to_date"
            )
            if from_date and to_date and from_date > to_date:
                raise rest_framework_exceptions.ValidationError({
                    "from_date": "Invalid date range. Start date must be on or before end date.",
                    "to_date": "Invalid date range. Start date must be on or before end date.",
                })

        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        return queryset


# ─────────────────────────────────────────────────────────
# ContainerKpiViewSet
# ─────────────────────────────────────────────────────────


class ContainerKpiViewSet(ContainerFilterMixin, ViewSet):
    """
    Container KPI endpoints registered under /quality/kpis/container/.

    Endpoints:
        - GET executive-summary/      → aggregate totals and average pass rate
        - GET containers-by-state/    → pass-rate bucket distribution
        - GET pass-rate-trend/        → date series of average pass rate
        - GET inspected-trend/         → date series of total palettes inspected
        - GET rejected-trend/          → date series of total rejected palettes
        - GET top-defects/            → top defect types by SUM(amount) DESC
        - GET defect-composition/     → defect type composition (donut shape)
        - GET worst-containers/       → containers ranked by pass rate ASC
    """

    def _base_queryset(self):
        """Return the filtered Container queryset shared by all endpoints."""
        return self.get_filtered_container_queryset()

    def _defect_queryset(self):
        """Return ContainerInspectionDefect queryset filtered by current containers."""
        containers = self._base_queryset()
        return ContainerInspectionDefect.objects.filter(container__in=containers)

    def _defect_queryset_visual(self):
        """
        Return ContainerInspectionDefect queryset for visual chart KPIs,
        excluding 'total_defects' so it never appears in plotted chart data.
        """
        return self._defect_queryset().exclude(defect_type__name="total_defects")

    @action(detail=False, methods=["get"], url_path="filter-options")
    def filter_options(self, request):
        """
        GET /quality/kpis/container/filter-options/

        Returns distinct customer values for Container-specific filter selects.
        """
        customers = list(
            Container.objects.exclude(customer__isnull=True)
            .exclude(customer__exact="")
            .values_list("customer", flat=True)
            .distinct()
            .order_by("customer")
        )
        return Response({"customer": customers}, status=http_status.HTTP_200_OK)

    # ── Executive Summary ────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="executive-summary")
    def executive_summary(self, request):
        """
        GET /quality/kpis/container/executive-summary/

        Returns:
          - Total Containers
          - Average Pass Rate
          - Total Palettes Inspected
          - Total Rejected Palettes

        Response: [{"label": "Total Containers", "value": 7}, ...]
        """
        queryset = self._base_queryset()

        aggregates = queryset.aggregate(
            total=Count("id"),
            avg_pass=Avg("percentage_pass"),
            total_palettes=Sum("total_palette"),
            total_rejected=Sum("total_palette_rejected"),
        )

        total = aggregates["total"] or 0
        avg_pass = round(aggregates["avg_pass"] or 0, 2)
        total_palettes = aggregates["total_palettes"] or 0
        total_rejected = aggregates["total_rejected"] or 0

        result = [
            {"label": "Total Containers", "value": total},
            {"label": "Average Pass Rate", "value": avg_pass},
            {"label": "Total Palettes Inspected", "value": total_palettes},
            {"label": "Total Rejected Palettes", "value": total_rejected},
        ]

        serializer = ScalarMetricSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Containers by State ──────────────────────────────────

    @action(detail=False, methods=["get"], url_path="containers-by-state")
    def containers_by_state(self, request):
        """
        GET /quality/kpis/container/containers-by-state/

        Group by percentage_pass buckets:
          - "< 80%"
          - "80-90%"   (>= 80, < 90)
          - "90-95%"   (>= 90, <= 95)
          - "> 95%"    (> 95)

        Response: [{"name": "< 80%", "value": 3}, ...]
        All four ranges always present, even with zero count.
        """
        queryset = self._base_queryset()

        aggregated = (
            queryset
            .annotate(
                range_bucket=Case(
                    When(percentage_pass__lt=80, then=1),
                    When(percentage_pass__gte=80, percentage_pass__lt=90, then=2),
                    When(percentage_pass__gte=90, percentage_pass__lte=95, then=3),
                    When(percentage_pass__gt=95, then=4),
                    output_field=IntegerField(),
                )
            )
            .values("range_bucket")
            .annotate(count=Count("id"))
        )

        range_labels = {
            1: "< 80%",
            2: "80-90%",
            3: "90-95%",
            4: "> 95%",
        }

        result_dict = {
            range_labels[item["range_bucket"]]: item["count"]
            for item in aggregated
        }

        all_ranges = ["< 80%", "80-90%", "90-95%", "> 95%"]
        result = [{"name": r, "value": result_dict.get(r, 0)} for r in all_ranges]

        serializer = KpiDonutSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Trend KPIs ───────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="pass-rate-trend")
    def pass_rate_trend(self, request):
        """
        GET /quality/kpis/container/pass-rate-trend/

        Daily average pass rate trend. Grouped by Container.date, AVG(percentage_pass).
        Ordered by date ASC. Null dates excluded.

        Response: [{"name": "Pass Rate", "data": [{"x": "2025-01-10", "y": 85.0}, ...]}]
        """
        queryset = self._base_queryset()
        # Exclude null dates — trends require a date axis
        queryset = queryset.exclude(date__isnull=True)

        aggregated = (
            queryset
            .values(date_val=F("date"))
            .annotate(avg_pass=Avg("percentage_pass"))
            .order_by("date_val")
        )

        data_points = [
            {"x": item["date_val"].isoformat(), "y": round(item["avg_pass"], 2)}
            for item in aggregated
        ]

        result = [{"name": "Pass Rate", "data": data_points}]
        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="inspected-trend")
    def inspected_trend(self, request):
        """
        GET /quality/kpis/container/inspected-trend/

        Daily inspected palettes trend. Grouped by Container.date, SUM(total_palette).
        Ordered by date ASC. Null dates excluded.

        Response: [{"name": "Inspected", "data": [{"x": "2025-01-10", "y": 50}, ...]}]
        """
        queryset = self._base_queryset()
        queryset = queryset.exclude(date__isnull=True)

        aggregated = (
            queryset
            .values(date_val=F("date"))
            .annotate(total=Sum("total_palette"))
            .order_by("date_val")
        )

        data_points = [
            {"x": item["date_val"].isoformat(), "y": item["total"] or 0}
            for item in aggregated
        ]

        result = [{"name": "Inspected", "data": data_points}]
        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="rejected-trend")
    def rejected_trend(self, request):
        """
        GET /quality/kpis/container/rejected-trend/

        Daily rejected palettes trend. Grouped by Container.date, SUM(total_palette_rejected).
        Ordered by date ASC. Null dates excluded.

        Response: [{"name": "Rejected", "data": [{"x": "2025-01-10", "y": 5}, ...]}]
        """
        queryset = self._base_queryset()
        queryset = queryset.exclude(date__isnull=True)

        aggregated = (
            queryset
            .values(date_val=F("date"))
            .annotate(total=Sum("total_palette_rejected"))
            .order_by("date_val")
        )

        data_points = [
            {"x": item["date_val"].isoformat(), "y": item["total"] or 0}
            for item in aggregated
        ]

        result = [{"name": "Rejected", "data": data_points}]
        serializer = KpiSeriesSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Defect KPIs ──────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="top-defects")
    def top_defects(self, request):
        """
        GET /quality/kpis/container/top-defects/

        Top defect types by total amount from ContainerInspectionDefect.
        Source: ContainerInspectionDefect.defect_type.name, SUM(amount).
        Sorted by total DESC. Excludes 'total_defects' from chart data.

        Response: [{"label": "Broken Seal", "value": 13}, ...]
        """
        defect_qs = self._defect_queryset_visual()

        aggregated = (
            defect_qs
            .values(defect_name=F("defect_type__name"))
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        result = [
            {"label": item["defect_name"], "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiBarSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="defect-composition")
    def defect_composition(self, request):
        """
        GET /quality/kpis/container/defect-composition/

        Defect type composition (donut shape).
        Source: ContainerInspectionDefect, grouped by defect_type__name, SUM(amount).
        Excludes zero totals and 'total_defects' from chart data.
        Sorted by value DESC, name ASC.

        Response: [{"name": "Broken Seal", "value": 13}, ...]
        """
        defect_qs = self._defect_queryset_visual()

        aggregated = (
            defect_qs
            .values(defect_name=F("defect_type__name"))
            .annotate(total=Sum("amount"))
            .filter(total__gt=0)
            .order_by("-total", "defect_name")
        )

        result = [
            {"name": item["defect_name"], "value": item["total"]}
            for item in aggregated
        ]

        serializer = KpiDonutSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    # ── Worst Containers ─────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="worst-containers")
    def worst_containers(self, request):
        """
        GET /quality/kpis/container/worst-containers/

        Returns filtered containers ordered from worst pass rate to best.
        Tiebreaker: container_number ASC (deterministic).
        Accepts optional 'top' query param (default 5) to limit results.

        Response: [
          {
            "containerNumber": 101,
            "customer": "AlphaCorp",
            "passRate": 50.0,
            "rejectedPalettes": 15,
            "inspectionDate": "2025-01-11"
          },
          ...
        ]
        """
        queryset = self._base_queryset()
        queryset = queryset.order_by("percentage_pass", "container_number")

        # ── top-N support ────────────────────────────────────
        try:
            top = int(request.query_params.get("top", 5))
        except (ValueError, TypeError):
            top = 5
        if top < 1:
            top = 5
        queryset = queryset[:top]

        result = [
            {
                "containerNumber": c.container_number,
                "customer": c.customer,
                "passRate": c.percentage_pass,
                "rejectedPalettes": c.total_palette_rejected,
                "inspectionDate": c.date.isoformat() if c.date else None,
            }
            for c in queryset
        ]

        serializer = WorstContainerSerializer(result, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)
