import pandas as pd
from datetime import datetime
from quality_data.models import QualityQcFa, amount_defects

# file_path = "./data/data.xlsx"
file_path = "/app/excel_importer/data/data.xlsx"
sheet_names = [
    ("QC FA Plant", 2, 67),
    ("QC FA Customer", 0, 64),
    ("SecondsA4", 1, 22),
    ("Seconds General", 1, 22),
    ("Container", 2, 24),
]

def load_and_clean(sheet, header, cols):
    df = pd.read_excel(file_path, sheet_name=sheet, header=header, usecols=range(cols))
    df = df.dropna(how='all').dropna(axis=1, how='all')
 

    numeric_columns = [
        "Week", "Po", "Batch", "Qty", "Seconds", "Accepted", "Rejected", "Sample", "Defects", "AQL %"
    ]
    
    for col in df.columns:
        if col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("UNKNOWN")
    return df

qc_fa_plant_df = load_and_clean(*sheet_names[0])
# qc_fa_customer_df = load_and_clean(*sheet_names[1])
# secondsA4_df = load_and_clean(*sheet_names[2])
# seconds_general_df = load_and_clean(*sheet_names[3])
# container_df = load_and_clean(*sheet_names[4])


# pd.set_option('display.max_columns', None)
# print(qc_fa_plant_df.columns)


def bulk_insert_qc_fa(df, batch_size: int | None = None):

    import math
    def clean_value(value):
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    instances: list[QualityQcFa] = []
    for _, row in df.iterrows():
        instances.append(
            QualityQcFa(
                date_1=clean_value(row.get("Date")),
                week=clean_value(row.get("Week")),
                customer=clean_value(row.get("Customer")),
                team=clean_value(row.get("Team")),
                coord=clean_value(row.get("COORD.")),
                date_2=clean_value(row.get("Date2")),
                po=clean_value(row.get("Po")),
                style=clean_value(row.get("Style")),
                batch=clean_value(row.get("Batch")),
                color=clean_value(row.get("Color")),
                qty=clean_value(row.get("Qty")),
                seconds=clean_value(row.get("Seconds")),
                accepted=clean_value(row.get("Accepted")),
                rejected=clean_value(row.get("Rejected")),
                sample=clean_value(row.get("Sample")),
                defeacts=clean_value(row.get("Defects")),
                aql=clean_value(row.get("AQL %")),
                pass_or_fail=clean_value(row.get("Pass/Fail")),
            )
        )
    if not instances:
        return 0

    total = len(instances)

    if batch_size is None:
        batch_size = min(500, total)

    QualityQcFa.objects.bulk_create(instances, batch_size=batch_size)
    return total


# Guardar datos de qc_fa_plant_df
created = bulk_insert_qc_fa(qc_fa_plant_df)
print(f"imported {created} qc_fa_plant rows")



