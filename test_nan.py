import pandas as pd
from backend.excel_importer.date_utils import build_qc_fa_key

df = pd.DataFrame([{"po": 123, "style": "abc", "team": 1, "color": "red"}])
row = next(df.iterrows())[1]
key = build_qc_fa_key(row, "QFC")
print(f"Key from pandas row: {key}")

parent_row = {"po": 123, "style": "abc", "team": 1, "color": "red", "line_code": None}
parent_key = build_qc_fa_key(parent_row, "QFC")
print(f"Key from parent: {parent_key}")

print(f"Match: {key == parent_key}")
