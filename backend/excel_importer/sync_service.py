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
from excel_importer.date_utils import normalize_container_date, parse_date


# ─────────────────────────────────────────────────────────
# Color Resolution (batched — avoids N+1 get_or_create per row)
# ─────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────
# Natural Key Builders
# ─────────────────────────────────────────────────────────

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

    Uses: date_1 + po + style + color
    """
    date = parse_date(row.get("date_1", ""))
    po = row.get("po", 0)
    style = str(row.get("style", "")).strip()
    color = str(row.get("color", "")).strip().lower().replace(" ", "_")
    return (date, int(po) if po else 0, style, color)


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


# ─────────────────────────────────────────────────────────
# Extract Unique Dates from DataFrame rows
# ─────────────────────────────────────────────────────────

def extract_dates(rows, date_field):
    """Extract unique normalized dates from a list of row dicts."""
    dates = set()
    for row in rows:
        d = parse_date(row.get(date_field, ""))
        if d:
            dates.add(d)
    return dates


# ─────────────────────────────────────────────────────────
# Preview Computation
# ─────────────────────────────────────────────────────────

def compute_preview_upsert(excel_rows, db_queryset, key_builder, date_field):
    """
    Compute preview for sheets with natural PKs (UPSERT strategy).

    Compares Excel rows against DB by natural key.
    Classifies each row as: new, modified, or unchanged.

    Returns:
        dict with keys: new_count, modified_count, unchanged_count, total, dates
    """
    # Build DB index by natural key
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
            # Check if any field differs
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

    # Build comparison and warnings
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


# ─────────────────────────────────────────────────────────
# Apply Logic
# ─────────────────────────────────────────────────────────

def apply_upsert(excel_rows, model_class, key_builder, not_numeric_columns,
                 numeric_columns, defect_fields=None, color_map=None):
    """
    Apply UPSERT for sheets with natural PKs.

    - New records: bulk_create
    - Modified records: bulk_update
    """
    if not excel_rows:
        return

    # Build DB index - use .iterator() to stream objects without loading all into memory
    # Only() defers loading non-essential fields
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

    # Handle defects if applicable
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

    # Delete existing records for these dates
    date_column = "date_1" if hasattr(model_class, "date_1") else "date"
    delete_filter = {f"{date_column}__in": list(excel_dates)}
    if table_type:
        delete_filter["table_type"] = table_type

    model_class.objects.filter(**delete_filter).delete()

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

    # Handle defects if applicable
    if defect_fields and table_type:
        _sync_defects_timewindow(excel_rows, model_class, table_type,
                                  defect_fields, excel_dates,
                                  color_map=color_map)


def apply_session(session):
    """
    Apply all sheets from an ExcelSyncSession in a single atomic transaction.

    If any sheet fails, the entire operation is rolled back.

    When preview data was stored in Redis (session._redis_stored is True),
    row data is fetched from Redis before processing. This keeps JSONFields
    small during preview and provides automatic TTL cleanup.
    """
    # ── Fetch data from Redis if it was stored there during preview ──
    if session.redis_stored:
        _hydrate_session_from_redis(session)

    # ── Batch-resolve ALL colors upfront (1-2 queries instead of N× get_or_create) ──
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
                # Delete existing records for these dates (CASCADE deletes their defects)
                SecondsGeneral.objects.filter(date__in=list(sg_dates)).delete()

                # Convert to DataFrame and call bulk_insert which creates parents + defects
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

    # ── Clean up Redis after successful application ──
    if session.redis_stored:
        from excel_importer.preview_cache import delete_preview_data
        delete_preview_data(session.pk)


# ─────────────────────────────────────────────────────────
# Session Management
# ─────────────────────────────────────────────────────────

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

    # Prepare parsed data
    raw_container_rows = dataframes.get("container", [])
    container_rows, container_warnings = _normalize_container_rows(raw_container_rows)

    sheet_data_map = {
        "qc_fa_plant": dataframes.get("qc_fa_plant", []),
        "qc_fa_customer": dataframes.get("qc_fa_customer", []),
        "seconds_a4": dataframes.get("seconds_a4", []),
        "seconds_general": dataframes.get("seconds_general", []),
        "container": container_rows,
    }

    # Store parsed data — prefer Redis for auto-TTL cleanup, fall back to JSONField
    session.redis_stored = False
    if is_redis_available():
        session.save()  # Need PK for Redis key
        if store_preview_data(session.pk, sheet_data_map):
            # Data is in Redis — clear JSONFields to avoid duplicate storage
            session.redis_stored = True

    # Assign data to session fields (either full data or empty lists if in Redis)
    session.qc_fa_plant_data = sheet_data_map["qc_fa_plant"] if not session.redis_stored else []
    session.qc_fa_customer_data = sheet_data_map["qc_fa_customer"] if not session.redis_stored else []
    session.seconds_a4_data = sheet_data_map["seconds_a4"] if not session.redis_stored else []
    session.seconds_general_data = sheet_data_map["seconds_general"] if not session.redis_stored else []
    session.container_data = sheet_data_map["container"] if not session.redis_stored else []

    # For preview computation, always use the in-memory data (before it's cleared)
    qc_fa_plant_rows = sheet_data_map["qc_fa_plant"]
    qc_fa_customer_rows = sheet_data_map["qc_fa_customer"]
    seconds_a4_rows = sheet_data_map["seconds_a4"]
    seconds_general_rows = sheet_data_map["seconds_general"]
    container_rows = sheet_data_map["container"]

    # Compute previews — filter DB queries by Excel dates to avoid loading
    # the entire table into memory. For large tables (100k+ rows), this is
    # a critical optimization that reduces query time from seconds to milliseconds.

    # QC FA Plant (time_window)
    qfa_plant_dates = extract_dates(qc_fa_plant_rows, "date_1")
    session.qc_fa_plant_preview = compute_preview_timewindow(
        qc_fa_plant_rows,
        QualityQcFa.objects.filter(table_type="QFA", date_1__in=qfa_plant_dates).select_related('color')
        if qfa_plant_dates else QualityQcFa.objects.none(),
        date_field="date_1",
    )

    # QC FA Customer (time_window)
    qfa_customer_dates = extract_dates(qc_fa_customer_rows, "date_1")
    session.qc_fa_customer_preview = compute_preview_timewindow(
        qc_fa_customer_rows,
        QualityQcFa.objects.filter(table_type="QFC", date_1__in=qfa_customer_dates).select_related('color')
        if qfa_customer_dates else QualityQcFa.objects.none(),
        date_field="date_1",
    )

    # SecondsA4 (upsert)
    seconds_a4_dates = extract_dates(seconds_a4_rows, "date")
    session.seconds_a4_preview = compute_preview_upsert(
        seconds_a4_rows,
        SecondsA4.objects.filter(date__in=seconds_a4_dates).select_related('color')
        if seconds_a4_dates else SecondsA4.objects.none(),
        key_builder=build_seconds_a4_key,
        date_field="date",
    )

    # Seconds General (time_window)
    seconds_general_dates = extract_dates(seconds_general_rows, "date")
    session.seconds_general_preview = compute_preview_timewindow(
        seconds_general_rows,
        SecondsGeneral.objects.filter(date__in=seconds_general_dates)
        if seconds_general_dates else SecondsGeneral.objects.none(),
        date_field="date",
    )

    # Container (upsert) — use date filtering too
    container_dates = extract_dates(container_rows, "date")
    session.container_preview = compute_preview_upsert(
        container_rows,
        Container.objects.filter(date__in=container_dates)
        if container_dates else Container.objects.none(),
        key_builder=build_container_key,
        date_field="date",
    )

    # Collect all warnings
    all_warnings = []
    for preview_field in ["qc_fa_plant_preview", "qc_fa_customer_preview",
                          "seconds_general_preview"]:
        preview = getattr(session, preview_field)
        all_warnings.extend(preview.get("warnings", []))
    all_warnings.extend(container_warnings)
    session.warnings = all_warnings

    session.save()
    return session


def reject_session(session):
    """Reject a pending session — mark it as rejected and clean up Redis."""
    if session.redis_stored:
        from excel_importer.preview_cache import delete_preview_data
        delete_preview_data(session.pk)

    session.status = "rejected"
    session.save()


def _hydrate_session_from_redis(session):
    """
    Fetch row data from Redis and populate session.*_data fields.

    Called at the start of apply_session() when data was stored in Redis
    during preview (session._redis_stored is True).
    """
    from excel_importer.preview_cache import fetch_preview_data

    sheet_names = [
        "qc_fa_plant", "qc_fa_customer", "seconds_a4",
        "seconds_general", "container",
    ]
    session_fields = [
        "qc_fa_plant_data", "qc_fa_customer_data", "seconds_a4_data",
        "seconds_general_data", "container_data",
    ]

    for sheet_name, field_name in zip(sheet_names, session_fields):
        rows = fetch_preview_data(session.pk, sheet_name)
        if rows is None:
            raise RuntimeError(
                f"Preview data for session {session.pk}, sheet '{sheet_name}' "
                f"has expired or is unavailable. Please re-upload the file."
            )
        setattr(session, field_name, rows)


# ─────────────────────────────────────────────────────────
# Private Helpers
# ─────────────────────────────────────────────────────────

def _get_key_field_names(key_builder):
    """
    Extract field names used by a key builder function.

    Different key builders use different fields:
    - build_seconds_a4_key: date, cut_num, color
    - build_container_key: container_number
    - build_qc_fa_plant_key: date_1, po, style, team, color
    - build_qc_fa_customer_key: date_1, po, style, color
    - build_seconds_general_key: date, week, style, color

    Returns field names as a list.
    """
    import inspect
    sig = inspect.signature(key_builder)
    # First parameter is 'row' (the dict)
    param_names = list(sig.parameters.keys())
    if param_names and param_names[0] == 'row':
        param_names = param_names[1:]
    return param_names if param_names else ['id']

def _get_numeric_columns(sheet_key):
    """Get numeric column names for a sheet."""
    from excel_importer.sheet_configs import (
        QC_FA_PLANT_NUMERIC_COLUMNS,
        QC_FA_CUSTOMER_NUMERIC_COLUMNS,
        SECONDS_A4_NUMERIC_COLUMNS,
        SECONDS_GENERAL_NUMERIC_COLUMNS,
        CONTAINER_NUMERIC_COLUMNS,
    )
    mapping = {
        "qc_fa_plant": QC_FA_PLANT_NUMERIC_COLUMNS,
        "qc_fa_customer": QC_FA_CUSTOMER_NUMERIC_COLUMNS,
        "seconds_a4": SECONDS_A4_NUMERIC_COLUMNS,
        "seconds_general": SECONDS_GENERAL_NUMERIC_COLUMNS,
        "container": CONTAINER_NUMERIC_COLUMNS,
    }
    return mapping.get(sheet_key, [])


def _get_not_numeric_columns(sheet_key):
    """Get non-numeric column names for a sheet."""
    from excel_importer.sheet_configs import (
        QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
        QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
        SECONDS_A4_NOT_NUMERIC_COLUMNS,
        SECONDS_GENERAL_NOT_NUMERIC_COLUMNS,
        CONTAINER_NOT_NUMERIC_COLUMNS,
    )
    mapping = {
        "qc_fa_plant": QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
        "qc_fa_customer": QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
        "seconds_a4": SECONDS_A4_NOT_NUMERIC_COLUMNS,
        "seconds_general": SECONDS_GENERAL_NOT_NUMERIC_COLUMNS,
        "container": CONTAINER_NOT_NUMERIC_COLUMNS,
    }
    return mapping.get(sheet_key, [])


def _get_defect_fields(sheet_key):
    """Get defect field names for a sheet."""
    from excel_importer.sheet_configs import (
        QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
        QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
        CONTAINER_AMOUNT_DEFEACTS_FIELDS,
    )
    mapping = {
        "qc_fa_plant": QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
        "qc_fa_customer": QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
        "container": CONTAINER_AMOUNT_DEFEACTS_FIELDS,
    }
    return mapping.get(sheet_key)


def _build_instance(model_class, row, numeric_columns, not_numeric_columns,
                    table_type=None, color_map=None):
    """Build a model instance from a row dict."""
    fk_fields = {"color"}  # Fields that are FK and need special handling

    data = {}
    for field in (numeric_columns or []):
        data[field] = row.get(field, 0)
    for field in (not_numeric_columns or []):
        if field not in fk_fields:
            data[field] = row.get(field, "UNKNOWN")
    if table_type:
        data["table_type"] = table_type

    # Handle FK fields
    if "color" in [f.name for f in model_class._meta.fields]:
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        if color_map is not None:
            color_obj = color_map.get(color_name)
            if color_obj is None:
                # Fallback: color not in batch map (shouldn't happen if _collect_sheet_colors
                # caught all unique colors). Create it individually as a safety net.
                color_obj, _ = Color.objects.get_or_create(
                    name=color_name, defaults={"is_active": True}
                )
        else:
            color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})
        data["color"] = color_obj

    if model_class == Container:
        data["date"] = normalize_container_date(row.get("date"))

    return model_class(**data)


def _update_instance(instance, row, numeric_columns, not_numeric_columns, color_map=None):
    """Update an existing model instance with row data."""
    fk_fields = {"color"}  # Fields that are FK and need special handling

    for field in (numeric_columns or []):
        if field in row:
            setattr(instance, field, row[field])
    for field in (not_numeric_columns or []):
        if field in row and field not in fk_fields:
            if isinstance(instance, Container) and field == "date":
                continue
            setattr(instance, field, row[field])

    # Handle FK fields
    if hasattr(instance, "color") and "color" in row:
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        if color_map is not None:
            color_obj = color_map.get(color_name)
            if color_obj is None:
                color_obj, _ = Color.objects.get_or_create(
                    name=color_name, defaults={"is_active": True}
                )
        else:
            color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})
        instance.color = color_obj

    if isinstance(instance, Container) and "date" in row:
        normalized = normalize_container_date(row.get("date"))
        if normalized is not None:
            instance.date = normalized


def _model_to_dict(obj):
    """Convert a model instance to a dict for comparison with Excel rows."""
    result = {}
    for field in obj._meta.fields:
        value = getattr(obj, field.name)
        if hasattr(value, "pk"):
            result[field.name] = value.pk if field.name != "color" else str(value)
        else:
            result[field.name] = value
    return result


def _rows_differ(row_a, row_b):
    """Compare two row dicts, ignoring None values."""
    all_keys = set(row_a.keys()) | set(row_b.keys())
    for key in all_keys:
        if key in ("id", "color"):
            continue
        val_a = row_a.get(key)
        val_b = row_b.get(key)
        if val_a is None or val_b is None:
            continue
        # Normalize for comparison
        if str(val_a).strip() != str(val_b).strip():
            return True
    return False


def _sync_defects(excel_rows, model_class, defect_fields, color_map=None):
    """
    Sync defect through-table records for QC FA or Container.
    
    Delegates to handler_service for defect creation logic.
    """
    if not excel_rows or not defect_fields:
        return
    
    _sync_defects_via_handler(excel_rows, model_class, defect_fields, color_map=color_map)


def _sync_defects_timewindow(excel_rows, model_class, table_type,
                              defect_fields, excel_dates, color_map=None):
    """
    Sync defects for time-window strategy (already deleted, just create).
    
    Delegates to handler_service for defect creation logic.
    """
    if not excel_rows or not defect_fields:
        return
    
    # For time-window, the parent records were already deleted (CASCADE deletes defects)
    # So we just need to create new defect records for the new parent records
    _sync_defects_via_handler(excel_rows, model_class, defect_fields, color_map=color_map)


def _sync_defects_via_handler(excel_rows, model_class, defect_fields, color_map=None):
    """
    Helper that delegates defect creation to handler_service.
    
    The handler_service.bulk_insert functions already handle creating
    InspectionDefect/ContainerInspectionDefect records. We reuse that logic
    by passing the Excel rows through it.

    For QualityQcFa (time-window strategy): parent records are ALREADY created
    by apply_timewindow, so we use defects_only=True to only create defects.
    """
    import pandas as pd
    from excel_importer.handler_service import (
        bulk_insert as handler_bulk_insert_qcfa,
        bulk_insert_container,
    )
    from quality_data.models import QualityQcFa, Container
    
    if not excel_rows or not defect_fields:
        return
    
    # Convert list of dicts to DataFrame (handler_service expects DataFrame)
    df = pd.DataFrame(excel_rows)
    
    # Get column lists from sheet_configs
    numeric_cols = _get_numeric_columns_for_model(model_class)
    not_numeric_cols = _get_not_numeric_columns_for_model(model_class)
    
    # Determine table_type for QualityQcFa
    table_type = None
    if model_class == QualityQcFa:
        # Check if this is QFA or QFC based on data
        table_types = df['table_type'].unique() if 'table_type' in df.columns else []
        table_type = table_types[0] if len(table_types) == 1 else 'QFA'
    
    # Call the appropriate handler based on model
    if model_class == QualityQcFa:
        # Get QC defect field names
        qc_defect_fields = _get_defect_fields('qc_fa_plant') or defect_fields
        
        # For QC FA time-window: parent records are already created by apply_timewindow.
        # Use defects_only=True to only create InspectionDefect records.
        handler_bulk_insert_qcfa(
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
