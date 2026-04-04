"""
Pivot table parsers for KPI Excel dynamic ranges.

These parsers read specific ranges from Excel sheets that contain
pivot table data for KPIs (seconds rework, cut qty, fabric defects, enganche,
top defects, defects by style type, containers by state).
"""
import pandas as pd
from excel_importer.handler_service import load_pivot_range, load_and_clean
from excel_importer.sheet_configs import (
    PIVOT_RANGES, CONTAINER_REMAP, CONTAINER_NUMERIC_COLUMNS,
    CONTAINER_NOT_NUMERIC_COLUMNS, QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS
)


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


# ─────────────────────────────────────────────────────────
# QC FA Plant based parsers (use pre-parsed rows, no Excel read)
# ─────────────────────────────────────────────────────────

DEFECT_LABEL_MAP = {
    'uneven': 'Uneven', 'broken_stitch': 'Broken Stitch', 'open_seam': 'Open Seam',
    'tear': 'Tear', 'hi_low': 'Hi Low', 'run_off_stitch': 'Run Off Stitch',
    'raw_edge': 'Raw Edge', 'neddle_holes': 'Needle Holes', 'loose_thread': 'Loose Thread',
    'uncut_thread': 'Uncut Thread', 'big_or_littler_neck': 'Big/Littler Neck',
    'uneven_neck_or_sleeve': 'Uneven Neck/Sleeve', 'out_of_measurements': 'Out of Measurements',
    'incorrect_stitch': 'Incorrect Stitch', 'variation_tension_sttich': 'Variation Tension',
    'excess_fabric': 'Excess Fabric', 'hitched': 'Hitched', 'po_midex': 'PO Mixed',
    'transfer_peel_off_or_leave': 'Transfer Peel Off', 'wrong_transfer': 'Wrong Transfer',
    'wrong_label': 'Wrong Label', 'missing_transfer': 'Missing Transfer',
    'missing_label': 'Missing Label', 'shine': 'Shine', 'skip_stitch': 'Skip Stitch',
    'pleat': 'Pleat', 'dirt_marck': 'Dirt Mark', 'missing_operation': 'Missing Operation',
    'stain_oil_soil': 'Stain/Oil/Soil', 'contamination': 'Contamination',
    'construction_defect': 'Construction Defect', 'mill_flaw': 'Mill Flaw',
    'fabric_run': 'Fabric Run', 'misplaced': 'Misplaced', 'pucketing': 'Puckering',
    'slanted': 'Slanted', 'defect_sticker_inside': 'Sticker Inside', 'roping': 'Roping',
    'label_slanted': 'Label Slanted', 'shadding': 'Shading',
    'missing_packing_trims': 'Missing Packing Trims',
    'missing_print_or_embroidery': 'Missing Print/Embroidery',
    'wrong_packing_trims': 'Wrong Packing Trims', 'wrong_po': 'Wrong PO',
    'wrong_folding_method': 'Wrong Folding', 'wrong_size_attached': 'Wrong Size',
    'damaged_label': 'Damaged Label', 'pocket_label': 'Pocket Label',
    'label_placement': 'Label Placement', 'missing_information_label': 'Missing Info Label',
}


def parse_top_defects(rows):
    """
    Calcula Top Defectos desde las filas ya parseadas de QC FA Plant.
    SUM cada columna de defecto, ordena DESC, top 10.

    Returns: [{"label": "Loose Thread", "value": 234}, ...] or None on error.
    """
    try:
        if not rows:
            return []

        totals = {}
        for field in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS:
            total = sum(int(row.get(field, 0) or 0) for row in rows)
            if total > 0:
                label = DEFECT_LABEL_MAP.get(field, field.replace('_', ' ').title())
                totals[label] = totals.get(label, 0) + total

        result = [{"label": k, "value": v} for k, v in totals.items()]
        result.sort(key=lambda x: x['value'], reverse=True)
        return result[:10]

    except Exception:
        return None


def parse_defects_by_style(rows):
    """
    Calcula Defectos por Estilo × Tipo desde las filas ya parseadas de QC FA Plant.
    Top 5 styles × top 5 defect types.

    Returns: [{"x": "Style-2", "y": "Loose Thread", "value": 45}, ...] or None on error.
    """
    try:
        if not rows:
            return []

        # Top 5 styles by total defects
        style_totals = {}
        for row in rows:
            style = row.get('style', 'Unknown')
            total = sum(int(row.get(f, 0) or 0) for f in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS)
            style_totals[style] = style_totals.get(style, 0) + total

        top_styles = sorted(style_totals, key=style_totals.get, reverse=True)[:5]

        # Top 5 defect types by total amount
        defect_totals = {}
        for row in rows:
            for field in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS:
                val = int(row.get(field, 0) or 0)
                if val > 0:
                    defect_totals[field] = defect_totals.get(field, 0) + val

        top_defect_fields = sorted(defect_totals, key=defect_totals.get, reverse=True)[:5]

        # Build heatmap: style × defect
        from collections import defaultdict
        agg = defaultdict(int)
        for row in rows:
            style = row.get('style', 'Unknown')
            if style not in top_styles:
                continue
            for field in top_defect_fields:
                val = int(row.get(field, 0) or 0)
                if val > 0:
                    label = DEFECT_LABEL_MAP.get(field, field.replace('_', ' ').title())
                    agg[(style, label)] += val

        return [{"x": k[0], "y": k[1], "value": v} for k, v in agg.items()]

    except Exception:
        return None


def parse_containers_by_state(file_obj):
    """
    Lee el sheet Container del Excel y agrupa por rangos de percentage_pass.
    Rangos: < 80%, 80-90%, 90-95%, > 95%

    Returns: [{"name": "< 80%", "value": 3}, ...] or None on error.
    """
    try:
        df = load_and_clean(
            file_obj, CONTAINER_REMAP, CONTAINER_NUMERIC_COLUMNS,
            CONTAINER_NOT_NUMERIC_COLUMNS, "Container", 2, 24
        )

        if df.empty:
            return []

        # Convert percentage_pass to numeric
        df['percentage_pass'] = pd.to_numeric(df['percentage_pass'], errors='coerce').fillna(0)

        # Group by ranges
        ranges = [
            ("< 80%", (df['percentage_pass'] < 80).sum()),
            ("80-90%", ((df['percentage_pass'] >= 80) & (df['percentage_pass'] < 90)).sum()),
            ("90-95%", ((df['percentage_pass'] >= 90) & (df['percentage_pass'] < 95)).sum()),
            ("> 95%", (df['percentage_pass'] >= 95).sum()),
        ]

        return [{"name": name, "value": int(count)} for name, count in ranges]

    except Exception:
        return None
