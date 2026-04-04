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
)
from excel_importer.date_utils import parse_date


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

# He quitado y vuelto a poner esta funcion como mil veces, ya mejor aqui se queda
def print_headers(file_obj,sheet,header,cols):
    file_obj.seek(0)
    df = pd.read_excel(file_obj, engine='openpyxl', sheet_name=sheet, header=header, usecols=range(cols))
    pd.set_option('display.max_columns', None)
    print(df.columns.tolist())


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


def load_and_clean(file_obj, remap_columns, numeric_columns, defeacts_fields, sheet, header, cols):
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    file_obj.seek(0)
    df = pd.read_excel(file_obj, engine='openpyxl', sheet_name=sheet, header=header, usecols=range(cols))

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
    df[text_cols] = df[text_cols].fillna("UNKNOWN")
    
    return df

def bulk_insert(df, numeric_columns, not_numeric_columns, defeacts_fields, table_type,
                defects_only=False):
    """
    Bulk insert QualityQcFa records and/or InspectionDefect records.

    Args:
        defects_only: If True, skip creating QualityQcFa parents and only create
            InspectionDefect records by querying existing parents. Use this when
            parent records were already created by apply_timewindow.
    """
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    if df.empty:
        return

    # For defects_only mode, query existing parents instead of creating new ones
    if defects_only:
        _bulk_insert_defects_only(df, defeacts_fields, table_type)
        return

    quality_instances = []

    for _, row in df.iterrows():

        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
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


def _bulk_insert_defects_only(df, defeacts_fields, table_type):
    """
    Create only InspectionDefect records, querying existing QualityQcFa parents.

    Used when QualityQcFa records were already created by apply_timewindow.
    Parents are queried by natural key: date_1 + po + style + team + color.
    """
    defect_types = DefectType.objects.filter(name__in=defeacts_fields)
    defect_type_map = {defect.name: defect for defect in defect_types}

    inspection_defects = []

    for _, row in df.iterrows():
        # Query existing QualityQcFa by natural key
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj = Color.objects.filter(name=color_name).first()
        if color_obj is None:
            continue

        # Build natural key query - same as build_qc_fa_plant_key in sync_service
        query = {
            'table_type': table_type,
            'date_1': parse_date(row.get('date_1', '')),
            'po': int(row.get('po', 0)) if row.get('po') else 0,
            'style': str(row.get('style', '')).strip(),
            'team': int(row.get('team', 0)) if row.get('team') else 0,
            'color': color_obj,
        }

        # Only query if we have valid key values
        if not query['date_1'] or not query['style']:
            continue

        quality_instance = QualityQcFa.objects.filter(**query).first()
        if quality_instance is None:
            continue

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


def bulk_insert_seconds_a4(df, numeric_columns, not_numeric_columns):
    if df.empty:
        return

    instances = []

    for _, row in df.iterrows():
        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
        production_data['color'] = color_obj
        production_data = _truncate_charfields(SecondsA4, production_data)

        instances.append(SecondsA4(**production_data))

    SecondsA4.objects.bulk_create(instances, batch_size=1000)


def bulk_insert_seconds_general(df, numeric_columns, not_numeric_columns):
    if df.empty:
        return

    instances = []

    for _, row in df.iterrows():
        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
        production_data = _truncate_charfields(SecondsGeneral, production_data)

        instances.append(SecondsGeneral(**production_data))

    SecondsGeneral.objects.bulk_create(instances, batch_size=1000)


def bulk_insert_container(df, numeric_columns, not_numeric_columns, defeacts_fields):
    defeacts_fields = _normalize_defects_fields(defeacts_fields)

    if df.empty:
        return

    container_instances = []

    for _, row in df.iterrows():
        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
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
                       'percentage_pass', 'percentage_reject']
    )

    # Build a deterministic mapping from container_number to Container instance
    # by re-querying the database. This ensures we get the actual persisted
    # container (either newly created or existing) for correct defect linking.
    container_numbers = [row.get('container_number') for _, row in df.iterrows()]
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