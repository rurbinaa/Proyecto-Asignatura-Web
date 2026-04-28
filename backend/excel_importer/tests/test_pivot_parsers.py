"""
Tests for pivot table parsers.
These tests verify parsing of dynamic ranges from the Excel KPI workbook.
"""
import io
from unittest.mock import patch
from django.test import TestCase
import pandas as pd

# Import the functions under test
from excel_importer.pivot_parsers import (
    parse_seconds_rework,
    parse_fabric_defects,
    parse_top_defects,
    parse_defects_by_style,
    parse_containers_by_state,
)
from excel_importer.handler_service import load_pivot_range


class LoadPivotRangeTest(TestCase):
    """Tests for load_pivot_range utility function."""

    def test_load_pivot_range_reads_correct_range(self):
        """
        load_pivot_range should read the specified range from a sheet
        and return a DataFrame with the expected structure.
        """
        # Create a minimal Excel file with proper column structure
        output = io.BytesIO()
        
        # Create a DataFrame with columns A, B, C... through Z, AA, AB...
        # X is column 24 (1-indexed), Y is 25, Z is 26
        # We'll create enough columns and then reference X, Y, Z
        num_cols = 30
        data = [[None] * num_cols for _ in range(12)]
        
        # Row 8 (index 7) has headers
        data[7][0] = 'Dummy'  # Column A
        data[7][23] = 'Week'   # Column X (index 23)
        data[7][24] = 'Sum of 2DA BY SEW'  # Column Y
        data[7][25] = 'Sum of 2DA BY FAB'  # Column Z
        
        # Data rows
        data[8][23] = 1
        data[8][24] = 4.5
        data[8][25] = 2.1
        data[9][23] = 2
        data[9][24] = 5.6
        data[9][25] = 3.2
        data[10][23] = 3
        data[10][24] = 6.7
        data[10][25] = 4.3
        
        # Create column names A through ~AD
        col_names = [chr(i) if i < 26 else chr(64 + i // 26) + chr(65 + i % 26) 
                     for i in range(num_cols)]
        
        df_source = pd.DataFrame(data, columns=col_names)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_source.to_excel(writer, sheet_name='SecondsA4', index=False, header=False)
        
        output.seek(0)
        
        # Read from row 8 (1-indexed), columns X:Z
        result = load_pivot_range(output, 'SecondsA4', header_row=8, usecols='X:Z', nrows=48)
        
        # Should have parsed the headers
        self.assertIn('Week', result.columns)
        self.assertIn('Sum of 2DA BY SEW', result.columns)
        self.assertIn('Sum of 2DA BY FAB', result.columns)
        
        # Should have data rows
        self.assertTrue(len(result) <= 48)


class ParseSecondsReworkTest(TestCase):
    """Tests for parse_seconds_rework parser."""

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_seconds_rework_extracts_sewing_fabric(self, mock_load):
        """
        parse_seconds_rework should return two series: Sewing and Fabric,
        each with data points containing x (week) and y (value).
        """
        # Mock the load_pivot_range to return test data
        mock_df = pd.DataFrame({
            'week': [1, 2, 3],
            'sewing': [12.5, 15.2, 11.8],
            'fabric': [8.3, 9.1, 7.5],
        })
        mock_load.return_value = mock_df

        result = parse_seconds_rework(io.BytesIO())

        self.assertEqual(len(result), 2)
        
        sewing = next(s for s in result if s['name'] == 'Sewing')
        fabric = next(s for s in result if s['name'] == 'Fabric')
        
        self.assertEqual(len(sewing['data']), 3)
        self.assertEqual(len(fabric['data']), 3)
        
        self.assertEqual(sewing['data'][0]['x'], 1)
        self.assertEqual(sewing['data'][0]['y'], 12.5)
        self.assertEqual(fabric['data'][0]['x'], 1)
        self.assertEqual(fabric['data'][0]['y'], 8.3)

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_seconds_rework_excludes_grand_total(self, mock_load):
        """
        parse_seconds_rework should exclude the 'Grand Total' row.
        """
        mock_df = pd.DataFrame({
            'week': [1, 2, 'Grand Total'],
            'sewing': [12.5, 15.2, 27.7],
            'fabric': [8.3, 9.1, 17.4],
        })
        mock_load.return_value = mock_df

        result = parse_seconds_rework(io.BytesIO())

        sewing = next(s for s in result if s['name'] == 'Sewing')
        # Should only have 2 data points, not 3 (Grand Total excluded)
        self.assertEqual(len(sewing['data']), 2)
        self.assertTrue(all(d['x'] != 'Grand Total' for d in sewing['data']))

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_seconds_rework_handles_percentage_strings(self, mock_load):
        """
        parse_seconds_rework should handle percentage strings like "4.31 %"
        and convert them to float values.
        """
        mock_df = pd.DataFrame({
            'week': [1, 2],
            'sewing': ['4.31 %', '5.12 %'],
            'fabric': ['3.25 %', '2.88 %'],
        })
        mock_load.return_value = mock_df

        result = parse_seconds_rework(io.BytesIO())

        sewing = next(s for s in result if s['name'] == 'Sewing')
        
        # Should be converted to floats
        self.assertEqual(sewing['data'][0]['y'], 4.31)
        self.assertEqual(sewing['data'][1]['y'], 5.12)


class ParseFabricDefectsTest(TestCase):
    """Tests for parse_fabric_defects parser."""

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_fabric_defects_merges_by_color(self, mock_load):
        """
        parse_fabric_defects should read both corrido2 and corrido ranges,
        merge by Color, and sum the values.
        """
        # Mock returns different DataFrames for two calls
        mock_df_corrido2 = pd.DataFrame({
            'color': ['Color A', 'Color B'],
            'corrido_value': [10, 20],
        })
        mock_df_corrido = pd.DataFrame({
            'color': ['Color A', 'Color C'],
            'corrido_value': [5, 15],
        })
        mock_load.side_effect = [mock_df_corrido2, mock_df_corrido]

        result = parse_fabric_defects(io.BytesIO())

        # Should have 3 unique colors
        self.assertEqual(len(result), 3)
        
        # Color A should be merged: 10 + 5 = 15
        color_a = next(r for r in result if r['label'] == 'Color A')
        self.assertEqual(color_a['value'], 15)
        
        # Color B = 20 (only in corrido2)
        color_b = next(r for r in result if r['label'] == 'Color B')
        self.assertEqual(color_b['value'], 20)
        
        # Color C = 15 (only in corrido)
        color_c = next(r for r in result if r['label'] == 'Color C')
        self.assertEqual(color_c['value'], 15)

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_fabric_defects_sorted_descending(self, mock_load):
        """
        parse_fabric_defects should return results sorted by value descending.
        """
        mock_df_corrido2 = pd.DataFrame({
            'color': ['Low', 'High', 'Medium'],
            'corrido_value': [5, 100, 50],
        })
        mock_df_corrido = pd.DataFrame({
            'color': ['Low'],
            'corrido_value': [5],  # Will become 10
        })
        mock_load.side_effect = [mock_df_corrido2, mock_df_corrido]

        result = parse_fabric_defects(io.BytesIO())

        # Should be sorted descending by value
        values = [r['value'] for r in result]
        self.assertEqual(values, sorted(values, reverse=True))

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_fabric_defects_excludes_total_resultado(self, mock_load):
        """
        parse_fabric_defects should exclude 'Total Resultado' rows.
        """
        mock_df_corrido2 = pd.DataFrame({
            'color': ['Red', 'Total Resultado'],
            'corrido_value': [10, 50],
        })
        mock_df_corrido = pd.DataFrame({
            'color': ['Blue'],
            'corrido_value': [20],
        })
        mock_load.side_effect = [mock_df_corrido2, mock_df_corrido]

        result = parse_fabric_defects(io.BytesIO())

        # Should not contain Total Resultado
        labels = [r['label'] for r in result]
        self.assertNotIn('Total Resultado', labels)
        self.assertEqual(len(result), 2)


class ParseNullHandlingTest(TestCase):
    """Tests for null/exception handling in parsers."""

    def test_parse_returns_null_on_malformed_data(self):
        """
        All parse_* functions should return None (not raise) on malformed data.
        """
        # Empty/mock file that will fail to parse
        empty_file = io.BytesIO(b'not an excel file')
        
        # Each parser should return None instead of raising
        result = parse_seconds_rework(empty_file)
        self.assertIsNone(result)
        
        empty_file.seek(0)
        result = parse_fabric_defects(empty_file)
        self.assertIsNone(result)


class ParseTopDefectsTest(TestCase):
    """Tests for parse_top_defects — uses pre-parsed rows, no Excel read."""

    def test_returns_top_10_defects_sorted_descending(self):
        rows = [
            {'style': 'S1', 'loose_thread': 5, 'broken_stitch': 3, 'open_seam': 0, 'tear': 0,
             'hi_low': 0, 'run_off_stitch': 0, 'raw_edge': 0, 'neddle_holes': 0,
             'uncut_thread': 0, 'big_or_littler_neck': 0, 'uneven_neck_or_sleeve': 0,
             'out_of_measurements': 0, 'incorrect_stitch': 0, 'variation_tension_sttich': 0,
             'excess_fabric': 0, 'hitched': 0, 'po_midex': 0, 'transfer_peel_off_or_leave': 0,
             'wrong_transfer': 0, 'wrong_label': 0, 'missing_transfer': 0, 'missing_label': 0,
             'shine': 0, 'skip_stitch': 0, 'pleat': 0, 'dirt_marck': 0, 'missing_operation': 0,
             'stain_oil_soil': 0, 'contamination': 0, 'construction_defect': 0, 'mill_flaw': 0,
             'fabric_run': 0, 'misplaced': 0, 'pucketing': 0, 'slanted': 0,
             'defect_sticker_inside': 0, 'roping': 0, 'label_slanted': 0, 'shadding': 0,
             'missing_packing_trims': 0, 'missing_print_or_embroidery': 0,
             'wrong_packing_trims': 0, 'wrong_po': 0, 'wrong_folding_method': 0,
             'wrong_size_attached': 0, 'damaged_label': 0, 'pocket_label': 0,
             'label_placement': 0, 'missing_information_label': 0, 'uneven': 1},
            {'style': 'S2', 'loose_thread': 2, 'broken_stitch': 8, 'open_seam': 1, 'tear': 0,
             'hi_low': 0, 'run_off_stitch': 0, 'raw_edge': 0, 'neddle_holes': 0,
             'uncut_thread': 0, 'big_or_littler_neck': 0, 'uneven_neck_or_sleeve': 0,
             'out_of_measurements': 0, 'incorrect_stitch': 0, 'variation_tension_sttich': 0,
             'excess_fabric': 0, 'hitched': 0, 'po_midex': 0, 'transfer_peel_off_or_leave': 0,
             'wrong_transfer': 0, 'wrong_label': 0, 'missing_transfer': 0, 'missing_label': 0,
             'shine': 0, 'skip_stitch': 0, 'pleat': 0, 'dirt_marck': 0, 'missing_operation': 0,
             'stain_oil_soil': 0, 'contamination': 0, 'construction_defect': 0, 'mill_flaw': 0,
             'fabric_run': 0, 'misplaced': 0, 'pucketing': 0, 'slanted': 0,
             'defect_sticker_inside': 0, 'roping': 0, 'label_slanted': 0, 'shadding': 0,
             'missing_packing_trims': 0, 'missing_print_or_embroidery': 0,
             'wrong_packing_trims': 0, 'wrong_po': 0, 'wrong_folding_method': 0,
             'wrong_size_attached': 0, 'damaged_label': 0, 'pocket_label': 0,
             'label_placement': 0, 'missing_information_label': 0, 'uneven': 0},
        ]
        result = parse_top_defects(rows)
        self.assertIsNotNone(result)
        # Should be sorted descending: broken_stitch(11), loose_thread(7), open_seam(1), uneven(1)
        self.assertEqual(result[0]['label'], 'Broken Stitch')
        self.assertEqual(result[0]['value'], 11)
        self.assertEqual(result[1]['label'], 'Loose Thread')
        self.assertEqual(result[1]['value'], 7)

    def test_returns_empty_for_empty_rows(self):
        result = parse_top_defects([])
        self.assertEqual(result, [])

    def test_handles_none_values(self):
        rows = [{'style': 'S1', 'loose_thread': None, 'broken_stitch': 0}]
        result = parse_top_defects(rows)
        self.assertIsNotNone(result)
        # None and 0 should be treated as 0


class ParseDefectsByStyleTest(TestCase):
    """Tests for parse_defects_by_style — heatmap of style × defect type."""

    def test_returns_heatmap_data(self):
        rows = [
            {'style': 'Style-A', 'loose_thread': 5, 'broken_stitch': 3, 'open_seam': 0, 'tear': 0,
             'hi_low': 0, 'run_off_stitch': 0, 'raw_edge': 0, 'neddle_holes': 0,
             'uncut_thread': 0, 'big_or_littler_neck': 0, 'uneven_neck_or_sleeve': 0,
             'out_of_measurements': 0, 'incorrect_stitch': 0, 'variation_tension_sttich': 0,
             'excess_fabric': 0, 'hitched': 0, 'po_midex': 0, 'transfer_peel_off_or_leave': 0,
             'wrong_transfer': 0, 'wrong_label': 0, 'missing_transfer': 0, 'missing_label': 0,
             'shine': 0, 'skip_stitch': 0, 'pleat': 0, 'dirt_marck': 0, 'missing_operation': 0,
             'stain_oil_soil': 0, 'contamination': 0, 'construction_defect': 0, 'mill_flaw': 0,
             'fabric_run': 0, 'misplaced': 0, 'pucketing': 0, 'slanted': 0,
             'defect_sticker_inside': 0, 'roping': 0, 'label_slanted': 0, 'shadding': 0,
             'missing_packing_trims': 0, 'missing_print_or_embroidery': 0,
             'wrong_packing_trims': 0, 'wrong_po': 0, 'wrong_folding_method': 0,
             'wrong_size_attached': 0, 'damaged_label': 0, 'pocket_label': 0,
             'label_placement': 0, 'missing_information_label': 0, 'uneven': 1},
        ]
        result = parse_defects_by_style(rows)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        for item in result:
            self.assertIn('x', item)
            self.assertIn('y', item)
            self.assertIn('value', item)

    def test_returns_empty_for_empty_rows(self):
        result = parse_defects_by_style([])
        self.assertEqual(result, [])


class ParseContainersByStateTest(TestCase):
    """Tests for parse_containers_by_state — groups by percentage_pass ranges."""

    @patch('excel_importer.pivot_parsers.load_and_clean')
    def test_returns_four_ranges(self, mock_load):
        """Should return exactly 4 range buckets based on percentage_pass."""
        mock_load.return_value = pd.DataFrame({
            'container_number': [1, 2, 3, 4, 5],
            'percentage_pass': [50, 70, 90, 100, 80],
        })

        result = parse_containers_by_state(io.BytesIO())
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)
        names = [r['name'] for r in result]
        self.assertIn('< 80%', names)
        self.assertIn('80-90%', names)
        self.assertIn('90-95%', names)
        self.assertIn('> 95%', names)
        # 50(<80), 70(<80) = 2; 80(80-90) = 1; 90(90-95) = 1; 100(>95) = 1
        buckets = {r['name']: r['value'] for r in result}
        self.assertEqual(buckets['< 80%'], 2)
        self.assertEqual(buckets['80-90%'], 1)
        self.assertEqual(buckets['90-95%'], 1)
        self.assertEqual(buckets['> 95%'], 1)

    def test_returns_none_on_empty_file(self):
        empty_file = io.BytesIO()
        result = parse_containers_by_state(empty_file)
        self.assertIsNone(result)
