import pandas as pd
from datetime import datetime
from quality_data.models import QualityQcFa, AmountDefects
import math



def load_and_clean(file_obj, remap_columns, numeric_columns,defeacts_fields, sheet, header, cols):
    df = pd.read_excel(file_obj, engine='openpyxl', sheet_name=sheet, header=header, usecols=range(cols))
    df = df.dropna(how='all').dropna(axis=1, how='all')
    df = df.rename(columns=remap_columns)
    
 

    numeric_and_defects_cols = list(set(numeric_columns + defeacts_fields))

    for col in numeric_and_defects_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if "pass_or_fail" in df.columns:
        mask = ~df["pass_or_fail"].isin(["Pass", "Fail"])
        df.loc[mask, "pass_or_fail"] = "Pass"

    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].fillna("UNKNOWN")
    
    return df

def bulk_insert(df, numeric_columns, not_numeric_columns, defeacts_fields):
    quality_instances = []

    defect_data = [
        AmountDefects (**{field: row.get(field, 0) for field in defeacts_fields})
        for _, row in df.iterrows()
    ]

    created_defects = AmountDefects.objects.bulk_create(defect_data)

    for (_, row), defect_obj in zip(df.iterrows(), created_defects):

        production_data = {field: row.get(field, 0) for field in numeric_columns}
        production_data.update({field: row.get(field, "UNKNOWN") for field in not_numeric_columns})
        production_data['defeacts'] = defect_obj
 

        quality_instances.append(QualityQcFa(**production_data))

    QualityQcFa.objects.bulk_create(quality_instances, batch_size=1000)