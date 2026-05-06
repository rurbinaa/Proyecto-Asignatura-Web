import pandas as pd
from quality_data.models import (
    Color,
    Container,
    ContainerDefectType,
    ContainerInspectionDefect,
    DefectType,
    InspectionDefect,
    QualityQcFa,
    SecondsA4,
    SecondsGeneral,
    SecondsGeneralDefectType,
    SecondsGeneralDefect,
)
from excel_importer.date_utils import (
    normalize_container_date,
    parse_date,
    canonicalize_qc_fa_date,
    build_qc_fa_key,
)


def _normalize_defects_fields(defeacts_fields):
    if defeacts_fields in (None, 0):
        return []
    return list(defeacts_fields)


def _truncate_charfields(model_class, data):
    field_lengths = {
        field.name: field.max_length
        for field in model_class._meta.fields
        if hasattr(field, "max_length") and field.max_length is not None
    }

    for field_name, max_length in field_lengths.items():
        value = data.get(field_name)
        if isinstance(value, str):
            data[field_name] = value[:max_length]

    return data


def load_pivot_range(file_obj, sheet, header_row, usecols, nrows=None):
    """
    Lee un rango específico de un sheet del Excel.

    Args:
        file_obj: File object (seekable)
        sheet: Sheet name
        header_row: 1-indexed row number containing headers
        usecols: Column range string like "X:Z" or "AE:AF"
        nrows: Number of rows of data to read (optional)

    Returns:
        DataFrame with the specified range, empty rows/columns removed.
    """
    file_obj.seek(0)
    df = pd.read_excel(
        file_obj, engine='openpyxl', sheet_name=sheet,
        header=header_row - 1,  # Convert 1-indexed to 0-indexed
        usecols=usecols,
        nrows=nrows
    )
    df = df.dropna(how='all').dropna(axis=1, how='all')
    return df


def load_and_clean(file_obj, remap_columns, numeric_columns, defeacts_fields, sheet, header, cols,
                   excel_file=None):
    """
    Load and clean a single sheet from an Excel file.

    Args:
        file_obj: seekable file-like object (used as fallback if excel_file is None).
        excel_file: Optional pd.ExcelFile instance. When provided, reads the sheet
            directly from the already-opened ExcelFile, avoiding repeated file I/O
            when processing multiple sheets.
    """
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    if excel_file is not None:
        # Try with usecols first (fast path). If the sheet has fewer columns
        # than expected, pandas raises ValueError. Fall back to reading all
        # columns and slicing.
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet, header=header, usecols=range(cols))
        except ValueError:
            df = pd.read_excel(excel_file, sheet_name=sheet, header=header)
            if df.shape[1] > cols:
                df = df.iloc[:, :cols]
    else:
        file_obj.seek(0)
        try:
            df = pd.read_excel(file_obj, engine='openpyxl', sheet_name=sheet, header=header, usecols=range(cols))
        except ValueError:
            file_obj.seek(0)
            df = pd.read_excel(file_obj, engine='openpyxl', sheet_name=sheet, header=header)
            if df.shape[1] > cols:
                df = df.iloc[:, :cols]

    df = df.dropna(how='all').dropna(axis=1, how='all')
    df = df.rename(columns=remap_columns)
    
 

    numeric_and_defects_cols = list(set(numeric_columns + defeacts_fields))

    for col in numeric_and_defects_cols:
        if col not in df.columns:
            df[col] = 0

    for col in numeric_and_defects_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if "po" in df.columns:
        df = df[df["po"] != 0].copy()

    if "pass_or_fail" in df.columns:
        normalized_pass_or_fail = df["pass_or_fail"].astype(str).str.strip().str.upper()
        df["pass_or_fail"] = "PASS"
        df.loc[normalized_pass_or_fail == "FAIL", "pass_or_fail"] = "REJECT"

    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].fillna("")
    
    return df

QC_FA_CUSTOMER_VALID_TEAM_RANGE = range(1, 37)


def parse_qfc_line(raw_value):
    """
    Parse a QFC Line value into a ``(team, line_code)`` tuple.

    Business rules (mandatory by design):
    - Simple numeric-only line (for example ``"35"``) → ``(35, None)``
    - Valid dual label (for example ``"35-36"``) → ``(35, "35-36")``
    - **Unspported composite**: any value that is not a simple line or
      a well-formed dual label → ``(None, None)``

    Composite requirements for dual labels:
    - Exactly two segments separated by a single dash
    - Both segments must be integers in 1..36
    - Segments MUST be different

    Edge cases handled:
    - Integer input → treated as simple line
    - Leading/trailing whitespace → stripped
    - Trailing dash (``"35-"``) → invalid
    - More than one dash (``"1-2-3"``) → invalid
    - Non-numeric segments (``"X-36"``) → invalid
    - Zero (``"0"``) → invalid
    - 60 is valid as a simple line; downstream 60→6 sanitization
      runs separately after this parser

    Returns:
        tuple: ``(team_int, line_code_str_or_None)``.
        Returns ``(None, None)`` when the value cannot be parsed as a
        valid line identity.
    """
    # ── Handle integer (or float-as-int) input directly ──
    if isinstance(raw_value, (int, float)):
        try:
            team_val = int(raw_value)
        except (ValueError, TypeError):
            return None, None
        if team_val in QC_FA_CUSTOMER_VALID_TEAM_RANGE or team_val == 60:
            return team_val, None
        return None, None

    # ── Handle string input ──
    if not isinstance(raw_value, str):
        return None, None

    stripped = raw_value.strip()

    # Empty string → invalid
    if not stripped:
        return None, None

    # Count dashes to detect composite
    dash_count = stripped.count("-")

    if dash_count == 0:
        # Simple numeric line
        try:
            team_val = int(stripped)
        except ValueError:
            return None, None
        if team_val in QC_FA_CUSTOMER_VALID_TEAM_RANGE or team_val == 60:
            return team_val, None
        return None, None

    if dash_count == 1:
        # Dual-label candidate
        parts = stripped.split("-", 1)

        # Reject trailing/leading dash: empty segment
        left = parts[0].strip()
        right = parts[1].strip()
        if not left or not right:
            return None, None

        try:
            left_val = int(left)
            right_val = int(right)
        except ValueError:
            return None, None

        # Both segments must be in valid range (1..36) — NOT 60
        if left_val not in QC_FA_CUSTOMER_VALID_TEAM_RANGE:
            return None, None
        if right_val not in QC_FA_CUSTOMER_VALID_TEAM_RANGE:
            return None, None

        # Segments must differ (reject "35-35")
        if left_val == right_val:
            return None, None

        # ✅ Valid dual label — normalize to canonical form (no extra spaces)
        canonical_label = f"{left_val}-{right_val}"
        return left_val, canonical_label

    # More than one dash → invalid
    return None, None


def normalize_qc_fa_customer_rows(rows):
    """
    Normalize QC FA Customer ``Line → team + line_code`` at the import boundary.

    Uses :func:`parse_qfc_line` to split the raw ``Line`` value into
    ``(team, line_code)``. After parsing, the classic 60→6 sanitization
    is applied to the ``team`` portion.

    Business rules:
    - Simple numeric line (``"35"``) → ``team=35, line_code=None``
    - Dual label (``"35-36"``) → ``team=35, line_code="35-36"``
    - Valid ranges: ``1..36`` (and ``60`` which gets corrected to ``6``)
    - Invalid (non-numeric, 0, composite with non-numeric segment, etc.) → rejected

    The function does NOT mutate the input rows — it creates copies.

    Returns:
        tuple: (normalized_rows, warnings_dict)
            warnings_dict has keys:
                corrected (int): number of rows with 60→6 fix
                rejected (int): number of rows removed as invalid
                message (str): human-readable summary (empty if no events)
    """
    if not rows:
        return [], {"corrected": 0, "rejected": 0, "message": ""}

    normalized_rows = []
    corrected_count = 0
    rejected_count = 0

    for row in rows:
        normalized_row = dict(row)
        raw_team = normalized_row.get("team", None)

        # Parse the raw line value using the new dual-line-aware parser
        parsed_team, parsed_line_code = parse_qfc_line(raw_team)

        # Reject rows where parsing failed
        if parsed_team is None:
            rejected_count += 1
            continue

        # Classic 60→6 sanitization (applied AFTER parsing)
        if parsed_team == 60:
            normalized_row["team"] = 6
            corrected_count += 1
        elif parsed_team in QC_FA_CUSTOMER_VALID_TEAM_RANGE:
            normalized_row["team"] = parsed_team
        else:
            # Out of range after parsing (shouldn't happen with the parser validations)
            rejected_count += 1
            continue

        # Set line_code from parsed value (None for simple lines, label for dual)
        normalized_row["line_code"] = parsed_line_code

        normalized_rows.append(normalized_row)

    # Build human-readable message
    parts = []
    if corrected_count:
        s = "s" if corrected_count != 1 else ""
        parts.append(f"corrected {corrected_count} line value{s} (60→6)")
    if rejected_count:
        s = "s" if rejected_count != 1 else ""
        parts.append(f"rejected {rejected_count} invalid row{s} (0/out of range/invalid composite)")

    message = ""
    if parts:
        message = f"QC FA Customer: {' and '.join(parts)}."

    warnings = {
        "corrected": corrected_count,
        "rejected": rejected_count,
        "message": message,
    }

    return normalized_rows, warnings


def normalize_seconds_general_rows(rows):
    """
    Normalize Seconds General raw rows, parsing ``team`` and ``line_code``
    at the import boundary.

    Uses :func:`parse_qfc_line` to split the raw team value into
    ``(team, line_code)``. After parsing, the classic 60→6 sanitization
    is applied to the ``team`` portion.

    Business rules:
    - Simple numeric line (``"35"``) → ``team=35, line_code=None``
    - Dual label (``"35-36"``) → ``team=35, line_code="35-36"``
    - Valid ranges: ``1..36`` (and ``60`` which gets corrected to ``6``)
    - Invalid (non-numeric, 0, composite with non-numeric segment, etc.) → rejected

    The function does NOT mutate the input rows — it creates copies.

    Returns:
        tuple: (normalized_rows, warnings_dict)
            warnings_dict has keys:
                corrected (int): number of rows with 60→6 fix
                rejected (int): number of rows removed as invalid
                message (str): human-readable summary (empty if no events)
    """
    if not rows:
        return [], {"corrected": 0, "rejected": 0, "message": ""}

    normalized_rows = []
    corrected_count = 0
    rejected_count = 0

    for row in rows:
        normalized_row = dict(row)
        raw_team = normalized_row.get("team", None)

        # Parse the raw line value using the existing dual-line-aware parser
        parsed_team, parsed_line_code = parse_qfc_line(raw_team)

        # Reject rows where parsing failed
        if parsed_team is None:
            rejected_count += 1
            continue

        # Classic 60→6 sanitization (applied AFTER parsing)
        if parsed_team == 60:
            normalized_row["team"] = 6
            corrected_count += 1
        elif parsed_team in QC_FA_CUSTOMER_VALID_TEAM_RANGE:
            normalized_row["team"] = parsed_team
        else:
            # Out of range after parsing (shouldn't happen with the parser validations)
            rejected_count += 1
            continue

        # Set line_code from parsed value (None for simple lines, label for dual)
        normalized_row["line_code"] = parsed_line_code

        normalized_rows.append(normalized_row)

    # Build human-readable message
    parts = []
    if corrected_count:
        s = "s" if corrected_count != 1 else ""
        parts.append(f"corrected {corrected_count} line value{s} (60→6)")
    if rejected_count:
        s = "s" if rejected_count != 1 else ""
        parts.append(f"rejected {rejected_count} invalid row{s} (0/out of range/invalid composite)")

    message = ""
    if parts:
        message = f"Seconds General: {' and '.join(parts)}."

    warnings = {
        "corrected": corrected_count,
        "rejected": rejected_count,
        "message": message,
    }

    return normalized_rows, warnings


def bulk_insert(df, numeric_columns, not_numeric_columns, defeacts_fields, table_type,
                defects_only=False, color_map=None):
    """
    Bulk insert QualityQcFa records and/or InspectionDefect records.

    Args:
        defects_only: If True, skip creating QualityQcFa parents and only create
            InspectionDefect records by querying existing parents. Use this when
            parent records were already created by apply_timewindow.
        color_map: Optional dict mapping color name → Color instance. When provided,
            avoids N+1 get_or_create queries per row.
    """
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    if df.empty:
        return

    # For defects_only mode, query existing parents instead of creating new ones
    if defects_only:
        return _bulk_insert_defects_only(df, defeacts_fields, table_type, color_map=color_map)

    quality_instances = []

    for _, row in df.iterrows():

        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        if color_map is not None:
            color_obj = color_map.get(color_name)
            if color_obj is None:
                color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})
        else:
            color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "") for field in not_numeric_columns})
        production_data['table_type'] = table_type
        production_data['color'] = color_obj
        production_data = _truncate_charfields(QualityQcFa, production_data)
  

        quality_instances.append(QualityQcFa(**production_data))

    created_quality_instances = QualityQcFa.objects.bulk_create(quality_instances, batch_size=1000)

    defect_types = DefectType.objects.filter(name__in=defeacts_fields)
    defect_type_map = {defect.name: defect for defect in defect_types}

    inspection_defects = []

    for (_, row), quality_instance in zip(df.iterrows(), created_quality_instances):
        for defect_field in defeacts_fields:
            amount = int(row.get(defect_field, 0) or 0)

            if amount <= 0:
                continue

            defect_type = defect_type_map.get(defect_field)
            if defect_type is None:
                continue

            inspection_defects.append(
                InspectionDefect(
                    inspection=quality_instance,
                    defect_type=defect_type,
                    amount=amount,
                )
            )

    if inspection_defects:
        InspectionDefect.objects.bulk_create(inspection_defects, batch_size=2000)


def _bulk_insert_defects_only(df, defeacts_fields, table_type, color_map=None):
    """
    Create only InspectionDefect records, querying existing QualityQcFa parents.

    Used when QualityQcFa records were already created by apply_timewindow.
    Parents are loaded in a single batch query by table_type, indexed in memory
    by the shared QC FA natural key via :func:`build_qc_fa_key`, eliminating
    N+1 per-row DB queries.

    Returns a stats dict with:
        created_defects, matched_parents, unmatched_defect_rows,
        invalid_date_rows, missing_color_rows.

    Args:
        color_map: Optional dict mapping color name → Color instance. When provided,
            avoids N+1 Color.objects.filter() queries per row.
    """
    stats = {
        "created_defects": 0,
        "matched_parents": 0,
        "unmatched_defect_rows": 0,
        "unmatched_row_details": [],  # list of {"key": tuple}
        "invalid_date_rows": 0,
        "missing_color_rows": 0,
    }

    if df.empty:
        return stats

    # ── Resolve DefectType records, auto-creating any that are missing ──
    # Without this, the sync silently skips defects when DefectType records
    # haven't been pre-seeded (e.g. fresh database, first-time import).
    defect_types = DefectType.objects.filter(name__in=defeacts_fields)
    existing_names = set(defect_types.values_list('name', flat=True))
    missing_names = [n for n in defeacts_fields if n not in existing_names]
    if missing_names:
        DefectType.objects.bulk_create(
            [DefectType(name=n, is_active=True) for n in missing_names],
            ignore_conflicts=True,
        )
        # Re-fetch to get PKs for the newly created DefectType records
        defect_types = DefectType.objects.filter(name__in=defeacts_fields)
    defect_type_map = {defect.name: defect for defect in defect_types}

    # ── Batch-load ALL QualityQcFa parents for this table_type ──
    # Loading all parents (scoped by table_type) ensures we match legacy rows
    # with non-ISO dates that would be missed by an exact date_1__in filter.
    parents = QualityQcFa.objects.filter(
        table_type=table_type,
    ).select_related('color')

    # Build in-memory index using the shared QC FA natural-key builder.
    # This ensures the same canonical-date logic is used for both parent
    # creation (sync_service) and defect matching (handler_service).
    parent_index = {}
    for parent in parents:
        parent_row = {
            'date_1': parent.date_1,
            'po': parent.po,
            'style': parent.style or "",
            'team': parent.team,
            'color': parent.color.name if parent.color_id else "",
            'table_type': parent.table_type,
            'line_code': parent.line_code,
        }
        key = build_qc_fa_key(parent_row, table_type=table_type)
        parent_index[key] = parent

    inspection_defects = []
    matched_parent_ids = set()

    for _, row in df.iterrows():
        # ── Skip rows without any positive defect amount ──
        has_defects = any(
            (int(row.get(f, 0) or 0)) > 0 for f in defeacts_fields
        )
        if not has_defects:
            continue

        # ── Resolve color ──
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        if color_map is not None:
            color_obj = color_map.get(color_name)
        else:
            color_obj = Color.objects.filter(name=color_name).first()
        if color_obj is None:
            stats["missing_color_rows"] += 1
            continue

        # ── Validate canonical date ──
        canonical_date = canonicalize_qc_fa_date(row.get('date_1', ''))
        if canonical_date is None:
            stats["invalid_date_rows"] += 1
            continue

        # ── Match parent via shared QC FA natural key ──
        key = build_qc_fa_key(row, table_type=table_type)
        quality_instance = parent_index.get(key)
        if quality_instance is None:
            stats["unmatched_defect_rows"] += 1
            stats["unmatched_row_details"].append({"key": key})
            continue

        matched_parent_ids.add(quality_instance.id)

        for defect_field in defeacts_fields:
            amount = int(row.get(defect_field, 0) or 0)
            if amount <= 0:
                continue

            defect_type = defect_type_map.get(defect_field)
            if defect_type is None:
                continue

            inspection_defects.append(
                InspectionDefect(
                    inspection=quality_instance,
                    defect_type=defect_type,
                    amount=amount,
                )
            )

    if inspection_defects:
        InspectionDefect.objects.bulk_create(inspection_defects, batch_size=2000, ignore_conflicts=True)

    stats["created_defects"] = len(inspection_defects)
    stats["matched_parents"] = len(matched_parent_ids)

    return stats


def bulk_insert_seconds_a4(df, numeric_columns, not_numeric_columns):
    if df.empty:
        return

    instances = []

    for _, row in df.iterrows():
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "") for field in not_numeric_columns})
        production_data['color'] = color_obj
        production_data = _truncate_charfields(SecondsA4, production_data)

        instances.append(SecondsA4(**production_data))

    SecondsA4.objects.bulk_create(instances, batch_size=1000)


def _normalize_nullable_fields(production_data):
    """
    Coerce NaN/blank values in nullable dual-line fields to None.
    
    DataFrame conversion can reintroduce NaN for missing cells. These
    must be normalized back to None before model construction to prevent
    Django from storing "nan"/"NaN" strings or crashing on IntegerField.
    """
    for field in ("team", "line_code"):
        val = production_data.get(field)
        if val is None or pd.isna(val) or val == "":
            production_data[field] = None
    return production_data


def bulk_insert_seconds_general(df, numeric_columns, not_numeric_columns):
    if df.empty:
        return

    from excel_importer.sheet_configs import SECONDS_GENERAL_DEFECT_COLUMNS

    instances = []
    for _, row in df.iterrows():
        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "") for field in not_numeric_columns})
        production_data = _normalize_nullable_fields(production_data)
        production_data = _truncate_charfields(SecondsGeneral, production_data)
        instances.append(SecondsGeneral(**production_data))

    SecondsGeneral.objects.bulk_create(instances, batch_size=1000)

    defect_type_names = SECONDS_GENERAL_DEFECT_COLUMNS
    defect_types = SecondsGeneralDefectType.objects.filter(name__in=defect_type_names)
    defect_type_map = {dt.name: dt for dt in defect_types}

    all_created = SecondsGeneral.objects.order_by('-pk')[:len(instances)]
    # Re-query to get PKs
    date_week_pairs = [(inst.date, inst.week) for inst in instances]
    created_records = SecondsGeneral.objects.filter(
        date__in=[d for d, _ in date_week_pairs],
        week__in=[w for _, w in date_week_pairs],
    ).order_by('pk')

    defects_to_create = []
    for idx, (_, row) in enumerate(df.iterrows()):
        if idx >= len(created_records):
            break
        sg = created_records[idx]
        for defect_field in defect_type_names:
            amount = int(row.get(defect_field, 0) or 0)
            if amount <= 0:
                continue
            defect_type = defect_type_map.get(defect_field)
            if defect_type is None:
                continue
            defects_to_create.append(
                SecondsGeneralDefect(
                    seconds_general=sg,
                    defect_type=defect_type,
                    amount=amount,
                )
            )

    if defects_to_create:
        SecondsGeneralDefect.objects.bulk_create(
            defects_to_create,
            batch_size=2000,
            ignore_conflicts=True,
        )


def bulk_insert_container(df, numeric_columns, not_numeric_columns, defeacts_fields):
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    if df.empty:
        return

    container_instances = []
    container_numbers = df['container_number'].dropna().unique().tolist()
    container_numbers = [int(num) for num in container_numbers if pd.notna(num)]
    existing_dates = {
        c.container_number: c.date
        for c in Container.objects.filter(container_number__in=container_numbers)
    }

    for _, row in df.iterrows():
        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "") for field in not_numeric_columns})
        # Normalize percentage values that Excel stored as fractions
        for pct_field in ('percentage_pass', 'percentage_reject'):
            if pct_field in production_data:
                production_data[pct_field] = _normalize_percentage(production_data[pct_field])
        container_number = row.get('container_number')
        if pd.notna(container_number):
            container_number = int(container_number)
            production_data['container_number'] = container_number

        production_data['date'] = _resolve_container_date(
            row.get('date'),
            existing_dates.get(container_number),
        )
        production_data = _truncate_charfields(Container, production_data)

        container_instances.append(Container(**production_data))

    # Use bulk_create with update_conflicts to handle duplicate container_number
    # This prevents IntegrityError and allows us to upsert existing containers
    Container.objects.bulk_create(
        container_instances,
        batch_size=1000,
        update_conflicts=True,
        unique_fields=['container_number'],
        update_fields=['customer', 'transfer_of_container', 'total_palette', 
                       'total_palette_pass', 'total_palette_rejected', 
                       'percentage_pass', 'percentage_reject', 'date']
    )

    # Build a deterministic mapping from container_number to Container instance
    # by re-querying the database. This ensures we get the actual persisted
    # container (either newly created or existing) for correct defect linking.
    containers_by_number = {
        c.container_number: c 
        for c in Container.objects.filter(container_number__in=container_numbers)
    }

    defect_types = ContainerDefectType.objects.filter(name__in=defeacts_fields)
    defect_type_map = {defect.name: defect for defect in defect_types}

    container_defects = []
    for _, row in df.iterrows():
        container_num = row.get('container_number')
        container_instance = containers_by_number.get(container_num)
        
        if container_instance is None:
            continue

        for defect_field in defeacts_fields:
            amount = int(row.get(defect_field, 0) or 0)

            if amount <= 0:
                continue

            defect_type = defect_type_map.get(defect_field)
            if defect_type is None:
                continue

            container_defects.append(
                ContainerInspectionDefect(
                    container=container_instance,
                    defect_type=defect_type,
                    amount=amount,
                )
            )

    if container_defects:
        ContainerInspectionDefect.objects.bulk_create(
            container_defects, 
            batch_size=2000,
            ignore_conflicts=True  # Skip duplicate (container, defect_type) pairs
        )


def _normalize_percentage(value):
    """
    Convert a percentage value from fractional (0-1) to 0-100 scale if stored
    as a decimal by Excel (e.g. 97% stored as 0.97). Values already on the
    0-100 scale (value > 1) or unsupported types are returned unchanged.

    Args:
        value: The raw percentage value (int, float, or None).

    Returns:
        The normalized value on 0-100 scale, or None unchanged.
    """
    if value is not None and isinstance(value, (int, float)) and 0 < value <= 1:
        return round(value * 100, 2)
    return value


def _resolve_container_date(raw_date, existing_date):
    """Preserve existing non-null date when import date is empty/invalid."""
    normalized = normalize_container_date(raw_date)
    if normalized is not None:
        return normalized
    return existing_date
