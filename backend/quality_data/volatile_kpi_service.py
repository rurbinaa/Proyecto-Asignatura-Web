"""
Volatile KPI Service — Shared workbook parsing and dashboard dispatch for Fast Mode.

Opens the Excel file once (``pd.ExcelFile``) and parses sheets on demand
via ``load_and_clean(..., excel_file=...)`` to avoid repeated I/O.

Dashboard dispatch:
    - ``qcfa`` (+ ``context=plant|customer``) → QC FA Plant / Customer rows.
    - ``container`` → Container rows (named tuple ready for KPI compute).
    - ``seconds_a4`` → SecondsA4 rows.
    - ``seconds_general`` → Seconds General rows.

Usage::

    service = VolatileWorkbookService(file_obj)
    rows, defect_fields = service.get_parsed_data("qcfa", context="customer")
"""

import pandas as pd

from excel_importer.handler_service import (
    load_and_clean,
    normalize_container_rows,
    normalize_qc_fa_customer_rows,
)
from quality_data.dashboard_contracts import ALL_CONTAINER_STATE_BUCKET_LABELS
from excel_importer.sheet_configs import (
    CONTAINER_AMOUNT_DEFEACTS_FIELDS,
    CONTAINER_NUMERIC_COLUMNS,
    CONTAINER_REMAP,
    QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
    QC_FA_CUSTOMER_NUMERIC_COLUMNS,
    QC_FA_CUSTOMER_REMAP,
    QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
    QC_FA_PLANT_NUMERIC_COLUMNS,
    QC_FA_PLANT_REMAP,
    SECONDS_A4_NUMERIC_COLUMNS,
    SECONDS_A4_REMAP,
    SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS,
    SECONDS_GENERAL_FABRIC_DEFECTS,
    SECONDS_GENERAL_NUMERIC_COLUMNS,
    SECONDS_GENERAL_REMAP,
    SECONDS_GENERAL_SEWING_DEFECTS,
    SHEET_NAMES,
)

# ─────────────────────────────────────────────────────────
# Dashboard → (sheet_index, remap, numeric_cols, defect_fields)
# ─────────────────────────────────────────────────────────

DASHBOARD_SHEET_MAP = {
    "qcfa": {
        "plant": {
            "sheet_idx": 0,  # QC FA Plant
            "remap": QC_FA_PLANT_REMAP,
            "numeric_cols": QC_FA_PLANT_NUMERIC_COLUMNS,
            "defect_fields": QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
        },
        "customer": {
            "sheet_idx": 1,  # QC FA Customer
            "remap": QC_FA_CUSTOMER_REMAP,
            "numeric_cols": QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            "defect_fields": QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
        },
    },
    "container": {
        "plant": {  # Container has no plant/customer distinction; context ignored.
            "sheet_idx": 4,
            "remap": CONTAINER_REMAP,
            "numeric_cols": CONTAINER_NUMERIC_COLUMNS,
            "defect_fields": CONTAINER_AMOUNT_DEFEACTS_FIELDS,
        },
    },
    "seconds_a4": {
        "plant": {
            "sheet_idx": 2,
            "remap": SECONDS_A4_REMAP,
            "numeric_cols": SECONDS_A4_NUMERIC_COLUMNS,
            "defect_fields": None,
        },
    },
    "seconds_general": {
        "plant": {
            "sheet_idx": 3,
            "remap": SECONDS_GENERAL_REMAP,
            "numeric_cols": SECONDS_GENERAL_NUMERIC_COLUMNS,
            "defect_fields": SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS,
        },
    },
}


class VolatileWorkbookService:
    """
    Opens an Excel file once and provides parsed sheets on demand.

    Attributes:
        file_obj: Seekable file-like object (used as fallback).
        excel_file: ``pd.ExcelFile`` instance or ``None``.
    """

    def __init__(self, file_obj):
        self.file_obj = file_obj
        try:
            self.excel_file = pd.ExcelFile(file_obj, engine="openpyxl")
        except Exception:
            self.excel_file = None

    def parse_sheet(self, remap, numeric_cols, defect_fields, sheet_name, header, cols):
        """Parse a single sheet via ``load_and_clean`` with the shared ExcelFile."""
        try:
            return load_and_clean(
                self.file_obj,
                remap,
                numeric_cols,
                defect_fields,
                sheet_name,
                header,
                cols,
                excel_file=self.excel_file,
            )
        except Exception:
            # Return empty DataFrame when the sheet cannot be read
            # (e.g. invalid file, missing sheet, mock data in tests).
            import pandas as pd
            return pd.DataFrame()

    def get_parsed_data(self, dashboard, context="plant"):
        """
        Parse the sheet(s) needed for *dashboard* and return ``(rows, defect_fields)``.

        Args:
            dashboard: One of ``"qcfa"``, ``"container"``, ``"seconds_a4"``,
                       ``"seconds_general"``.
            context: ``"plant"`` (default) or ``"customer"`` (only meaningful for QC FA).

        Returns:
            tuple: ``(list_of_dicts, list_of_defect_field_names_or_None)``.
        """
        context_key = context if context in ("plant", "customer") else "plant"
        cfg = DASHBOARD_SHEET_MAP.get(dashboard, {}).get(context_key)
        if cfg is None:
            # Fall back to the first available context for this dashboard
            contexts = DASHBOARD_SHEET_MAP.get(dashboard, {})
            cfg = next(iter(contexts.values())) if contexts else None
        if cfg is None:
            return [], None

        sheet_idx = cfg["sheet_idx"]
        sheet_name, header, cols = SHEET_NAMES[sheet_idx]
        df = self.parse_sheet(
            cfg["remap"],
            cfg["numeric_cols"],
            cfg["defect_fields"],
            sheet_name,
            header,
            cols,
        )
        rows = df.to_dict("records")
        defect_fields = cfg["defect_fields"]

        # Normalize QC FA Customer rows at the import boundary
        if dashboard == "qcfa" and context_key == "customer":
            normalized, _ = normalize_qc_fa_customer_rows(rows)
            return normalized, defect_fields

        # Normalize Container rows at the import boundary (Slice 3)
        if dashboard == "container":
            normalized, _ = normalize_container_rows(rows)
            return normalized, defect_fields

        return rows, defect_fields


# ─────────────────────────────────────────────────────────
# Container KPI computation helpers (volatile / fast mode)
# ─────────────────────────────────────────────────────────


def _normalize_container_percentage(value):
    """
    Normalize a container percentage value from fractional (0-1) to 0-100 scale.

    Excel sometimes stores percentages as 0-1 fractions (e.g. 97% → 0.97).
    Values already on 0-100 scale or null/None are returned unchanged.
    """
    if value is not None and isinstance(value, (int, float)) and 0 < value <= 1:
        return round(value * 100, 2)
    return value


def _safe_defect_int(value):
    """
    Convert a defect field value to int, safely handling NaN/None/float.
    """
    import math
    if value is None:
        return 0
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def calc_container_executive_summary(rows):
    """
    Compute Container executive summary from parsed volatile rows.

    Returns::
        [{"label": "Total Containers", "value": int},
         {"label": "Average Pass Rate", "value": float},
         {"label": "Total Palettes Inspected", "value": int},
         {"label": "Total Rejected Palettes", "value": int}]
    """
    if not rows:
        return [
            {"label": "Total Containers", "value": 0},
            {"label": "Average Pass Rate", "value": 0},
            {"label": "Total Palettes Inspected", "value": 0},
            {"label": "Total Rejected Palettes", "value": 0},
        ]

    total = len(rows)
    pass_rates = [_normalize_container_percentage(r.get("percentage_pass", 0)) for r in rows]
    avg_pass = round(sum(p for p in pass_rates if p is not None) / total, 2) if total > 0 else 0
    total_palettes = sum(int(r.get("total_palette", 0) or 0) for r in rows)
    total_rejected = sum(int(r.get("total_palette_rejected", 0) or 0) for r in rows)

    return [
        {"label": "Total Containers", "value": total},
        {"label": "Average Pass Rate", "value": avg_pass},
        {"label": "Total Palettes Inspected", "value": total_palettes},
        {"label": "Total Rejected Palettes", "value": total_rejected},
    ]


def calc_container_state_distribution(rows):
    """
    Group container rows by percentage_pass bucket.

    Buckets: < 80%, 80-90%, 90-95%, > 95%
    All four ranges always present, even with zero count.
    """
    buckets = {label: 0 for label in ALL_CONTAINER_STATE_BUCKET_LABELS}

    for r in rows:
        pct = _normalize_container_percentage(r.get("percentage_pass", 0))
        if pct is None:
            continue
        if pct < 80:
            buckets[ALL_CONTAINER_STATE_BUCKET_LABELS[0]] += 1
        elif pct < 90:
            buckets[ALL_CONTAINER_STATE_BUCKET_LABELS[1]] += 1
        elif pct <= 95:
            buckets[ALL_CONTAINER_STATE_BUCKET_LABELS[2]] += 1
        else:
            buckets[ALL_CONTAINER_STATE_BUCKET_LABELS[3]] += 1

    return [{"name": k, "value": v} for k, v in buckets.items()]


def _container_trend(rows, date_field, value_field, agg_func="sum", series_name=None):
    """
    Build a date-series trend from container rows.

    Groups by *date_field*, applies *agg_func* to *value_field*.
    Rows with null/missing dates are excluded.

    Returns::
        [{"name": str, "data": [{"x": date_str, "y": value}, ...]}]
    """
    import pandas as pd

    if not rows:
        name = series_name or value_field.replace("_", " ").title()
        return [{"name": name, "data": []}]

    df = pd.DataFrame(rows)
    if date_field not in df.columns:
        name = series_name or value_field.replace("_", " ").title()
        return [{"name": name, "data": []}]

    # Exclude null dates
    df = df.dropna(subset=[date_field])
    if df.empty:
        name = series_name or value_field.replace("_", " ").title()
        return [{"name": name, "data": []}]

    if agg_func == "sum":
        grouped = df.groupby(date_field).agg(total=(value_field, "sum")).reset_index()
    elif agg_func == "avg":
        grouped = df.groupby(date_field).agg(total=(value_field, "mean")).reset_index()
    else:
        grouped = df.groupby(date_field).agg(total=(value_field, agg_func)).reset_index()

    grouped = grouped.sort_values(date_field)

    data_points = []
    for _, row in grouped.iterrows():
        date_val = row[date_field]
        if hasattr(date_val, "isoformat"):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val)
        y_val = row["total"]
        if isinstance(y_val, float):
            y_val = round(y_val, 2)
        else:
            y_val = int(y_val or 0)
        data_points.append({"x": date_str, "y": y_val})

    name = series_name or value_field.replace("_", " ").title()
    return [{"name": name, "data": data_points}]


def calc_container_pass_rate_trend(rows):
    """Daily average pass rate. Returns series list."""
    return _container_trend(rows, "date", "percentage_pass", agg_func="avg", series_name="Pass Rate")


def calc_container_inspected_trend(rows):
    """Daily inspected palettes. Returns series list."""
    return _container_trend(rows, "date", "total_palette", agg_func="sum", series_name="Inspected")


def calc_container_rejected_trend(rows):
    """Daily rejected palettes. Returns series list."""
    return _container_trend(rows, "date", "total_palette_rejected", agg_func="sum", series_name="Rejected")


def calc_container_top_defects(rows, defect_fields):
    """
    Sum each defect field across all container rows, excluding 'total_defects'.

    Returns::
        [{"label": str, "value": int}, ...]
        Sorted by value DESC. Empty list if no defects.
    """
    if not rows or not defect_fields:
        return []

    totals = {}
    for field in defect_fields:
        if field == "total_defects":
            continue
        total = sum(_safe_defect_int(r.get(field)) for r in rows)
        if total > 0:
            label = field.replace("_", " ").title()
            totals[label] = totals.get(label, 0) + total

    result = [{"label": k, "value": v} for k, v in totals.items()]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result


def calc_container_defect_composition(rows, defect_fields):
    """
    Same as top defects but with ``name`` key for donut charts.
    Excludes zero totals and ``total_defects``.
    Sorted by value DESC, name ASC.

    Returns::
        [{"name": str, "value": int}, ...]
    """
    if not rows or not defect_fields:
        return []

    totals = {}
    for field in defect_fields:
        if field == "total_defects":
            continue
        total = sum(_safe_defect_int(r.get(field)) for r in rows)
        if total > 0:
            label = field.replace("_", " ").title()
            totals[label] = totals.get(label, 0) + total

    result = [{"name": k, "value": v} for k, v in totals.items()]
    result.sort(key=lambda x: (-x["value"], x["name"]))
    return result


def calc_container_worst_containers(rows, top=5):
    """
    Return containers sorted by percentage_pass ASC (worst first).
    Tiebreaker: container_number ASC.

    Returns::
        [{"containerNumber": int, "customer": str, "passRate": float,
          "rejectedPalettes": int, "inspectionDate": str or None}, ...]
    """
    if not rows:
        return []

    # Sort by percentage_pass ASC, container_number ASC
    sorted_rows = sorted(
        rows,
        key=lambda r: (
            _normalize_container_percentage(r.get("percentage_pass", 0)) or 0,
            int(r.get("container_number", 0) or 0),
        ),
    )

    result = []
    for r in sorted_rows[:top]:
        raw_date = r.get("date")
        date_str = None
        if raw_date is not None:
            try:
                from datetime import date as date_cls
                if isinstance(raw_date, (date_cls,)):
                    date_str = raw_date.isoformat()
                else:
                    date_str = str(raw_date)
            except Exception:
                date_str = str(raw_date)

        result.append({
            "containerNumber": int(r.get("container_number", 0) or 0),
            "customer": str(r.get("customer", "") or ""),
            "passRate": _normalize_container_percentage(r.get("percentage_pass", 0)) or 0,
            "rejectedPalettes": int(r.get("total_palette_rejected", 0) or 0),
            "inspectionDate": date_str,
        })

    return result


# ─────────────────────────────────────────────────────────
# Seconds A4 KPI computation helpers (volatile / fast mode)
# ─────────────────────────────────────────────────────────


_SECONDS_A4_SUM_FIELDS = [
    "total_of_2ds",
    "seconds_by_sew",
    "seconds_by_fab",
    "seconds_sew_a4",
    "seconds_fab_a4",
    "accepted",
    "rejected",
]


def _safe_a4_int(value):
    """Convert a Seconds A4 numeric field to int, safely handling NaN/None."""
    import math
    if value is None:
        return 0
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def calc_seconds_a4_executive_summary(rows):
    """
    Compute Seconds A4 executive summary (totals + empty percentages).

    Matches the live endpoint contract exactly::
        {"totals": {total_of_2ds, seconds_by_sew, seconds_by_fab,
                    seconds_sew_a4, seconds_fab_a4, accepted, rejected},
         "percentages": []}
    """
    totals = {field: 0 for field in _SECONDS_A4_SUM_FIELDS}
    for r in rows:
        for field in _SECONDS_A4_SUM_FIELDS:
            totals[field] += _safe_a4_int(r.get(field))

    return {"totals": totals, "percentages": []}


def calc_seconds_a4_weekly_trend(rows):
    """
    Compute weekly total_of_2ds trend series.

    Returns::
        [{"name": "2DS", "data": [{"x": "2025-W1", "y": int}, ...]}]
    """
    if not rows:
        return [{"name": "2DS", "data": []}]

    # Group by (year, week), sum total_of_2ds
    import pandas as pd
    df = pd.DataFrame(rows)
    if "year" not in df.columns or "week" not in df.columns:
        return [{"name": "2DS", "data": []}]

    # Fill NaN in total_of_2ds
    df["total_of_2ds"] = pd.to_numeric(df.get("total_of_2ds", 0), errors="coerce").fillna(0)

    grouped = (
        df.groupby(["year", "week"])["total_of_2ds"]
        .sum()
        .reset_index()
        .sort_values(["year", "week"])
    )

    data_points = [
        {"x": f'{int(r["year"])}-W{int(r["week"])}', "y": int(r["total_of_2ds"])}
        for _, r in grouped.iterrows()
    ]

    return [{"name": "2DS", "data": data_points}]


def calc_seconds_a4_sew_vs_fab(rows):
    """Sum seconds_by_sew and seconds_by_fab across all rows.

    Returns::
        [{"label": "Sew", "value": int}, {"label": "Fabric", "value": int}]
    """
    totals = {"sew": 0, "fab": 0}
    for r in rows:
        totals["sew"] += _safe_a4_int(r.get("seconds_by_sew"))
        totals["fab"] += _safe_a4_int(r.get("seconds_by_fab"))

    return [
        {"label": "Sew", "value": totals["sew"]},
        {"label": "Fabric", "value": totals["fab"]},
    ]


def _seconds_a4_group_sum(rows, group_field, value_field="total_of_2ds", label_transform=None):
    """
    Generic group-by-sum helper for Seconds A4 KPIs.

    Args:
        rows: List of dict rows.
        group_field: The field to group by (e.g., "style", "color", "line", "cut_num").
        value_field: The field to sum (default "total_of_2ds").
        label_transform: Optional callable to transform the raw group value into a label.
            If None, uses the raw value as label (converted to string).

    Returns::
        [{"label": str, "value": int}, ...] sorted by value DESC.
    """
    from collections import defaultdict

    totals = defaultdict(int)
    for r in rows:
        key = r.get(group_field)
        if key is None:
            continue
        totals[key] += _safe_a4_int(r.get(value_field))

    if label_transform is None:
        label_transform = str

    result = [
        {"label": label_transform(k), "value": v}
        for k, v in totals.items()
        if v > 0
    ]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result


def calc_seconds_a4_by_style(rows):
    """Seconds A4 total_of_2ds grouped by style.

    Returns:: [{"label": "STYLE-A", "value": int}, ...]
    """
    return _seconds_a4_group_sum(rows, "style")


def calc_seconds_a4_by_color(rows):
    """Seconds A4 total_of_2ds grouped by color.

    Returns:: [{"label": "Red", "value": int}, ...]
    """
    return _seconds_a4_group_sum(rows, "color")


def calc_seconds_a4_by_line(rows):
    """Seconds A4 total_of_2ds grouped by line.

    Returns:: [{"label": "L1", "value": int}, ...]
    """
    return _seconds_a4_group_sum(rows, "line")


def calc_seconds_a4_by_cut(rows):
    """Seconds A4 total_of_2ds grouped by cut number.

    Returns:: [{"label": "Cut 101", "value": int}, ...]
    """
    return _seconds_a4_group_sum(
        rows, "cut_num", label_transform=lambda v: f"Cut {int(v)}",
    )


def calc_seconds_a4_pass_fail_weekly(rows):
    """
    Compute weekly pass vs fail series from Seconds A4 rows.

    Returns::
        [{"name": "Pass", "data": [{"x": "2025-W1", "y": int}, ...]},
         {"name": "Fail", "data": [{"x": "2025-W1", "y": int}, ...]}]
    """
    if not rows:
        return [{"name": "Pass", "data": []}, {"name": "Fail", "data": []}]

    import pandas as pd
    df = pd.DataFrame(rows)

    for col in ["year", "week", "pass_field", "fail_field"]:
        if col not in df.columns:
            return [{"name": "Pass", "data": []}, {"name": "Fail", "data": []}]

    # Filter out invalid year/week
    df = df[(df["year"] > 0) & (df["week"] >= 1) & (df["week"] <= 53)]

    if df.empty:
        return [{"name": "Pass", "data": []}, {"name": "Fail", "data": []}]

    df["pass_field"] = pd.to_numeric(df["pass_field"], errors="coerce").fillna(0)
    df["fail_field"] = pd.to_numeric(df["fail_field"], errors="coerce").fillna(0)

    grouped = (
        df.groupby(["year", "week"])
        .agg(total_pass=("pass_field", "sum"), total_fail=("fail_field", "sum"))
        .reset_index()
        .sort_values(["year", "week"])
    )

    pass_data = [
        {"x": f'{int(r["year"])}-W{int(r["week"])}', "y": int(r["total_pass"])}
        for _, r in grouped.iterrows()
    ]
    fail_data = [
        {"x": f'{int(r["year"])}-W{int(r["week"])}', "y": int(r["total_fail"])}
        for _, r in grouped.iterrows()
    ]

    return [
        {"name": "Pass", "data": pass_data},
        {"name": "Fail", "data": fail_data},
    ]


def calc_seconds_a4_filter_options(rows):
    """
    Compute distinct filter options from Seconds A4 rows.

    Returns::
        {"year": [...], "week": [...], "line": [...],
         "cut_num": [...], "style": [...], "color": [...]}
    """
    if not rows:
        return {
            "year": [], "week": [], "line": [],
            "cut_num": [], "style": [], "color": [],
        }

    import pandas as pd
    df = pd.DataFrame(rows)

    def _sorted_unique(col):
        if col not in df.columns:
            return []
        vals = df[col].dropna().unique().tolist()
        if col in ("year", "week", "cut_num"):
            numeric = [v for v in vals if isinstance(v, (int, float))]
            numeric = sorted({int(v) for v in numeric})
            return numeric
        else:
            string_vals = sorted([str(v) for v in vals if v is not None and str(v).strip()])
            return string_vals

    return {
        "year": _sorted_unique("year"),
        "week": _sorted_unique("week"),
        "line": _sorted_unique("line"),
        "cut_num": _sorted_unique("cut_num"),
        "style": _sorted_unique("style"),
        "color": _sorted_unique("color"),
    }


# ─────────────────────────────────────────────────────────
# Seconds General KPI computation helpers (volatile / fast mode)
# ─────────────────────────────────────────────────────────

_SG_PRODUCTION_FIELDS = ["produced", "fixed", "definitive"]


def _sg_safe_int(value):
    """Convert a Seconds General value to int, safely handling NaN/None."""
    import math
    if value is None:
        return 0
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _sg_sum_defects(rows, defect_fields):
    """
    Sum each defect field across all rows.

    Returns a dict mapping field_name → total (int).
    """
    from collections import defaultdict
    totals = defaultdict(int)
    for r in rows:
        for field in defect_fields:
            totals[field] += _sg_safe_int(r.get(field))
    return dict(totals)


def _sg_group_sum(rows, group_field, defect_fields):
    """
    Group rows by *group_field* and sum all defect fields per group.

    Returns::
        [{"label": str, "value": int}, ...]
        Sorted by value DESC.
    """
    from collections import defaultdict
    group_totals = defaultdict(int)
    for r in rows:
        key = r.get(group_field)
        if key is None:
            continue
        for field in defect_fields:
            group_totals[key] += _sg_safe_int(r.get(field))
    result = [{"label": str(k), "value": v} for k, v in group_totals.items() if v > 0]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result


def _sg_weekly_production(rows, value_field):
    """
    Group rows by week and sum *value_field*.

    Returns::
        [{"x": week, "y": int}, ...]
        Sorted by week ASC.
    """
    from collections import defaultdict
    weekly = defaultdict(int)
    for r in rows:
        week = r.get("week")
        if week is None:
            continue
        weekly[week] += _sg_safe_int(r.get(value_field))
    result = [{"x": int(k), "y": v} for k, v in sorted(weekly.items())]
    return result


def _sg_weekly_defects(rows, defect_fields):
    """
    Group rows by week and sum all defect fields.

    Returns::
        [{"x": week, "y": int}, ...]
        Sorted by week ASC.
    """
    from collections import defaultdict
    weekly = defaultdict(int)
    for r in rows:
        week = r.get("week")
        if week is None:
            continue
        total = sum(_sg_safe_int(r.get(f)) for f in defect_fields)
        weekly[week] += total
    result = [{"x": int(k), "y": v} for k, v in sorted(weekly.items())]
    return result


def calc_seconds_general_filter_options(rows):
    """
    Compute distinct filter options from Seconds General rows.

    Returns::
        {"customer": [...], "style": [...], "week": [...],
         "color": [...], "size": [...], "team": [...]}
    """
    if not rows:
        return {
            "customer": [], "style": [], "week": [],
            "color": [], "size": [], "team": [],
        }

    import pandas as pd
    df = pd.DataFrame(rows)

    def _sorted_unique(col):
        if col not in df.columns:
            return []
        vals = df[col].dropna().unique().tolist()
        if col in ("week", "team"):
            numeric = [v for v in vals if isinstance(v, (int, float))]
            numeric = sorted({int(v) for v in numeric})
            return numeric
        else:
            string_vals = sorted([str(v) for v in vals if v is not None and str(v).strip()])
            return string_vals

    return {
        "customer": _sorted_unique("customer"),
        "style": _sorted_unique("style"),
        "week": _sorted_unique("week"),
        "color": _sorted_unique("color"),
        "size": _sorted_unique("size"),
        "team": _sorted_unique("team"),
    }


def calc_seconds_general_production_totals(rows):
    """
    Compute Seconds General production totals.

    Returns::
        {"total_produced": int, "total_fixed": int, "total_definitive": int}
    """
    totals = {"total_produced": 0, "total_fixed": 0, "total_definitive": 0}
    for r in rows:
        totals["total_produced"] += _sg_safe_int(r.get("produced"))
        totals["total_fixed"] += _sg_safe_int(r.get("fixed"))
        totals["total_definitive"] += _sg_safe_int(r.get("definitive"))
    return totals


def calc_seconds_general_defects_by_customer(rows):
    """Group defects by customer. Returns ``[{"label": str, "value": int}, ...]``."""
    return _sg_group_sum(rows, "customer", SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)


def calc_seconds_general_defects_by_style(rows):
    """Group defects by style. Returns ``[{"label": str, "value": int}, ...]``."""
    return _sg_group_sum(rows, "style", SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)


def calc_seconds_general_weekly_trend(rows):
    """
    Weekly defect total trend.

    Returns::
        [{"name": "Defects", "data": [{"x": week, "y": int}, ...]}]
    """
    data = _sg_weekly_defects(rows, SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)
    return [{"name": "Defects", "data": data}]


def calc_seconds_general_sewing_vs_fabric(rows):
    """
    Compute sewing vs fabric defect totals.

    Returns::
        [{"label": "Sewing", "value": int}, {"label": "Fabric", "value": int}]
    """
    sewing = sum(_sg_safe_int(r.get(f)) for r in rows for f in SECONDS_GENERAL_SEWING_DEFECTS)
    fabric = sum(_sg_safe_int(r.get(f)) for r in rows for f in SECONDS_GENERAL_FABRIC_DEFECTS)
    return [
        {"label": "Sewing", "value": sewing},
        {"label": "Fabric", "value": fabric},
    ]


def calc_seconds_general_top_sewing_defects(rows, top=10):
    """
    Sum each sewing defect field across all rows.

    Returns::
        [{"label": str, "value": int}, ...]
        Sorted by value DESC, limited to *top*.
    """
    totals = _sg_sum_defects(rows, SECONDS_GENERAL_SEWING_DEFECTS)
    result = [{"label": k, "value": v} for k, v in totals.items() if v > 0]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result[:top]


def calc_seconds_general_top_fabric_defects(rows, top=10):
    """
    Sum each fabric defect field across all rows.

    Returns::
        [{"label": str, "value": int}, ...]
        Sorted by value DESC, limited to *top*.
    """
    totals = _sg_sum_defects(rows, SECONDS_GENERAL_FABRIC_DEFECTS)
    result = [{"label": k, "value": v} for k, v in totals.items() if v > 0]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result[:top]


def calc_seconds_general_fix_vs_definitive(rows):
    """
    Compute weekly fix vs definitive series.

    Returns::
        [{"name": "Fixed", "data": [{"x": week, "y": int}, ...]},
         {"name": "Definitive", "data": [{"x": week, "y": int}, ...]}]
    """
    fixed_data = _sg_weekly_production(rows, "fixed")
    definitive_data = _sg_weekly_production(rows, "definitive")
    return [
        {"name": "Fixed", "data": fixed_data},
        {"name": "Definitive", "data": definitive_data},
    ]


def calc_seconds_general_defects_by_color(rows):
    """Group defects by color. Returns ``[{"label": str, "value": int}, ...]``."""
    return _sg_group_sum(rows, "color", SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)


def calc_seconds_general_defects_by_size(rows):
    """Group defects by size. Returns ``[{"label": str, "value": int}, ...]``."""
    return _sg_group_sum(rows, "size", SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)


def calc_seconds_general_defects_by_line(rows):
    """
    Group defects by team (display as "Line N").

    Returns::
        [{"label": "Line 1", "value": int}, ...]
        Sorted by value DESC.
    """
    from collections import defaultdict
    group_totals = defaultdict(int)
    for r in rows:
        team = r.get("team")
        if team is None:
            continue
        try:
            team_val = int(team)
        except (ValueError, TypeError):
            continue
        total = sum(_sg_safe_int(r.get(f)) for f in SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS)
        group_totals[team_val] += total

    result = [
        {"label": f"Line {k}", "value": v}
        for k, v in group_totals.items()
        if v > 0
    ]
    result.sort(key=lambda x: (-x["value"], x["label"]))
    return result
