"""
dashboard_contracts — Shared DTO contracts, bucket rules, labels, and KPI registries.

This module is the single source of truth for:
  - Container state bucket definitions (labels + boundaries shared by live/volatile)
  - Domain KPI key sets (which KPIs belong to each dashboard)
  - KPI registry (which serializer handles each KPI)
  - Shared field name and label constants

Live and volatile paths both reference these constants so the output contract
never diverges between ORM-aggregated and row-computed KPIs.

"""
# ─────────────────────────────────────────────────────────
# Supported dashboards
# ─────────────────────────────────────────────────────────

SUPPORTED_DASHBOARDS = {"qcfa", "container", "seconds_a4", "seconds_general"}

# ─────────────────────────────────────────────────────────
# Container domain
# ─────────────────────────────────────────────────────────

# Container state bucket definitions for Case/When (live) and python (volatile).
# Bucket ids: 1 = "< 80%", 2 = "80-90%", 3 = "90-95%", 4 = "> 95%"
CONTAINER_STATE_BUCKET_LABELS = {
    1: "< 80%",
    2: "80-90%",
    3: "90-95%",
    4: "> 95%",
}

ALL_CONTAINER_STATE_BUCKET_LABELS = ["< 80%", "80-90%", "90-95%", "> 95%"]

CONTAINER_EXECUTIVE_SUMMARY_LABELS = [
    "Total Containers",
    "Average Pass Rate",
    "Total Palettes Inspected",
    "Total Rejected Palettes",
]

CONTAINER_KPI_KEYS = {
    "executive_summary",
    "containers_by_state",
    "pass_rate_trend",
    "inspected_trend",
    "rejected_trend",
    "top_defects",
    "defect_composition",
    "worst_containers",
}

# Registry: (kpi_key, serializer_import_path, many)
# serializer_import_path is resolved at assembler runtime to avoid circular imports.
CONTAINER_KPI_REGISTRY = [
    ("executive_summary", "quality_data.serializers.ScalarMetricSerializer", True),
    ("containers_by_state", "quality_data.serializers.KpiDonutSerializer", True),
    ("pass_rate_trend", "quality_data.serializers.KpiSeriesSerializer", True),
    ("inspected_trend", "quality_data.serializers.KpiSeriesSerializer", True),
    ("rejected_trend", "quality_data.serializers.KpiSeriesSerializer", True),
    ("top_defects", "quality_data.serializers.KpiBarSerializer", True),
    ("defect_composition", "quality_data.serializers.KpiDonutSerializer", True),
    ("worst_containers", "quality_data.serializers.WorstContainerSerializer", True),
]

# ─────────────────────────────────────────────────────────
# Seconds A4 domain
# ─────────────────────────────────────────────────────────

SECONDS_A4_KPI_KEYS = {
    "filter_options",
    "executive_summary",
    "weekly_trend",
    "sew_vs_fab",
    "by_style",
    "by_color",
    "by_line",
    "by_cut",
    "pass_fail_weekly",
}

SECONDS_A4_KPI_REGISTRY = [
    ("filter_options", "quality_data.serializers.SecondsA4FilterOptionsSerializer", False),
    ("executive_summary", None, False),  # No serializer — raw dict is the contract
    ("weekly_trend", "quality_data.serializers.KpiSeriesSerializer", True),
    ("sew_vs_fab", "quality_data.serializers.KpiBarSerializer", True),
    ("by_style", "quality_data.serializers.KpiBarSerializer", True),
    ("by_color", "quality_data.serializers.KpiBarSerializer", True),
    ("by_line", "quality_data.serializers.KpiBarSerializer", True),
    ("by_cut", "quality_data.serializers.KpiBarSerializer", True),
    ("pass_fail_weekly", "quality_data.serializers.KpiSeriesSerializer", True),
]

# Seconds A4 sum fields (shared between live and volatile)
SECONDS_A4_SUM_FIELDS = [
    "total_of_2ds",
    "seconds_by_sew",
    "seconds_by_fab",
    "seconds_sew_a4",
    "seconds_fab_a4",
    "accepted",
    "rejected",
]

# ─────────────────────────────────────────────────────────
# Seconds General domain
# ─────────────────────────────────────────────────────────

SECONDS_GENERAL_KPI_KEYS = {
    "filter_options",
    "defects_by_customer",
    "defects_by_style",
    "weekly_trend",
    "sewing_vs_fabric",
    "production_totals",
    "top_sewing_defects",
    "top_fabric_defects",
    "fix_vs_definitive",
    "defects_by_color",
    "defects_by_size",
    "defects_by_line",
}

SECONDS_GENERAL_KPI_REGISTRY = [
    ("filter_options", None, False),  # No serializer — raw dict is the contract
    ("defects_by_customer", "quality_data.serializers.KpiBarSerializer", True),
    ("defects_by_style", "quality_data.serializers.KpiBarSerializer", True),
    ("weekly_trend", "quality_data.serializers.KpiSeriesSerializer", True),
    ("sewing_vs_fabric", "quality_data.serializers.KpiBarSerializer", True),
    ("production_totals", None, False),  # No serializer — raw dict is the contract
    ("top_sewing_defects", "quality_data.serializers.KpiBarSerializer", True),
    ("top_fabric_defects", "quality_data.serializers.KpiBarSerializer", True),
    ("fix_vs_definitive", "quality_data.serializers.KpiSeriesSerializer", True),
    ("defects_by_color", "quality_data.serializers.KpiBarSerializer", True),
    ("defects_by_size", "quality_data.serializers.KpiBarSerializer", True),
    ("defects_by_line", "quality_data.serializers.KpiBarSerializer", True),
]

# Seconds General production fields
SG_PRODUCTION_FIELDS = ["produced", "fixed", "definitive"]

# ─────────────────────────────────────────────────────────
# QC FA domain
# ─────────────────────────────────────────────────────────

QCFA_KPI_KEYS = {
    "aql_by_style",
    "aql_by_team",
    "aql_weekly",
    "audited_pieces",
    "ac_re_rate_by_line",
    "seconds_rework",
    "performance_by_customer",
    "performance_by_line",
    "top_defects",
    "fabric_defects",
    "defects_by_style_type",
    "pass_reject_distribution",
    "rejected_evolution",
    "containers_by_state",
    "defect_rate",
    "defect_composition",
    "defect_trend_top_3",
    "filter_options",
}

QCFA_KPI_REGISTRY = [
    ("aql_by_style", "quality_data.serializers.KpiBarSerializer", True),
    ("aql_by_team", "quality_data.serializers.KpiBarSerializer", True),
    ("aql_weekly", "quality_data.serializers.KpiSeriesSerializer", True),
    ("audited_pieces", "quality_data.serializers.KpiSeriesSerializer", True),
    ("ac_re_rate_by_line", "quality_data.serializers.KpiBarSerializer", True),
    ("seconds_rework", "quality_data.serializers.KpiSeriesSerializer", True),
    ("performance_by_customer", "quality_data.serializers.KpiBarSerializer", True),
    ("performance_by_line", "quality_data.serializers.KpiBarSerializer", True),
    ("top_defects", "quality_data.serializers.KpiBarSerializer", True),
    ("fabric_defects", "quality_data.serializers.KpiBarSerializer", True),
    ("defects_by_style_type", "quality_data.serializers.KpiHeatmapSerializer", True),
    ("pass_reject_distribution", "quality_data.serializers.KpiDonutSerializer", True),
    ("rejected_evolution", "quality_data.serializers.KpiSeriesSerializer", True),
    ("containers_by_state", "quality_data.serializers.KpiDonutSerializer", True),
    ("defect_rate", "quality_data.serializers.ScalarMetricSerializer", False),
    ("defect_composition", "quality_data.serializers.KpiDonutSerializer", True),
    ("defect_trend_top_3", "quality_data.serializers.KpiSeriesSerializer", True),
    # filter_options is conditionally present — added from VolatileKpiView for QCFA
    ("filter_options", "quality_data.serializers.FilterOptionsSerializer", False),
]
