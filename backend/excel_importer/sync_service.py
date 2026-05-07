"""
Excel Sync Service — Hybrid Sync with Preview.

Implements two sync strategies:
- UPSERT: For sheets with natural PKs (SecondsA4, Container)
- Time-Window Sync: For sheets without PKs (QC FA Plant, QC FA Customer, Seconds General)

The flow is: parse_excel → compute_preview → apply (with user confirmation)
"""

from django.db import transaction
from quality_data.models import (
    QualityQcFa,
    SecondsA4,
    SecondsGeneral,
    Container,
    Color,
    ExcelSyncSession,
)
from excel_importer.date_utils import (
    normalize_container_date,
    parse_date,
    canonicalize_qc_fa_date,
)

import logging

logger = logging.getLogger(__name__)


def _resolve_colors_batch(color_names):
    """
    Resolve a set of color name strings to Color instances in O(1) queries.

    Loads existing colors in 1 query, bulk-creates any missing ones, and
    returns a `{name: Color}` map for O(1) lookups during row processing.

    Args:
        color_names: iterable of lowercased, underscore-normalized color name strings.

    Returns:
        dict mapping color name (str) → Color instance.
    """
    if not color_names:
        return {}

    unique_names = set(color_names)
    existing = Color.objects.filter(name__in=unique_names)
    existing_map = {c.name: c for c in existing}

    missing = [Color(name=n, is_active=True) for n in unique_names if n not in existing_map]
    if missing:
        Color.objects.bulk_create(missing, ignore_conflicts=True)
        # Re-fetch to get PKs for the newly created colors
        refreshed = Color.objects.filter(name__in=unique_names)
        existing_map = {c.name: c for c in refreshed}

    return existing_map


def _collect_sheet_colors(rows, color_field="color"):
    """
    Extract unique color names from a list of row dicts.

    Returns a set of lowercased, underscore-normalized color name strings.
    """
    colors = set()
    for row in (rows or []):
        raw = str(row.get(color_field, "")).strip().lower().replace(" ", "_")
        if raw and raw != "unknown":
            colors.add(raw)
    return colors


def build_seconds_a4_key(row):
    """
    Build natural key for SecondsA4: (date, cut_num, color).

    This is the unique combination that identifies a SecondsA4 record.
    """
    date = parse_date(row.get("date", ""))
    cut_num = row.get("cut_num", 0)
    color = str(row.get("color", "")).strip().lower().replace(" ", "_")
    return (date, int(cut_num) if cut_num else 0, color)


def build_container_key(row):
    """
    Build natural key for Container: (container_number,).

    Container number is globally unique.
    """
    container_number = row.get("container_number", 0)
    return (int(container_number) if container_number else 0,)


def build_qc_fa_plant_key(row):
    """
    Build composite key for QC FA Plant (not a true PK, used for diff matching).

    Uses: date_1 + po + style + team + color
    This helps identify "likely same inspection" for preview purposes.
    """
    date = parse_date(row.get("date_1", ""))
    po = row.get("po", 0)
    style = str(row.get("style", "")).strip()
    team = row.get("team", 0)
    color = str(row.get("color", "")).strip().lower().replace(" ", "_")
    return (date, int(po) if po else 0, style, int(team) if team else 0, color)


def build_qc_fa_customer_key(row):
    """
    Build composite key for QC FA Customer (not a true PK, used for diff matching).

    Uses: date_1 + po + style + color + team + line_code
    This helps identify "likely same inspection" for preview purposes.
    Dual-line rows with the same team but different line_code are distinct.
    """
    date = parse_date(row.get("date_1", ""))
    po = row.get("po", 0)
    style = str(row.get("style", "")).strip()
    color = str(row.get("color", "")).strip().lower().replace(" ", "_")
    team = int(row.get("team", 0)) if row.get("team") else 0
    line_code = row.get("line_code", None) or None
    return (date, int(po) if po else 0, style, color, team, line_code)


def build_seconds_general_key(row):
    """
    Build composite key for Seconds General (not a true PK, used for diff matching).

    Uses: date + week + style + color
    """
    date = parse_date(row.get("date", ""))
    week = row.get("week", 0)
    style = str(row.get("style", "")).strip()
    color = str(row.get("color", "")).strip()
    return (date, int(week) if week else 0, style, color)


def extract_dates(rows, date_field):
    """Extract unique normalized dates from a list of row dicts."""
    dates = set()
    for row in rows:
        d = parse_date(row.get(date_field, ""))
        if d:
            dates.add(d)
    return dates


def compute_preview_upsert(excel_rows, db_queryset, key_builder, date_field):
    """
    Compute preview for sheets with natural PKs (UPSERT strategy).

    Compares Excel rows against DB by natural key.
    Classifies each row as: new, modified, or unchanged.

    Returns:
        dict with keys: new_count, modified_count, unchanged_count, total, dates
    """
    db_index = {}
    for obj in db_queryset:
        row_dict = _model_to_dict(obj)
        key = key_builder(row_dict)
        db_index[key] = row_dict

    new_count = 0
    modified_count = 0
    unchanged_count = 0

    for row in excel_rows:
        key = key_builder(row)
        if key not in db_index:
            new_count += 1
        else:
            db_row = db_index[key]
            if _rows_differ(row, db_row):
                modified_count += 1
            else:
                unchanged_count += 1

    dates = extract_dates(excel_rows, date_field)

    return {
        "strategy": "upsert",
        "new": new_count,
        "modified": modified_count,
        "unchanged": unchanged_count,
        "total": len(excel_rows),
        "dates": sorted(dates),
    }


def compute_preview_timewindow(excel_rows, db_queryset, date_field):
    """
    Compute preview for sheets without natural PKs (Time-Window Sync strategy).

    Groups by date and compares row counts. Flags potential data loss.

    Returns:
        dict with keys: total, dates, date_counts (excel vs db), warnings
    """
    excel_dates = extract_dates(excel_rows, date_field)

    # Count existing rows per date in DB
    db_date_counts = {}
    for obj in db_queryset:
        row_dict = {"date_1": getattr(obj, "date_1", None) or getattr(obj, "date", None)}
        d = parse_date(row_dict.get("date_1", ""))
        if d:
            db_date_counts[d] = db_date_counts.get(d, 0) + 1

    # Count Excel rows per date
    excel_date_counts = {}
    for row in excel_rows:
        d = parse_date(row.get(date_field, ""))
        if d:
            excel_date_counts[d] = excel_date_counts.get(d, 0) + 1

    date_comparison = {}
    warnings = []

    for date in sorted(excel_dates):
        excel_count = excel_date_counts.get(date, 0)
        db_count = db_date_counts.get(date, 0)
        date_comparison[date] = {
            "excel": excel_count,
            "db": db_count,
            "diff": excel_count - db_count,
        }

        if db_count > 0 and excel_count < db_count:
            lost = db_count - excel_count
            warnings.append(
                f"Date {date}: Excel has {excel_count} rows but DB has {db_count}. "
                f"{lost} existing records will be replaced."
            )

    # Derive new/modified/unchanged from date comparison
    # For time_window strategy, we can't distinguish new vs modified at the row level
    # So: new = rows where excel > db, modified = rows where db > 0 and excel > 0, unchanged = 0
    new_count = 0
    modified_count = 0
    unchanged_count = 0
    for date, counts in date_comparison.items():
        excel_count = counts['excel']
        db_count = counts['db']
        if db_count == 0:
            new_count += excel_count
        elif excel_count == db_count:
            unchanged_count += excel_count
        else:
            # Some overlap — count the overlap as modified, the rest as new
            modified_count += min(excel_count, db_count)
            if excel_count > db_count:
                new_count += excel_count - db_count

    # Rows with missing/unparseable dates are skipped in the date loop
    # but still counted in total. Attribute them to 'new' to keep math consistent.
    unmatched = len(excel_rows) - (new_count + modified_count + unchanged_count)
    if unmatched > 0:
        new_count += unmatched

    return {
        "strategy": "time_window",
        "new": new_count,
        "modified": modified_count,
        "unchanged": unchanged_count,
        "total": len(excel_rows),
        "dates": sorted(excel_dates),
        "date_counts": date_comparison,
        "warnings": warnings,
    }


def apply_upsert(excel_rows, model_class, key_builder, not_numeric_columns,
                 numeric_columns, defect_fields=None, color_map=None):
    """
    Apply UPSERT for sheets with natural PKs.

    - New records: bulk_create
    - Modified records: bulk_update
    """
    if not excel_rows:
        return

    key_field_names = _get_key_field_names(key_builder)
    db_index = {}
    for obj in model_class.objects.only(*key_field_names).iterator():
        row_dict = _model_to_dict(obj)
        key = key_builder(row_dict)
        db_index[key] = obj

    new_instances = []
    update_instances = []

    # Dedupe incoming Excel rows by natural key (last row wins).
    # This prevents unique-key crashes when the same key appears multiple times
    # in the same uploaded file batch (e.g. duplicate container_number rows).
    deduped_rows_map = {}
    for row in excel_rows:
        deduped_rows_map[key_builder(row)] = row
    deduped_rows = list(deduped_rows_map.values())

    for row in deduped_rows:
        key = key_builder(row)
        if key not in db_index:
            # New record
            instance = _build_instance(model_class, row, numeric_columns,
                                       not_numeric_columns, color_map=color_map)
            new_instances.append(instance)
        else:
            # Existing record — update fields
            instance = db_index[key]
            _update_instance(instance, row, numeric_columns, not_numeric_columns,
                             color_map=color_map)
            update_instances.append(instance)

    if new_instances:
        model_class.objects.bulk_create(new_instances, batch_size=1000)

    if update_instances:
        # Determine update fields (all except id)
        update_fields = [
            f.name for f in model_class._meta.fields
            if f.name != "id" and not f.auto_created
        ]
        model_class.objects.bulk_update(update_instances, update_fields, batch_size=1000)

    if defect_fields:
        _sync_defects(deduped_rows, model_class, defect_fields, color_map=color_map)


def apply_timewindow(excel_rows, model_class, date_field, table_type=None,
                     numeric_columns=None, not_numeric_columns=None,
                     defect_fields=None, color_map=None):
    """
    Apply Time-Window Sync for sheets without natural PKs.

    1. Extract unique dates from Excel
    2. Delete existing records for those dates
    3. Insert all Excel rows for those dates
    """
    if not excel_rows:
        return

    excel_dates = extract_dates(excel_rows, date_field)

    if not excel_dates:
        return

    date_column = "date_1" if hasattr(model_class, "date_1") else "date"
    qs = model_class.objects.all()
    if table_type:
        qs = qs.filter(table_type=table_type)
    existing = qs.only("id", date_column)
    canonical_excel_set = set(excel_dates)
    ids_to_delete = []
    for obj in existing:
        canonical = canonicalize_qc_fa_date(getattr(obj, date_column))
        if canonical in canonical_excel_set:
            ids_to_delete.append(obj.id)
    if ids_to_delete:
        model_class.objects.filter(id__in=ids_to_delete).delete()

    # Insert new records
    instances = []
    for row in excel_rows:
        d = parse_date(row.get(date_field, ""))
        if d in excel_dates:
            instance = _build_instance(model_class, row, numeric_columns,
                                       not_numeric_columns, table_type,
                                       color_map=color_map)
            instances.append(instance)

    if instances:
        model_class.objects.bulk_create(instances, batch_size=1000)

    if defect_fields and table_type:
        stats = _sync_defects_timewindow(excel_rows, model_class, table_type,
                                          defect_fields, excel_dates,
                                          color_map=color_map)
        if stats and stats.get('unmatched_defect_rows', 0) > 0:
            logger.warning(
                "Defect sync for table_type=%s: %d unmatched rows, "
                "created=%d, matched_parents=%d, invalid_date=%d, missing_color=%d",
                table_type,
                stats.get('unmatched_defect_rows', 0),
                stats.get('created_defects', 0),
                stats.get('matched_parents', 0),
                stats.get('invalid_date_rows', 0),
                stats.get('missing_color_rows', 0),
            )
        return stats

    return None


def apply_session(session):
    """
    Apply all sheets from an ExcelSyncSession in a single atomic transaction.

    If any sheet fails, the entire operation is rolled back.

    When preview data was stored in Redis (session._redis_stored is True),
    row data is fetched from Redis before processing. This keeps JSONFields
    small during preview and provides automatic TTL cleanup.
    """
    if session.redis_stored:
        _hydrate_session_from_redis(session)

    all_color_names = set()
    for sheet_rows in [
        session.qc_fa_plant_data,
        session.qc_fa_customer_data,
        session.seconds_a4_data,
    ]:
        all_color_names |= _collect_sheet_colors(sheet_rows)

    color_map = _resolve_colors_batch(all_color_names)

    with transaction.atomic():
        # QC FA Plant (Time-Window)
        apply_timewindow(
            session.qc_fa_plant_data,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=_get_numeric_columns("qc_fa_plant"),
            not_numeric_columns=_get_not_numeric_columns("qc_fa_plant"),
            defect_fields=_get_defect_fields("qc_fa_plant"),
            color_map=color_map,
        )

        # QC FA Customer (Time-Window)
        apply_timewindow(
            session.qc_fa_customer_data,
            QualityQcFa,
            date_field="date_1",
            table_type="QFC",
            numeric_columns=_get_numeric_columns("qc_fa_customer"),
            not_numeric_columns=_get_not_numeric_columns("qc_fa_customer"),
            defect_fields=_get_defect_fields("qc_fa_customer"),
            color_map=color_map,
        )

        # SecondsA4 (UPSERT)
        apply_upsert(
            session.seconds_a4_data,
            SecondsA4,
            key_builder=build_seconds_a4_key,
            not_numeric_columns=_get_not_numeric_columns("seconds_a4"),
            numeric_columns=_get_numeric_columns("seconds_a4"),
            color_map=color_map,
        )

        # Seconds General — use bulk_insert_seconds_general which creates
        # both parent records AND SecondsGeneralDefect records
        seconds_rows = session.seconds_general_data
        if seconds_rows:
            import pandas as pd
            from excel_importer.handler_service import bulk_insert_seconds_general

            sg_dates = extract_dates(seconds_rows, "date")
            if sg_dates:
                SecondsGeneral.objects.filter(date__in=list(sg_dates)).delete()

                df = pd.DataFrame(seconds_rows)
                bulk_insert_seconds_general(
                    df,
                    numeric_columns=_get_numeric_columns("seconds_general"),
                    not_numeric_columns=_get_not_numeric_columns("seconds_general"),
                )

        # Container (UPSERT) — no color FK
        apply_upsert(
            session.container_data,
            Container,
            key_builder=build_container_key,
            not_numeric_columns=_get_not_numeric_columns("container"),
            numeric_columns=_get_numeric_columns("container"),
            defect_fields=_get_defect_fields("container"),
            color_map=color_map,
        )

        session.status = "confirmed"
        session.save()

    if session.redis_stored:
        from excel_importer.preview_cache import delete_preview_data
        delete_preview_data(session.pk)


def create_session_from_dataframes(dataframes):
    """
    Create an ExcelSyncSession from parsed DataFrames.

    Stores raw row data in Redis (with 24h TTL) when available, falling
    back to JSONField storage otherwise. This prevents PostgreSQL bloat
    from large preview payloads and provides automatic cleanup of
    abandoned sessions.

    Args:
        dataframes: dict with keys matching sheet names, values are lists of dicts

    Returns:
        ExcelSyncSession instance with preview computed
    """
    from excel_importer.preview_cache import (
        store_preview_data,
        is_redis_available,
    )

    session = ExcelSyncSession()

    raw_container_rows = dataframes.get("container", [])
    container_rows, container_warnings = _normalize_container_rows(raw_container_rows)

    sheet_data_map = {
        "qc_fa_plant": dataframes.get("qc_fa_plant", []),
        "qc_fa_customer": dataframes.get("qc_fa_customer", []),
        "seconds_a4": dataframes.get("seconds_a4", []),
        "seconds_general": dataframes.get("seconds_general", []),
        "container": container_rows,
    }

    from excel_importer.handler_service import (
        normalize_qc_fa_customer_rows,
        normalize_seconds_general_rows,
    )

    qfc_raw_rows = sheet_data_map.get("qc_fa_customer", [])
    qfc_normalized, qfc_import_warnings = normalize_qc_fa_customer_rows(qfc_raw_rows)
    sheet_data_map["qc_fa_customer"] = qfc_normalized

    sg_raw_rows = sheet_data_map.get("seconds_general", [])
    sg_normalized, sg_import_warnings = normalize_seconds_general_rows(sg_raw_rows)
    sheet_data_map["seconds_general"] = sg_normalized

    from excel_importer.handler_service import (
        bulk_insert as handler_bulk_insert_qcfa,
        bulk_insert_container,
    )
    from quality_data.models import QualityQcFa, Container

    if not excel_rows or not defect_fields:
        return None

    df = pd.DataFrame(excel_rows)

    # Get column lists from sheet_configs
    numeric_cols = _get_numeric_columns_for_model(model_class)
    not_numeric_cols = _get_not_numeric_columns_for_model(model_class)

    # Determine table_type for QualityQcFa.
    # Prefer the caller-supplied value; fall back to DataFrame detection
    # (which only works when the row dicts already carry the column).
    if table_type is None and model_class == QualityQcFa:
        table_types = df['table_type'].unique() if 'table_type' in df.columns else []
        table_type = table_types[0] if len(table_types) == 1 else 'QFA'

    # Call the appropriate handler based on model
    if model_class == QualityQcFa:
        # Use caller-provided defect_fields when available; fall back to the
        # sheet-specific list. This preserves testability and lets callers
        # scope defect processing without pulling in the full sheet list.
        if defect_fields:
            qc_defect_fields = defect_fields
        elif table_type == 'QFC':
            qc_defect_fields = _get_defect_fields('qc_fa_customer')
        else:
            qc_defect_fields = _get_defect_fields('qc_fa_plant')

        # For QC FA time-window: parent records are already created by apply_timewindow.
        # Use defects_only=True to only create InspectionDefect records.
        return handler_bulk_insert_qcfa(
            df,
            numeric_cols,
            not_numeric_cols,
            qc_defect_fields or defect_fields,
            table_type,
            defects_only=True,  # Parents already exist, only create defects
            color_map=color_map,
        )
    elif model_class == Container:
        container_defect_fields = _get_defect_fields('container') or defect_fields
        bulk_insert_container(
            df,
            numeric_cols,
            not_numeric_cols,
            container_defect_fields or defect_fields
        )
    return None


def _get_numeric_columns_for_model(model_class):
    """Get numeric columns for a specific model class."""
    from excel_importer.sheet_configs import (
        QC_FA_PLANT_NUMERIC_COLUMNS,
        CONTAINER_NUMERIC_COLUMNS,
    )
    
    if model_class == QualityQcFa:
        return QC_FA_PLANT_NUMERIC_COLUMNS
    elif model_class == Container:
        return CONTAINER_NUMERIC_COLUMNS
    return []


def _get_not_numeric_columns_for_model(model_class):
    """Get non-numeric columns for a specific model class."""
    from excel_importer.sheet_configs import (
        QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
        CONTAINER_NOT_NUMERIC_COLUMNS,
    )
    
    if model_class == QualityQcFa:
        return QC_FA_PLANT_NOT_NUMERIC_COLUMNS
    elif model_class == Container:
        return CONTAINER_NOT_NUMERIC_COLUMNS
    return []


def _normalize_container_rows(rows):
    """Normalize container date values and emit warnings for invalid input."""
    normalized_rows = []
    warnings = []

    for row in rows:
        normalized_row = dict(row)
        raw_date = normalized_row.get("date")
        normalized_date = normalize_container_date(raw_date)

        if normalized_date is not None:
            normalized_row["date"] = normalized_date.isoformat()
        else:
            normalized_row["date"] = None
            raw_text = str(raw_date).strip() if raw_date is not None else ""
            if raw_text:
                container_number = normalized_row.get("container_number", "unknown")
                warnings.append(
                    f"Container {container_number}: invalid date '{raw_text}' stored as NULL."
                )

        normalized_rows.append(normalized_row)

    return normalized_rows, warnings
