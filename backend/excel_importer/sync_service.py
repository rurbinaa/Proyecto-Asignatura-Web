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
    InspectionDefect,
    ContainerInspectionDefect,
    Color,
    DefectType,
    ContainerDefectType,
    ExcelSyncSession,
)
from excel_importer.date_utils import parse_date


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
                 numeric_columns, defect_fields=None):
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
                                       not_numeric_columns)
            new_instances.append(instance)
        else:
            # Existing record — update fields
            instance = db_index[key]
            _update_instance(instance, row, numeric_columns, not_numeric_columns)
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
        _sync_defects(deduped_rows, model_class, defect_fields)


def apply_timewindow(excel_rows, model_class, date_field, table_type=None,
                     numeric_columns=None, not_numeric_columns=None,
                     defect_fields=None):
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
                                       not_numeric_columns, table_type)
            instances.append(instance)

    if instances:
        model_class.objects.bulk_create(instances, batch_size=1000)

    # Handle defects if applicable
    if defect_fields and table_type:
        _sync_defects_timewindow(excel_rows, model_class, table_type,
                                  defect_fields, excel_dates)


def apply_session(session):
    """
    Apply all sheets from an ExcelSyncSession in a single atomic transaction.

    If any sheet fails, the entire operation is rolled back.
    """
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
        )

        # SecondsA4 (UPSERT)
        apply_upsert(
            session.seconds_a4_data,
            SecondsA4,
            key_builder=build_seconds_a4_key,
            not_numeric_columns=_get_not_numeric_columns("seconds_a4"),
            numeric_columns=_get_numeric_columns("seconds_a4"),
        )

        # Seconds General (Time-Window)
        apply_timewindow(
            session.seconds_general_data,
            SecondsGeneral,
            date_field="date",
            numeric_columns=_get_numeric_columns("seconds_general"),
            not_numeric_columns=_get_not_numeric_columns("seconds_general"),
        )

        # Container (UPSERT)
        apply_upsert(
            session.container_data,
            Container,
            key_builder=build_container_key,
            not_numeric_columns=_get_not_numeric_columns("container"),
            numeric_columns=_get_numeric_columns("container"),
            defect_fields=_get_defect_fields("container"),
        )

        session.status = "confirmed"
        session.save()


# ─────────────────────────────────────────────────────────
# Session Management
# ─────────────────────────────────────────────────────────

def create_session_from_dataframes(dataframes):
    """
    Create an ExcelSyncSession from parsed DataFrames.

    Args:
        dataframes: dict with keys matching sheet names, values are lists of dicts

    Returns:
        ExcelSyncSession instance with preview computed
    """
    session = ExcelSyncSession()

    # Store parsed data
    session.qc_fa_plant_data = dataframes.get("qc_fa_plant", [])
    session.qc_fa_customer_data = dataframes.get("qc_fa_customer", [])
    session.seconds_a4_data = dataframes.get("seconds_a4", [])
    session.seconds_general_data = dataframes.get("seconds_general", [])
    session.container_data = dataframes.get("container", [])

    # Compute previews
    session.qc_fa_plant_preview = compute_preview_timewindow(
        session.qc_fa_plant_data,
        QualityQcFa.objects.filter(table_type="QFA"),
        date_field="date_1",
    )

    session.qc_fa_customer_preview = compute_preview_timewindow(
        session.qc_fa_customer_data,
        QualityQcFa.objects.filter(table_type="QFC"),
        date_field="date_1",
    )

    session.seconds_a4_preview = compute_preview_upsert(
        session.seconds_a4_data,
        SecondsA4.objects.all(),
        key_builder=build_seconds_a4_key,
        date_field="date",
    )

    session.seconds_general_preview = compute_preview_timewindow(
        session.seconds_general_data,
        SecondsGeneral.objects.all(),
        date_field="date",
    )

    session.container_preview = compute_preview_upsert(
        session.container_data,
        Container.objects.all(),
        key_builder=build_container_key,
        date_field="date",
    )

    # Collect all warnings
    all_warnings = []
    for preview_field in ["qc_fa_plant_preview", "qc_fa_customer_preview",
                          "seconds_general_preview"]:
        preview = getattr(session, preview_field)
        all_warnings.extend(preview.get("warnings", []))
    session.warnings = all_warnings

    session.save()
    return session


def reject_session(session):
    """Reject a pending session — just mark it as rejected."""
    session.status = "rejected"
    session.save()


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
                    table_type=None):
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
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})
        data["color"] = color_obj

    return model_class(**data)


def _update_instance(instance, row, numeric_columns, not_numeric_columns):
    """Update an existing model instance with row data."""
    fk_fields = {"color"}  # Fields that are FK and need special handling

    for field in (numeric_columns or []):
        if field in row:
            setattr(instance, field, row[field])
    for field in (not_numeric_columns or []):
        if field in row and field not in fk_fields:
            setattr(instance, field, row[field])

    # Handle FK fields
    if hasattr(instance, "color") and "color" in row:
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})
        instance.color = color_obj


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


def _sync_defects(excel_rows, model_class, defect_fields):
    """
    Sync defect through-table records for QC FA or Container.
    
    Delegates to handler_service for defect creation logic.
    """
    if not excel_rows or not defect_fields:
        return
    
    _sync_defects_via_handler(excel_rows, model_class, defect_fields)


def _sync_defects_timewindow(excel_rows, model_class, table_type,
                              defect_fields, excel_dates):
    """
    Sync defects for time-window strategy (already deleted, just create).
    
    Delegates to handler_service for defect creation logic.
    """
    if not excel_rows or not defect_fields:
        return
    
    # For time-window, the parent records were already deleted (CASCADE deletes defects)
    # So we just need to create new defect records for the new parent records
    _sync_defects_via_handler(excel_rows, model_class, defect_fields)


def _sync_defects_via_handler(excel_rows, model_class, defect_fields):
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
            defects_only=True  # Parents already exist, only create defects
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
        QC_FA_CUSTOMER_NUMERIC_COLUMNS,
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
        QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
        CONTAINER_NOT_NUMERIC_COLUMNS,
    )
    
    if model_class == QualityQcFa:
        return QC_FA_PLANT_NOT_NUMERIC_COLUMNS
    elif model_class == Container:
        return CONTAINER_NOT_NUMERIC_COLUMNS
    return []
