import pandas as pd

file_path = "../../docs/general/data.xlsx"
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
    return df

qc_fa_plant_df = load_and_clean(*sheet_names[0])
qc_fa_customer_df = load_and_clean(*sheet_names[1])
secondsA4_df = load_and_clean(*sheet_names[2])
seconds_general_df = load_and_clean(*sheet_names[3])
container_df = load_and_clean(*sheet_names[4])



print(qc_fa_plant_df)
print(qc_fa_customer_df)
print(secondsA4_df)
print(seconds_general_df)
print(container_df)