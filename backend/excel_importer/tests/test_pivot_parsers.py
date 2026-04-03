"""
Tests for pivot table parsers.
These tests verify parsing of dynamic ranges from the Excel KPI workbook.
"""
import io
from unittest.mock import patch, MagicMock
from django.test import TestCase
import pandas as pd

# Import the functions under test
from excel_importer.pivot_parsers import (
    parse_seconds_rework,
    parse_cut_qty,
    parse_fabric_defects,
    parse_enganche,
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


class ParseCutQtyTest(TestCase):
    """Tests for parse_cut_qty parser."""

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_cut_qty_parses_thousand_separators(self, mock_load):
        """
        parse_cut_qty should parse values like "4,896" as 4896 (int).
        """
        mock_df = pd.DataFrame({
            'week': [1, 2],
            'cut_qty': ['4,896', '5,231'],
        })
        mock_load.return_value = mock_df

        result = parse_cut_qty(io.BytesIO())

        cut_qty_series = result[0]
        self.assertEqual(cut_qty_series['name'], 'Cut Qty')
        self.assertEqual(cut_qty_series['data'][0]['y'], 4896)
        self.assertEqual(cut_qty_series['data'][1]['y'], 5231)

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_cut_qty_includes_total(self, mock_load):
        """
        parse_cut_qty should include 'Total Resultado' as the last data point.
        """
        mock_df = pd.DataFrame({
            'week': [1, 2, 'Total Resultado'],
            'cut_qty': [1000, 2000, 4896],
        })
        mock_load.return_value = mock_df

        result = parse_cut_qty(io.BytesIO())

        cut_qty_series = result[0]
        data = cut_qty_series['data']
        
        # Last item should be Total Resultado
        self.assertEqual(data[-1]['x'], 'Total Resultado')
        self.assertEqual(data[-1]['y'], 4896)


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


class ParseEngancheTest(TestCase):
    """Tests for parse_enganche parser."""

    @patch('excel_importer.pivot_parsers.load_pivot_range')
    def test_parse_enganche_includes_total(self, mock_load):
        """
        parse_enganche should include 'Total Resultado' as last data point.
        """
        mock_df = pd.DataFrame({
            'week': [1, 2, 'Total Resultado'],
            'enganche': [100, 200, 1234],
        })
        mock_load.return_value = mock_df

        result = parse_enganche(io.BytesIO())

        enganche_series = result[0]
        data = enganche_series['data']
        
        # Last item should be Total Resultado
        self.assertEqual(data[-1]['x'], 'Total Resultado')
        self.assertEqual(data[-1]['y'], 1234)


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
        result = parse_cut_qty(empty_file)
        self.assertIsNone(result)
        
        empty_file.seek(0)
        result = parse_fabric_defects(empty_file)
        self.assertIsNone(result)
        
        empty_file.seek(0)
        result = parse_enganche(empty_file)
        self.assertIsNone(result)
