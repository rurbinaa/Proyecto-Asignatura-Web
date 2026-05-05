import pandas as pd

def patch_line_code(row):
    raw_line_code = row.get("line_code")
    if pd.isna(raw_line_code) or str(raw_line_code).strip() == "":
        return None
    return str(raw_line_code).strip()

row1 = pd.Series({"line_code": float('nan')})
row2 = pd.Series({"line_code": ""})
row3 = pd.Series({"line_code": "A1"})
row4 = pd.Series({})

print(f"NaN -> {patch_line_code(row1)}")
print(f"Empty -> {patch_line_code(row2)}")
print(f"A1 -> {patch_line_code(row3)}")
print(f"Missing -> {patch_line_code(row4)}")
