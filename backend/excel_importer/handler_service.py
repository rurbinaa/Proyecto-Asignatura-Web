import pandas as pd
from quality_data.models import Color, DefectType, InspectionDefect, QualityQcFa



def load_and_clean(file_obj, remap_columns, numeric_columns, defeacts_fields, sheet, header, cols):
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
        df["pass_or_fail"] = "Pass"
        df.loc[normalized_pass_or_fail == "FAIL", "pass_or_fail"] = "Fail"

    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].fillna("UNKNOWN")
    
    return df

def bulk_insert(df, numeric_columns, not_numeric_columns, defeacts_fields, table_type):
    if df.empty:
        return

    quality_instances = []

    for _, row in df.iterrows():

        color_name = str(row.get("color", "unknown")).strip().lower().replace(" ", "_")
        color_obj, _ = Color.objects.get_or_create(name=color_name, defaults={"is_active": True})

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
        production_data['table_type'] = table_type
        production_data['color'] = color_obj
 

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