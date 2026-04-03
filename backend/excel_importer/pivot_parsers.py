"""
Pivot table parsers for KPI Excel dynamic ranges.

These parsers read specific ranges from Excel sheets that contain
pivot table data for KPIs (seconds rework, cut qty, fabric defects, enganche).
"""
import pandas as pd
from excel_importer.handler_service import load_pivot_range
from excel_importer.sheet_configs import PIVOT_RANGES


def _clean_percentage_value(value):
    """
    Convert percentage string like "4.31 %" to float 4.31.
    Handles strings, floats, and other numeric types.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove percentage symbol and whitespace
        cleaned = value.replace('%', '').replace(' ', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _clean_integer_value(value):
    """
    Convert string with thousand separators like "4,896" to int 4896.
    Handles strings, ints, floats, and other numeric types.
    """
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        # Remove thousand separators (commas)
        cleaned = value.replace(',', '').strip()
        try:
            return int(float(cleaned))
        except ValueError:
            return 0
    return 0


def parse_seconds_rework(file_obj):
    """
    Parse seconds rework pivot table from SecondsA4 sheet.

    Expected columns after header row 8:
        - Week
        - Sum of 2DA BY SEW
        - Sum of 2DA BY FAB

    Excludes 'Grand Total' row.
    Cleans percentage strings like "4.31 %" to float values.

    Returns:
        [
            {"name": "Sewing", "data": [{"x": week, "y": value}, ...]},
            {"name": "Fabric", "data": [{"x": week, "y": value}, ...]}
        ]
        or None if parsing fails
    """
    try:
        config = PIVOT_RANGES['seconds_rework']
        df = load_pivot_range(
            file_obj,
            sheet=config['sheet'],
            header_row=config['header_row'],
            usecols=config['usecols'],
            nrows=config['nrows']
        )

        if df.empty:
            return None

        # Rename columns for clarity
        df.columns = ['week', 'sewing', 'fabric']

        # Exclude Grand Total row
        df = df[df['week'].astype(str).str.lower() != 'grand total']

        # Clean percentage values
        df['sewing'] = df['sewing'].apply(_clean_percentage_value)
        df['fabric'] = df['fabric'].apply(_clean_percentage_value)

        sewing_data = [
            {"x": int(row['week']), "y": row['sewing']}
            for _, row in df.iterrows()
        ]

        fabric_data = [
            {"x": int(row['week']), "y": row['fabric']}
            for _, row in df.iterrows()
        ]

        return [
            {"name": "Sewing", "data": sewing_data},
            {"name": "Fabric", "data": fabric_data},
        ]

    except Exception:
        return None


def parse_cut_qty(file_obj):
    """
    Parse cut quantity pivot table from SecondsA4 sheet.

    Expected columns after header row 70:
        - Week
        - Sum of CUT QTY

    Includes 'Total Resultado' row.
    Cleans thousand separators like "4,896" to int 4896.

    Returns:
        [{"name": "Cut Qty", "data": [{"x": week, "y": qty}, ...]}]
        or None if parsing fails
    """
    try:
        config = PIVOT_RANGES['cut_qty']
        df = load_pivot_range(
            file_obj,
            sheet=config['sheet'],
            header_row=config['header_row'],
            usecols=config['usecols'],
            nrows=config['nrows']
        )

        if df.empty:
            return None

        # Rename columns for clarity
        df.columns = ['week', 'cut_qty']

        # Clean integer values (handle thousand separators)
        df['cut_qty'] = df['cut_qty'].apply(_clean_integer_value)

        data = [
            {"x": str(row['week']), "y": row['cut_qty']}
            for _, row in df.iterrows()
        ]

        return [{"name": "Cut Qty", "data": data}]

    except Exception:
        return None


def parse_fabric_defects(file_obj):
    """
    Parse fabric defects from two ranges in Seconds General sheet.

    Reads both 'fabric_defects_corrido2' (row 3) and 'fabric_defects_corrido' (row 49).
    Both have columns: Color, Sum of Corrido(X)

    Merges by Color and sums values.
    Excludes 'Total Resultado' row.
    Returns sorted by value descending.

    Returns:
        [{"label": color, "value": total}, ...]
        or None if parsing fails
    """
    try:
        # Read first range (corrido2)
        config1 = PIVOT_RANGES['fabric_defects_corrido2']
        df1 = load_pivot_range(
            file_obj,
            sheet=config1['sheet'],
            header_row=config1['header_row'],
            usecols=config1['usecols'],
            nrows=config1['nrows']
        )
        df1.columns = ['color', 'corrido_value']
        df1['corrido_value'] = df1['corrido_value'].apply(_clean_integer_value)

        # Read second range (corrido)
        config2 = PIVOT_RANGES['fabric_defects_corrido']
        df2 = load_pivot_range(
            file_obj,
            sheet=config2['sheet'],
            header_row=config2['header_row'],
            usecols=config2['usecols'],
            nrows=config2['nrows']
        )
        df2.columns = ['color', 'corrido_value']
        df2['corrido_value'] = df2['corrido_value'].apply(_clean_integer_value)

        if df1.empty and df2.empty:
            return None

        # Concatenate both ranges
        df_combined = pd.concat([df1, df2], ignore_index=True)

        # Exclude Total Resultado
        df_combined = df_combined[
            df_combined['color'].astype(str).str.lower() != 'total resultado'
        ]

        # Group by color and sum values
        aggregated = df_combined.groupby('color', as_index=False)['corrido_value'].sum()
        aggregated = aggregated.sort_values('corrido_value', ascending=False)

        result = [
            {"label": str(row['color']), "value": int(row['corrido_value'])}
            for _, row in aggregated.iterrows()
        ]

        return result

    except Exception:
        return None


def parse_enganche(file_obj):
    """
    Parse enganche pivot table from Seconds General sheet.

    Expected columns after header row 42:
        - Week
        - Sum of Enganche

    Includes 'Total Resultado' row.

    Returns:
        [{"name": "Enganche", "data": [{"x": week, "y": value}, ...]}]
        or None if parsing fails
    """
    try:
        config = PIVOT_RANGES['enganche']
        df = load_pivot_range(
            file_obj,
            sheet=config['sheet'],
            header_row=config['header_row'],
            usecols=config['usecols'],
            nrows=config['nrows']
        )

        if df.empty:
            return None

        # Rename columns for clarity
        df.columns = ['week', 'enganche']

        # Clean values
        df['enganche'] = df['enganche'].apply(_clean_integer_value)

        data = [
            {"x": str(row['week']), "y": row['enganche']}
            for _, row in df.iterrows()
        ]

        return [{"name": "Enganche", "data": data}]

    except Exception:
        return None
