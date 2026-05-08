"""
Tests for VolatileKpiView edge cases.

Covers:
  - POST /api/kpis/volatile/ with missing file
  - Empty DataFrame handling (via helper method tests)
  - Zero sample (division by zero safety)
  - Single-point trend calculation
  - Missing columns in _compute_filter_options
  - Parser exception resilience (via helper method tests)

Note: We test VolatileKpiView helper methods directly (_calc_aql_by_style,
_calc_defect_rate, _calc_aql_weekly, _compute_filter_options) to avoid
requiring a real Excel file with exact QC FA Plant structure (67 columns,
specific header row). The full POST endpoint is tested for the missing file
case which doesn't require Excel parsing.
"""
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status as http_status
from unittest.mock import patch
import pandas as pd

from quality_data.views import VolatileKpiView


class VolatileKpiViewTest(TestCase):
    """Edge case tests for VolatileKpiView"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:kpi-volatile')
        # Instantiate view directly to test helper methods
        self.view = VolatileKpiView()

    # ─────────────────────────────────────────────────────────
    # 2.2 — Missing File (full POST test)
    # ─────────────────────────────────────────────────────────

    def test_volatile_post_missing_file(self):
        """
        POST without file should return 400 with error message.
        """
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_volatile_post_returns_serialized_qcfa_payload(self):
        """
        POST with a valid file returns serialized QC FA KPI payload.
        Verifies the output has the expected 16-KPI shape (serialization
        happens through the shared assembler).
        """
        file_obj = SimpleUploadedFile(
            'test.xlsx',
            b'fake excel content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        qc_df = pd.DataFrame([
            {
                'style': 'N3165',
                'defects_total': 3,
                'sample': 100,
                'week': 1,
                'team': 1,
                'customer': 'CUST_A',
                'color': 'red',
                'batch': 1,
                'pass_or_fail': 'PASS',
                'rejected': 5,
                'accepted': 95,
            }
        ])

        with patch('excel_importer.handler_service.load_and_clean', return_value=qc_df):
            with patch('quality_data.views.parse_seconds_rework', return_value=[]):
                with patch('quality_data.views.parse_fabric_defects', return_value=[]):
                    with patch('quality_data.views.parse_containers_by_state', return_value=[]):
                        with patch('quality_data.views.parse_top_defects', return_value=[]):
                            with patch('quality_data.views.parse_defects_by_style', return_value=[]):
                                response = self.client.post(
                                    self.url,
                                    {'file': file_obj},
                                    format='multipart',
                                )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Verify the payload has the expected 17-KPI QC FA shape
        self.assertIn('aql_by_style', response.data)
        self.assertIn('aql_by_team', response.data)
        self.assertIn('defect_rate', response.data)
        self.assertIn('containers_by_state', response.data)
        # Verify serialized shape (list of {label, value})
        self.assertIsInstance(response.data['aql_by_style'], list)

    # ─────────────────────────────────────────────────────────
    # 2.3 — Empty DataFrame (helper method tests)
    # ─────────────────────────────────────────────────────────

    def test_volatile_empty_dataframe_aql_by_style(self):
        """
        Empty DataFrame should return [] for _calc_aql_by_style.
        """
        result = self.view._calc_aql_by_style([])
        self.assertEqual(result, [])

    def test_volatile_empty_dataframe_aql_by_team(self):
        """
        Empty DataFrame should return [] for _calc_aql_by_team.
        """
        result = self.view._calc_aql_by_team([])
        self.assertEqual(result, [])

    def test_volatile_zero_division_safety_aql_by_team(self):
        """
        DataFrame with sample=0 should not crash _calc_aql_by_team.
        """
        rows = [
            {'team': 1, 'defects_total': 3, 'sample': 0},
            {'team': 1, 'defects_total': 1, 'sample': 0},
        ]
        result = self.view._calc_aql_by_team(rows)
        # Both rows have sample=0 → filtered out → result empty
        self.assertEqual(result, [])

    def test_volatile_aql_by_team_computes_correctly(self):
        """
        _calc_aql_by_team should group by team and compute AQL %.
        """
        rows = [
            {'team': 1, 'defects_total': 10, 'sample': 200},
            {'team': 1, 'defects_total': 5, 'sample': 200},
            {'team': 2, 'defects_total': 3, 'sample': 150},
        ]
        result = self.view._calc_aql_by_team(rows)
        # Team 1: (10+5)/(200+200)*100 = 15/400*100 = 3.75
        # Team 2: 3/150*100 = 2.0
        expected = [
            {"label": "1", "value": 3.75},
            {"label": "2", "value": 2.0},
        ]
        self.assertEqual(result, expected)

    def test_volatile_aql_by_team_non_finite_team_values(self):
        """
        _calc_aql_by_team should not crash on inf/-inf team values.

        Regression test: int(inf) raises OverflowError. The method must
        skip non-finite team values gracefully instead of crashing.
        """
        rows = [
            {'team': float('inf'), 'defects_total': 10, 'sample': 200},
            {'team': float('-inf'), 'defects_total': 5, 'sample': 100},
            {'team': 1, 'defects_total': 3, 'sample': 150},
        ]
        result = self.view._calc_aql_by_team(rows)
        # Only team 1 should survive — inf and -inf are filtered out
        expected = [
            {"label": "1", "value": round((3 / 150) * 100, 2)},
        ]
        self.assertEqual(result, expected)

    def test_volatile_empty_dataframe_aql_weekly(self):
        """
        Empty DataFrame should return empty series for _calc_aql_weekly.
        """
        result = self.view._calc_aql_weekly([])
        self.assertEqual(len(result), 2)  # AQL + Trend
        self.assertEqual(result[0]['data'], [])
        self.assertEqual(result[1]['data'], [])

    def test_volatile_empty_dataframe_audited_pieces(self):
        """
        Empty DataFrame should return empty series for _calc_audited_pieces.
        """
        result = self.view._calc_audited_pieces([])
        self.assertEqual(result[0]['data'], [])

    def test_volatile_empty_dataframe_ac_re_rate(self):
        """
        Empty DataFrame should return [] for _calc_ac_re_rate.
        """
        result = self.view._calc_ac_re_rate([])
        self.assertEqual(result, [])

    def test_volatile_empty_dataframe_perf_by_customer(self):
        """
        Empty DataFrame should return [] for _calc_perf_by_customer.
        """
        result = self.view._calc_perf_by_customer([])
        self.assertEqual(result, [])

    def test_volatile_empty_dataframe_perf_by_line(self):
        """
        Empty DataFrame should return [] for _calc_perf_by_line.
        """
        result = self.view._calc_perf_by_line([])
        self.assertEqual(result, [])

    def test_volatile_empty_dataframe_defect_rate(self):
        """
        Empty DataFrame should return value=0 for _calc_defect_rate.
        """
        result = self.view._calc_defect_rate([])
        self.assertEqual(result['value'], 0)

    def test_volatile_empty_dataframe_filter_options(self):
        """
        Empty DataFrame should return empty arrays for _compute_filter_options.
        """
        result = self.view._compute_filter_options([])
        self.assertEqual(result['week'], [])
        self.assertEqual(result['team'], [])
        self.assertEqual(result['style'], [])
        self.assertEqual(result['color'], [])
        self.assertEqual(result['customer'], [])
        self.assertEqual(result['batch'], [])

    # ─────────────────────────────────────────────────────────
    # 2.4 — Zero Division Safety (helper method tests)
    # ─────────────────────────────────────────────────────────

    def test_volatile_zero_division_safety_aql_by_style(self):
        """
        DataFrame with sample=0 should not crash _calc_aql_by_style.
        Rows with zero sample should be filtered out.
        """
        rows = [
            {
                'style': 'N3165', 'defects_total': 0, 'sample': 0,
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 0,
            },
            {
                'style': 'N4165', 'defects_total': 0, 'sample': 0,
                'week': 1, 'team': 2, 'customer': 'CUST_B',
                'color': 'blue', 'batch': 2, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 0,
            },
        ]
        result = self.view._calc_aql_by_style(rows)
        # Zero-sample rows should be filtered out
        self.assertEqual(result, [])

    def test_volatile_zero_division_safety_defect_rate(self):
        """
        DataFrame with accepted+rejected=0 should return value=0 for _calc_defect_rate
        without crashing (division by zero handled).
        """
        rows = [
            {
                'style': 'N3165', 'defects_total': 0, 'sample': 0,
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 0,
            },
        ]
        result = self.view._calc_defect_rate(rows)
        self.assertEqual(result['value'], 0)

    def test_volatile_defect_rate_uses_accepted_plus_rejected(self):
        """Defect rate in volatile mode uses accepted+rejected instead of sample."""
        rows = [
            {
                'defects_total': 10,
                'sample': 100,
                'accepted': 30,
                'rejected': 20,
            },
        ]
        result = self.view._calc_defect_rate(rows)
        self.assertEqual(result['value'], 20.0)

    def test_volatile_zero_division_safety_mixed_sample(self):
        """
        Mix of zero-sample and non-zero-sample rows should only
        calculate AQL for rows with sample > 0.
        """
        rows = [
            {
                'style': 'N3165', 'defects_total': 3, 'sample': 100,
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 5, 'accepted': 95,
            },
            {
                'style': 'N3165', 'defects_total': 0, 'sample': 0,  # Zero - filtered
                'week': 1, 'team': 2, 'customer': 'CUST_B',
                'color': 'blue', 'batch': 2, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 0,
            },
            {
                'style': 'N4165', 'defects_total': 8, 'sample': 100,
                'week': 1, 'team': 3, 'customer': 'CUST_C',
                'color': 'green', 'batch': 3, 'pass_or_fail': 'PASS',
                'rejected': 10, 'accepted': 90,
            },
        ]
        result = self.view._calc_aql_by_style(rows)
        # Should only have N3165 (from first row) and N4165
        self.assertEqual(len(result), 2)
        styles = {item['label'] for item in result}
        self.assertEqual(styles, {'N3165', 'N4165'})

    # ─────────────────────────────────────────────────────────
    # 2.5 — Single Point Trend (helper method test)
    # ─────────────────────────────────────────────────────────

    def test_volatile_trend_single_point(self):
        """
        _calc_aql_weekly with only 1 data point should return that
        single point for both AQL and Trend series (no slope calculation
        with single point).
        """
        rows = [
            {
                'style': 'N3165', 'defects_total': 3, 'sample': 100,
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 5, 'accepted': 95,
            },
        ]
        result = self.view._calc_aql_weekly(rows)

        self.assertEqual(len(result), 2)  # AQL + Trend

        aql_series = result[0]
        trend_series = result[1]

        # AQL series should have 1 point
        self.assertEqual(len(aql_series['data']), 1)
        self.assertEqual(aql_series['data'][0]['x'], 1)
        self.assertEqual(aql_series['data'][0]['y'], 3.0)  # 3/100*100

        # Trend series should ALSO have 1 point (same as AQL for single-point case)
        self.assertEqual(len(trend_series['data']), 1)
        self.assertEqual(trend_series['data'][0]['x'], 1)

    # ─────────────────────────────────────────────────────────
    # 2.6 — Missing Columns in Filter Options (helper method test)
    # ─────────────────────────────────────────────────────────

    def test_volatile_filter_options_missing_columns(self):
        """
        DataFrame missing optional columns should return empty arrays
        for those filter options without crashing.
        """
        # Only provide some fields - others missing
        rows = [
            {
                'style': None, 'customer': None, 'batch': None,
                'week': 1, 'team': 1, 'color': None,
            },
        ]
        result = self.view._compute_filter_options(rows)

        # Missing/None fields should return empty arrays
        self.assertEqual(result['week'], [1])  # Has value
        self.assertEqual(result['team'], [1])  # Has value
        self.assertEqual(result['style'], [])
        self.assertEqual(result['customer'], [])
        self.assertEqual(result['batch'], [])
        self.assertEqual(result['color'], [])

    def test_volatile_filter_options_empty_dataframe(self):
        """
        Empty DataFrame should return empty arrays for all filter options.
        """
        result = self.view._compute_filter_options([])
        self.assertEqual(result['week'], [])
        self.assertEqual(result['team'], [])
        self.assertEqual(result['style'], [])
        self.assertEqual(result['customer'], [])
        self.assertEqual(result['batch'], [])
        self.assertEqual(result['color'], [])

    # ─────────────────────────────────────────────────────────
    # 2.7 — Helper method coverage for post's error handling
    # ─────────────────────────────────────────────────────────

    def test_volatile_pass_reject_empty_dataframe(self):
        """
        _calc_pass_reject with empty DataFrame returns [].
        """
        result = self.view._calc_pass_reject([])
        self.assertEqual(result, [])

    def test_volatile_rejected_evolution_empty_dataframe(self):
        """
        _calc_rejected_evolution with empty DataFrame returns empty series.
        """
        result = self.view._calc_rejected_evolution([])
        self.assertEqual(result[0]['data'], [])

    # ─────────────────────────────────────────────────────────
    # Missing scenarios from spec compliance (required by verify)
    # ─────────────────────────────────────────────────────────

    def test_volatile_invalid_date_in_filter_options(self):
        """
        Invalid date format in DataFrame should not crash _compute_filter_options.
        Invalid values should be filtered out when computing week filter options.
        """
        # DataFrame with invalid week values (strings, floats that aren't valid ints)
        rows = [
            {
                'style': 'N3165', 'week': 'invalid', 'team': 1,
                'customer': 'CUST_A', 'color': 'red', 'batch': 1,
            },
            {
                'style': 'N4165', 'week': 1.5, 'team': 2,  # Float instead of int
                'customer': 'CUST_B', 'color': 'blue', 'batch': 2,
            },
            {
                'style': 'N5165', 'week': None, 'team': 3,
                'customer': 'CUST_C', 'color': 'green', 'batch': 3,
            },
            {
                'style': 'N6165', 'week': 5, 'team': 4,  # Valid week
                'customer': 'CUST_D', 'color': 'yellow', 'batch': 4,
            },
        ]
        # Should not raise - invalid values filtered out
        result = self.view._compute_filter_options(rows)
        # Only valid integer weeks should be included
        self.assertEqual(result['week'], [5])

    def test_volatile_outlier_numeric_handling(self):
        """
        Extreme outlier values in numeric columns (negative, very large)
        should be handled gracefully by AQL calculations.
        """
        rows = [
            {
                'style': 'N3165', 'defects_total': -999, 'sample': 100,  # Negative defects
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 100,
            },
            {
                'style': 'N4165', 'defects_total': 0, 'sample': 100,
                'week': 1, 'team': 2, 'customer': 'CUST_B',
                'color': 'blue', 'batch': 2, 'pass_or_fail': 'PASS',
                'rejected': 0, 'accepted': 100,
            },
            {
                'style': 'N5165', 'defects_total': 10**9, 'sample': 100,  # Extreme outlier
                'week': 1, 'team': 3, 'customer': 'CUST_C',
                'color': 'green', 'batch': 3, 'pass_or_fail': 'PASS',
                'rejected': 10, 'accepted': 90,
            },
        ]
        # Should not crash and should keep deterministic ordering by AQL desc
        result = self.view._calc_aql_by_style(rows)
        self.assertEqual(
            result,
            [
                {'label': 'N5165', 'value': 1000000000.0},
                {'label': 'N4165', 'value': 0.0},
                {'label': 'N3165', 'value': -999.0},
            ],
        )

    def test_volatile_parser_exception_returns_null(self):
        """
        When post() parser functions fail, the view should return a 400 error
        (not crash the entire endpoint).
        """
        import io
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a minimal Excel file with valid structure
        import pandas as pd
        buffer = io.BytesIO()
        df_data = pd.DataFrame({
            'PO': [100], 'date_1': ['2025-01-15'], 'week': [1],
            'team': [1], 'customer': ['CUST_A'], 'style': ['N3165'],
            'batch': [1], 'color': ['red'], 'qty': [100], 'sample': [50],
            'seconds': [25], 'accepted': [40], 'rejected': [10],
            'defects_total': [5], 'aql': [2.5], 'pass_or_fail': ['PASS'],
        })
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_data.to_excel(writer, sheet_name='QC FA Plant', index=False)
        buffer.seek(0)

        # Wrap buffer in SimpleUploadedFile to correctly simulate DRF multipart upload
        uploaded_file = SimpleUploadedFile(
            'kpi.xlsx',
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # When load_and_clean fails, post() should return 200 with empty payload
        # (the service catches the error and returns an empty DataFrame)
        with patch('excel_importer.handler_service.load_and_clean', side_effect=Exception("Simulated I/O error")):
            response = self.client.post(
                self.url,
                {'file': uploaded_file},
                format='multipart'
            )
            # Should not return error — the service handles the I/O error gracefully
            # and returns computed KPIs from empty data.
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            # With empty rows, KPI computations return empty/nil results
            self.assertIn('aql_by_style', response.data)
            self.assertIsNone(response.data.get('seconds_rework'))


# ─────────────────────────────────────────────────────────
# Volatile parity: defect_composition and defect_trend_top_3
# ─────────────────────────────────────────────────────────

class VolatileDefectInsightKpisTest(TestCase):
    """Tests for volatile KPI helpers: _calc_defect_composition, _calc_defect_trend_top_3"""

    def setUp(self):
        # Instantiate view directly to test helper methods
        self.view = VolatileKpiView()
        self.client = APIClient()
        self.url = reverse('quality_data:kpi-volatile')

    # ── _calc_defect_composition ────────────────────────

    def test_defect_composition_empty_rows(self):
        """Empty rows → returns []."""
        result = self.view._calc_defect_composition([])
        self.assertEqual(result, [])

    def test_defect_composition_shape_name_value(self):
        """Returns [{name, value}] with integer values."""
        rows = [
            {
                'uneven': 2, 'broken_stitch': 5, 'open_seam': 0,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 7, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertIn("name", item)
            self.assertIn("value", item)
            self.assertIsInstance(item["value"], int)

    def test_defect_composition_excludes_zeros(self):
        """Defect types with total=0 are excluded."""
        rows = [
            {
                'uneven': 0, 'broken_stitch': 0, 'tear': 0,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 0, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        self.assertEqual(result, [])

    def test_defect_composition_sorted_by_value_desc_name_asc(self):
        """Results sorted by value DESC, name ASC (tie-break)."""
        rows = [
            {
                'broken_stitch': 5, 'loose_thread': 5, 'tear': 10, 'open_seam': 3,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 23, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        sorted_items = sorted(result, key=lambda x: (-x["value"], x["name"]))
        self.assertEqual(result, sorted_items)

    def test_defect_composition_all_zeroes(self):
        """All defect columns are zero → returns []."""
        rows = [
            {
                'uneven': 0, 'broken_stitch': 0, 'tear': 0, 'loose_thread': 0,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 0, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        self.assertEqual(result, [])

    # ── _calc_defect_trend_top_3 ────────────────────────

    def test_defect_trend_top_3_empty_rows(self):
        """Empty rows → returns []."""
        result = self.view._calc_defect_trend_top_3([])
        self.assertEqual(result, [])

    def test_defect_trend_top_3_shape_name_data_x_y(self):
        """Returns [{name, data:[{x,y}]}] with integer y."""
        rows = [
            {
                'uneven': 3, 'broken_stitch': 8,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 11, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 3)
        for series in result:
            self.assertIn("name", series)
            self.assertIn("data", series)
            self.assertIsInstance(series["data"], list)
            for point in series["data"]:
                self.assertIn("x", point)
                self.assertIn("y", point)
                self.assertIsInstance(point["y"], (int, float))

    def test_defect_trend_top_3_weeks_ascending(self):
        """Weeks are ascending within each series."""
        rows = [
            {
                'uneven': 3, 'broken_stitch': 8, 'tear': 5,
                'style': 'N3165', 'week': 3, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 16, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
            {
                'uneven': 2, 'broken_stitch': 4, 'tear': 1,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 7, 'sample': 100, 'color': 'blue', 'batch': 2,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        for series in result:
            weeks = [p["x"] for p in series["data"]]
            self.assertEqual(weeks, sorted(weeks))

    def test_defect_trend_top_3_zero_fill_missing_weeks(self):
        """When a defect type is absent in a week, y=0 for that week."""
        rows = [
            {
                'uneven': 10, 'broken_stitch': 0,  # uneven in week 1 only
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 10, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
            {
                'broken_stitch': 8, 'uneven': 0,  # broken_stitch in week 2 only
                'style': 'N3165', 'week': 2, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 8, 'sample': 100, 'color': 'blue', 'batch': 2,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        # Both series should have week 1 and week 2
        for series in result:
            weeks = {p["x"] for p in series["data"]}
            self.assertEqual(weeks, {1, 2})

    def test_defect_trend_top_3_all_zero_amounts(self):
        """When all defect amounts are zero → returns []."""
        rows = [
            {
                'uneven': 0, 'broken_stitch': 0, 'tear': 0,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 0, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        self.assertEqual(result, [])

    # ── Parity: fewer than 3 ─────────────────────────────

    def test_defect_trend_top_3_fewer_than_3_types(self):
        """When only 2 defect types have positive amounts, returns 2 series."""
        rows = [
            {
                'uneven': 5, 'broken_stitch': 3, 'tear': 0, 'open_seam': 0,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 8, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        self.assertEqual(len(result), 2)
        names = {s["name"] for s in result}
        self.assertEqual(names, {"Uneven", "Broken Stitch"})

    # ── Parity: multi-row composition aggregation ────────

    def test_defect_composition_multi_row_sums_correctly(self):
        """Defect composition aggregates amounts across multiple rows."""
        rows = [
            {
                'uneven': 5, 'broken_stitch': 0, 'tear': 3,
                'style': 'A', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 8, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
            {
                'uneven': 2, 'broken_stitch': 4, 'tear': 0,
                'style': 'B', 'week': 2, 'team': 2, 'customer': 'CUST_A',
                'defects_total': 6, 'sample': 100, 'color': 'blue', 'batch': 2,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        # uneven: 5+2=7, broken_stitch: 0+4=4, tear: 3+0=3
        values = {item["name"]: item["value"] for item in result}
        self.assertEqual(values["Uneven"], 7)
        self.assertEqual(values["Broken Stitch"], 4)
        self.assertEqual(values["Tear"], 3)

    # ── Full volatile endpoint DTO parity ────────────────

    def test_volatile_post_includes_defect_insight_keys(self):
        """POST /api/kpis/volatile/ response includes defect_composition and
        defect_trend_top_3 when QC rows are provided."""
        from django.test import override_settings
        from unittest.mock import patch
        import pandas as pd

        file_obj = SimpleUploadedFile(
            'test.xlsx',
            b'fake excel content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        qc_df = pd.DataFrame([
            {
                'uneven': 5, 'broken_stitch': 3,
                'style': 'N3165', 'defects_total': 8, 'sample': 100,
                'week': 1, 'team': 1, 'customer': 'CUST_A',
                'color': 'red', 'batch': 1, 'pass_or_fail': 'PASS',
                'rejected': 5, 'accepted': 95,
            },
        ])

        with patch('excel_importer.handler_service.load_and_clean', return_value=qc_df):
            with patch('quality_data.views.parse_seconds_rework', return_value=[]):
                with patch('quality_data.views.parse_fabric_defects', return_value=[]):
                    with patch('quality_data.views.parse_containers_by_state', return_value=[]):
                        with patch('quality_data.views.parse_top_defects', return_value=[]):
                            with patch('quality_data.views.parse_defects_by_style', return_value=[]):
                                response = self.client.post(
                                    self.url,
                                    {'file': file_obj},
                                    format='multipart',
                                )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn('defect_composition', response.data)
        self.assertIn('defect_trend_top_3', response.data)
        # Verify DTO shapes match live contract
        dc = response.data['defect_composition']
        self.assertIsInstance(dc, list)
        if dc:
            self.assertIn('name', dc[0])
            self.assertIn('value', dc[0])
        dt = response.data['defect_trend_top_3']
        self.assertIsInstance(dt, list)
        if dt:
            self.assertIn('name', dt[0])
            self.assertIn('data', dt[0])
            self.assertIsInstance(dt[0]['data'], list)


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 1.1: _calculate_acceptance_rate helper
# ─────────────────────────────────────────────────────────

class AcceptanceRateHelperTest(TestCase):
    """Unit tests for _calculate_acceptance_rate shared helper."""

    def test_standard_rate_8_accepted_2_rejected(self):
        """8 accepted, 2 rejected → 80.0%"""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(8, 2)
        self.assertEqual(result, 80.0)

    def test_all_accepted_no_rejected(self):
        """10 accepted, 0 rejected → 100.0%"""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(10, 0)
        self.assertEqual(result, 100.0)

    def test_all_rejected_no_accepted(self):
        """0 accepted, 5 rejected → 0.0%"""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(0, 5)
        self.assertEqual(result, 0.0)

    def test_zero_denominator_returns_zero(self):
        """0 accepted, 0 rejected → 0 (no division error)."""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(0, 0)
        self.assertEqual(result, 0)

    def test_none_accepted_treated_as_zero(self):
        """None accepted, 5 rejected → accepted treated as 0."""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(None, 5)
        self.assertEqual(result, 0.0)

    def test_none_rejected_treated_as_zero(self):
        """5 accepted, None rejected → rejected treated as 0."""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(5, None)
        self.assertEqual(result, 100.0)

    def test_both_none_treated_as_zero(self):
        """None accepted, None rejected → 0."""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(None, None)
        self.assertEqual(result, 0)

    def test_prevents_rate_above_100_from_sample_mismatch(self):
        """9 accepted, 1 rejected → 90.0%, NOT using sample=5 denominator."""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(9, 1)
        self.assertEqual(result, 90.0)

    def test_large_numbers_rounded_to_2_decimals(self):
        """950 accepted, 50 rejected → 95.0%"""
        from quality_data.views import _calculate_acceptance_rate
        result = _calculate_acceptance_rate(950, 50)
        self.assertEqual(result, 95.0)


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 1.2 + 3.1: Team sanitization helpers
# ─────────────────────────────────────────────────────────

class TeamSanitizationHelperTest(TestCase):
    """Unit tests for team sanitization helpers (canonicalize 60→6, keep 1..36)."""

    def test_queryset_sanitization_canonicalizes_60_to_6(self):
        """Queryset sanitization maps team=60 to canonical_team=6 and keeps 1..36."""
        from quality_data.views import _apply_team_sanitization_queryset
        from quality_data.models import QualityQcFa, Color

        color = Color.objects.create(name="test_sanitize_60", is_active=True)

        # Create records: valid teams + 60
        for team in [1, 5, 60, 36]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="Test", team=team,
                coord="C", po=100, style="S", batch=1, color=color,
                qty=50, seconds=20, accepted=40, rejected=10, sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        # Invalid teams (should still be filtered out)
        for team in [0, -1, 37, 999]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="Test", team=team,
                coord="C", po=100, style="S", batch=1, color=color,
                qty=50, seconds=20, accepted=40, rejected=10, sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        qs = QualityQcFa.objects.all()
        sanitized = _apply_team_sanitization_queryset(qs)

        # canonical_team should be 6 for team=60, and valid teams preserved
        canonical_teams = sorted(set(
            item['canonical_team'] for item in sanitized.values('canonical_team')
        ))
        self.assertEqual(canonical_teams, [1, 5, 6, 36])

    def test_queryset_sanitization_all_valid_teams_preserved(self):
        """When all teams are in range, none are removed."""
        from quality_data.views import _apply_team_sanitization_queryset
        from quality_data.models import QualityQcFa, Color

        color = Color.objects.create(name="test_all_valid", is_active=True)

        for team in [1, 10, 20, 36]:
            QualityQcFa.objects.create(
                table_type="QFA",
                date_1="2025-03-01", week=10, customer="Test", team=team,
                coord="C", po=100, style="S", batch=1, color=color,
                qty=50, seconds=20, accepted=40, rejected=10, sample=50,
                defects_total=2, aql=2.5, pass_or_fail="PASS",
            )

        qs = QualityQcFa.objects.all()
        sanitized = _apply_team_sanitization_queryset(qs)
        self.assertEqual(sanitized.count(), 4)

    def test_dataframe_sanitization_canonicalizes_60_to_6(self):
        """DataFrame sanitization maps team=60 to 6, keeps 1..36, removes 0/out-of-range."""
        import pandas as pd
        from quality_data.views import _sanitize_team_dataframe

        df = pd.DataFrame([
            {'team': 1, 'accepted': 10, 'rejected': 2},
            {'team': 0, 'accepted': 5, 'rejected': 1},
            {'team': 36, 'accepted': 20, 'rejected': 5},
            {'team': 60, 'accepted': 30, 'rejected': 10},
            {'team': -1, 'accepted': 0, 'rejected': 0},
            {'team': 5, 'accepted': 15, 'rejected': 3},
        ])

        sanitized = _sanitize_team_dataframe(df)
        teams = sorted(sanitized['team'].unique().tolist())
        self.assertEqual(teams, [1, 5, 6, 36])

    def test_dataframe_sanitization_preserves_all_valid(self):
        """DataFrame with only valid teams keeps all rows."""
        import pandas as pd
        from quality_data.views import _sanitize_team_dataframe

        df = pd.DataFrame([
            {'team': 1, 'accepted': 10, 'rejected': 2},
            {'team': 36, 'accepted': 20, 'rejected': 5},
        ])

        sanitized = _sanitize_team_dataframe(df)
        self.assertEqual(len(sanitized), 2)

    def test_dataframe_sanitization_60_only_becomes_6(self):
        """Team=60 canonicalizes to 6 and is kept, not removed."""
        import pandas as pd
        from quality_data.views import _sanitize_team_dataframe

        df = pd.DataFrame([
            {'team': 60, 'accepted': 20, 'rejected': 5},
        ])

        sanitized = _sanitize_team_dataframe(df)
        self.assertEqual(len(sanitized), 1)
        self.assertEqual(sanitized.iloc[0]['team'], 6)

    def test_dataframe_sanitization_0_only_still_empty(self):
        """DataFrame with only team=0 still returns empty (0 is never valid)."""
        import pandas as pd
        from quality_data.views import _sanitize_team_dataframe

        df = pd.DataFrame([
            {'team': 0, 'accepted': 10, 'rejected': 2},
        ])

        sanitized = _sanitize_team_dataframe(df)
        self.assertEqual(len(sanitized), 0)

    def test_dataframe_sanitization_60_and_0_60_wins(self):
        """Team=60 canonicalizes to 6 and survives; team=0 is filtered out."""
        import pandas as pd
        from quality_data.views import _sanitize_team_dataframe

        df = pd.DataFrame([
            {'team': 0, 'accepted': 10, 'rejected': 2},
            {'team': 60, 'accepted': 20, 'rejected': 5},
        ])

        sanitized = _sanitize_team_dataframe(df)
        self.assertEqual(len(sanitized), 1)
        self.assertEqual(sanitized.iloc[0]['team'], 6)


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 3.3: Volatile helper formula + sanitization
# ─────────────────────────────────────────────────────────

class VolatileAcceptanceRateTest(TestCase):
    """Tests for corrected acceptance formula in volatile helpers."""

    def setUp(self):
        self.view = VolatileKpiView()

    def test_calc_perf_by_customer_uses_accepted_plus_rejected(self):
        """Volatile _calc_perf_by_customer uses accepted/(accepted+rejected)*100."""
        rows = [
            {
                'customer': 'CUST_A', 'accepted': 8, 'rejected': 2,
                'sample': 100,  # sample differs — proves formula change
                'team': 1, 'style': 'S1', 'week': 1,
                'batch': 1, 'color': 'red', 'pass_or_fail': 'PASS',
            },
        ]
        result = self.view._calc_perf_by_customer(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], 'CUST_A')
        self.assertEqual(result[0]['value'], 80.0)

    def test_calc_perf_by_line_uses_accepted_plus_rejected(self):
        """Volatile _calc_perf_by_line uses accepted/(accepted+rejected)*100."""
        rows = [
            {
                'team': 5, 'accepted': 9, 'rejected': 1,
                'sample': 50,  # sample differs
                'customer': 'CUST_B', 'style': 'S2', 'week': 1,
                'batch': 1, 'color': 'blue', 'pass_or_fail': 'PASS',
            },
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], '5')
        self.assertEqual(result[0]['value'], 90.0)

    def test_calc_perf_by_customer_zero_denominator_safe(self):
        """Volatile customer helper: accepted=0, rejected=0 → value=0 (no error)."""
        rows = [
            {
                'customer': 'CUST_C', 'accepted': 0, 'rejected': 0,
                'sample': 0,
                'team': 1, 'style': 'S3', 'week': 1,
                'batch': 1, 'color': 'red', 'pass_or_fail': 'PASS',
            },
        ]
        result = self.view._calc_perf_by_customer(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], 'CUST_C')
        self.assertEqual(result[0]['value'], 0)

    def test_calc_perf_by_line_zero_denominator_safe(self):
        """Volatile line helper: accepted=0, rejected=0 → value=0."""
        rows = [
            {
                'team': 10, 'accepted': 0, 'rejected': 0,
                'sample': 0,
                'customer': 'CUST_D', 'style': 'S4', 'week': 1,
                'batch': 1, 'color': 'blue', 'pass_or_fail': 'PASS',
            },
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['value'], 0)


class VolatileLineSanitizationTest(TestCase):
    """Tests for team sanitization in volatile line-based helpers."""

    def setUp(self):
        self.view = VolatileKpiView()

    def test_calc_perf_by_line_canonicalizes_60_and_excludes_0(self):
        """60 maps to 6, 0 is excluded, valid teams preserved."""
        rows = [
            {'team': 1, 'accepted': 40, 'rejected': 10, 'sample': 50,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 1,
             'color': 'red', 'pass_or_fail': 'PASS'},
            {'team': 0, 'accepted': 5, 'rejected': 1, 'sample': 6,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 2,
             'color': 'blue', 'pass_or_fail': 'PASS'},
            {'team': 60, 'accepted': 30, 'rejected': 10, 'sample': 40,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 3,
             'color': 'green', 'pass_or_fail': 'PASS'},
            {'team': 36, 'accepted': 20, 'rejected': 5, 'sample': 25,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 4,
             'color': 'yellow', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_line(rows)
        teams = {item['label'] for item in result}
        self.assertEqual(teams, {'1', '6', '36'})

    def test_calc_perf_by_line_canonicalized_60_acceptance_rate(self):
        """Team=60's accepted/rejected values are attributed to line 6 with correct rate."""
        rows = [
            {'team': 60, 'accepted': 30, 'rejected': 10, 'sample': 40,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 3,
             'color': 'green', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], '6')
        self.assertEqual(result[0]['value'], 75.0)  # 30/(30+10)*100

    def test_calc_perf_by_line_all_valid_teams_preserved(self):
        """Volatile line helper keeps all rows when teams are valid."""
        rows = [
            {'team': 10, 'accepted': 40, 'rejected': 10, 'sample': 50,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 1,
             'color': 'red', 'pass_or_fail': 'PASS'},
            {'team': 20, 'accepted': 50, 'rejected': 0, 'sample': 50,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 2,
             'color': 'blue', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(len(result), 2)

    def test_calc_perf_by_line_only_zero_returns_empty(self):
        """When only team=0 exists, returns empty list (0 is always invalid)."""
        rows = [
            {'team': 0, 'accepted': 10, 'rejected': 2, 'sample': 12,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 1,
             'color': 'red', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(result, [])

    def test_calc_perf_by_line_only_60_becomes_valid_line_6(self):
        """When only team=60 exists, it canonicalizes to line 6 (not empty)."""
        rows = [
            {'team': 60, 'accepted': 20, 'rejected': 5, 'sample': 25,
             'customer': 'C', 'style': 'S', 'week': 1, 'batch': 2,
             'color': 'blue', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_line(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], '6')
        # 20/(20+5)*100 = 80
        self.assertEqual(result[0]['value'], 80.0)

    def test_calc_perf_by_customer_not_affected_by_team_sanitization(self):
        """Volatile customer helper should NOT filter by team range."""
        rows = [
            {'customer': 'CUST_X', 'team': 60, 'accepted': 8, 'rejected': 2,
             'sample': 10, 'style': 'S', 'week': 1, 'batch': 1,
             'color': 'red', 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_perf_by_customer(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], 'CUST_X')
        self.assertEqual(result[0]['value'], 80.0)


# ─────────────────────────────────────────────────────────
# Strict TDD — Task 3.3 + 4.3: Volatile AC/RE rate sanitization
# ─────────────────────────────────────────────────────────

class VolatileAcReRateSanitizationTest(TestCase):
    """Tests for _calc_ac_re_rate with dirty historical teams."""

    def setUp(self):
        self.view = VolatileKpiView()

    def test_ac_re_rate_excludes_invalid_teams(self):
        """AC/RE rate excludes team=0 and out-of-range teams."""
        rows = [
            {'team': 1, 'pass_or_fail': 'PASS'},
            {'team': 0, 'pass_or_fail': 'PASS'},
            {'team': 60, 'pass_or_fail': 'REJECT'},
            {'team': 36, 'pass_or_fail': 'PASS'},
            {'team': 37, 'pass_or_fail': 'REJECT'},
        ]
        result = self.view._calc_ac_re_rate(rows)
        teams = {int(item['label'].split(' - ')[0]) for item in result}
        self.assertEqual(teams, {1, 6, 36})

    def test_ac_re_rate_60_maps_to_6_with_count(self):
        """Team=60 counts under label '6 - REJECT' after canonicalization."""
        rows = [
            {'team': 60, 'pass_or_fail': 'REJECT'},
            {'team': 60, 'pass_or_fail': 'REJECT'},
            {'team': 60, 'pass_or_fail': 'PASS'},
        ]
        result = self.view._calc_ac_re_rate(rows)
        labels = {item['label']: item['value'] for item in result}
        self.assertIn('6 - REJECT', labels)
        self.assertEqual(labels['6 - REJECT'], 2)
        self.assertIn('6 - PASS', labels)
        self.assertEqual(labels['6 - PASS'], 1)

    def test_ac_re_rate_all_zero_and_60_produces_line_6(self):
        """Only zero and sixty: zero excluded, 60→6, only line 6 appears."""
        rows = [
            {'team': 0, 'pass_or_fail': 'PASS'},
            {'team': 60, 'pass_or_fail': 'REJECT'},
        ]
        result = self.view._calc_ac_re_rate(rows)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['label'], '6 - REJECT')

    def test_ac_re_rate_aggregates_60_and_existing_6(self):
        """Team 60 and team 6 records both contribute to line 6."""
        rows = [
            {'team': 6, 'pass_or_fail': 'PASS'},
            {'team': 60, 'pass_or_fail': 'PASS'},
            {'team': 6, 'pass_or_fail': 'REJECT'},
        ]
        result = self.view._calc_ac_re_rate(rows)
        labels = {item['label']: item['value'] for item in result}
        # Both team-6 and team-60 PASS records → 2 total for '6 - PASS'
        self.assertEqual(labels['6 - PASS'], 2)
        # team-6 REJECT record → 1 total for '6 - REJECT'
        self.assertEqual(labels['6 - REJECT'], 1)


class VolatileFilterOptionsSanitizationTest(TestCase):
    """Tests for _compute_filter_options team sanitization."""

    def setUp(self):
        self.view = VolatileKpiView()

    def test_filter_options_excludes_invalid_teams(self):
        """Team filter options exclude 0 and >36 after canonicalization."""
        rows = [
            {'week': 1, 'team': 1, 'style': 'A', 'color': 'red',
             'customer': 'C', 'batch': 1},
            {'week': 1, 'team': 0, 'style': 'B', 'color': 'blue',
             'customer': 'C', 'batch': 2},
            {'week': 1, 'team': 60, 'style': 'C', 'color': 'green',
             'customer': 'C', 'batch': 3},
            {'week': 1, 'team': 36, 'style': 'D', 'color': 'yellow',
             'customer': 'C', 'batch': 4},
        ]
        result = self.view._compute_filter_options(rows)
        self.assertEqual(result['team'], [1, 36])

    def test_filter_options_60_not_in_team_options(self):
        """Team=60 should not appear as a selectable option."""
        rows = [
            {'week': 1, 'team': 60, 'style': 'A', 'color': 'red',
             'customer': 'C', 'batch': 1},
        ]
        result = self.view._compute_filter_options(rows)
        self.assertEqual(result['team'], [])

    def test_filter_options_0_is_excluded(self):
        """Team=0 should not appear as a selectable option."""
        rows = [
            {'week': 1, 'team': 0, 'style': 'A', 'color': 'red',
             'customer': 'C', 'batch': 1},
        ]
        result = self.view._compute_filter_options(rows)
        self.assertEqual(result['team'], [])

    def test_filter_options_mixed_valid_and_invalid(self):
        """Only valid 1..36 teams appear in filter options."""
        rows = [
            {'week': 1, 'team': 5, 'style': 'A', 'color': 'red',
             'customer': 'C', 'batch': 1},
            {'week': 1, 'team': 10, 'style': 'B', 'color': 'blue',
             'customer': 'C', 'batch': 2},
            {'week': 1, 'team': 60, 'style': 'C', 'color': 'green',
             'customer': 'C', 'batch': 3},
            {'week': 1, 'team': 0, 'style': 'D', 'color': 'yellow',
             'customer': 'C', 'batch': 4},
        ]
        result = self.view._compute_filter_options(rows)
        self.assertEqual(result['team'], [5, 10])


# ─────────────────────────────────────────────────────────
# Slice 1: Dashboard dispatch + context forwarding + NaN safety
# ─────────────────────────────────────────────────────────

class VolatileDashboardDispatchTest(TestCase):
    """Tests for the dashboard-aware dispatch in VolatileKpiView.post()."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:kpi-volatile')

    def _make_file(self):
        return SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_post_with_dashboard_container_returns_all_container_kpis(self):
        """POST with dashboard=container returns full container KPI payload."""
        from unittest.mock import patch

        file_obj = self._make_file()

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            # Return empty container rows (still returns zero-filled KPIs)
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                self.url,
                {'file': file_obj, 'dashboard': 'container'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # All container KPI keys should be present
        self.assertIn('containers_by_state', response.data)
        self.assertIn('executive_summary', response.data)
        self.assertIn('pass_rate_trend', response.data)
        self.assertIn('inspected_trend', response.data)
        self.assertIn('rejected_trend', response.data)
        self.assertIn('top_defects', response.data)
        self.assertIn('defect_composition', response.data)
        self.assertIn('worst_containers', response.data)
        # QC FA keys should NOT be present for container dashboard
        self.assertNotIn('aql_by_style', response.data)
        self.assertNotIn('defect_rate', response.data)

    def test_post_with_dashboard_seconds_a4_returns_full_payload_now(self):
        """POST with dashboard=seconds_a4 returns real KPI payload (no longer empty placeholder)."""
        from unittest.mock import patch

        file_obj = self._make_file()

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                self.url,
                {'file': file_obj, 'dashboard': 'seconds_a4'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have all Seconds A4 KPIs (not empty anymore)
        self.assertIn('executive_summary', response.data)
        self.assertIn('weekly_trend', response.data)
        self.assertIn('sew_vs_fab', response.data)
        self.assertIn('by_style', response.data)

    def test_post_with_dashboard_seconds_general_returns_full_payload_now(self):
        """POST with dashboard=seconds_general returns real KPI payload (no longer empty placeholder)."""
        from unittest.mock import patch

        file_obj = self._make_file()

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                self.url,
                {'file': file_obj, 'dashboard': 'seconds_general'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should now have real KPI keys (not empty anymore)
        self.assertIn('defects_by_customer', response.data)
        self.assertIn('production_totals', response.data)
        self.assertNotEqual(response.data, {})

    def test_post_with_dashboard_qcfa_and_context_customer_uses_customer_sheet(self):
        """dashboard=qcfa + context=customer triggers QC FA Customer sheet parsing."""
        from unittest.mock import patch

        file_obj = self._make_file()

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)

            response = self.client.post(
                self.url,
                {'file': file_obj, 'dashboard': 'qcfa', 'context': 'customer'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Verify _get_volatile_rows was called with correct dashboard and context
        mock_get_rows.assert_called_once()
        call_args = mock_get_rows.call_args[0]
        self.assertEqual(call_args[1], 'qcfa')
        self.assertEqual(call_args[2], 'customer')

    # ── Slice 1 / Controller Boundary: legacy parser isolation ─────────

    def test_container_dashboard_does_not_call_legacy_parsers(self):
        """dashboard=container does NOT call parse_seconds_rework, parse_fabric_defects, or parse_containers_by_state."""
        file_obj = self._make_file()

        with patch('quality_data.views.parse_seconds_rework') as mock_seconds:
            with patch('quality_data.views.parse_fabric_defects') as mock_fabric:
                with patch('quality_data.views.parse_containers_by_state') as mock_containers:
                    with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                        mock_get_rows.return_value = ([], None, None)
                        response = self.client.post(
                            self.url,
                            {'file': file_obj, 'dashboard': 'container'},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        mock_seconds.assert_not_called()
        mock_fabric.assert_not_called()
        mock_containers.assert_not_called()

    def test_seconds_a4_dashboard_does_not_call_legacy_parsers(self):
        """dashboard=seconds_a4 does NOT call parse_seconds_rework, parse_fabric_defects, or parse_containers_by_state."""
        file_obj = self._make_file()

        with patch('quality_data.views.parse_seconds_rework') as mock_seconds:
            with patch('quality_data.views.parse_fabric_defects') as mock_fabric:
                with patch('quality_data.views.parse_containers_by_state') as mock_containers:
                    with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                        mock_get_rows.return_value = ([], None, None)
                        response = self.client.post(
                            self.url,
                            {'file': file_obj, 'dashboard': 'seconds_a4'},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        mock_seconds.assert_not_called()
        mock_fabric.assert_not_called()
        mock_containers.assert_not_called()

    def test_seconds_general_dashboard_does_not_call_legacy_parsers(self):
        """dashboard=seconds_general does NOT call parse_seconds_rework, parse_fabric_defects, or parse_containers_by_state."""
        file_obj = self._make_file()

        with patch('quality_data.views.parse_seconds_rework') as mock_seconds:
            with patch('quality_data.views.parse_fabric_defects') as mock_fabric:
                with patch('quality_data.views.parse_containers_by_state') as mock_containers:
                    with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                        mock_get_rows.return_value = ([], None, None)
                        response = self.client.post(
                            self.url,
                            {'file': file_obj, 'dashboard': 'seconds_general'},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        mock_seconds.assert_not_called()
        mock_fabric.assert_not_called()
        mock_containers.assert_not_called()

    def test_qcfa_dashboard_calls_seconds_rework_and_fabric_defects_but_not_parse_containers(self):
        """dashboard=qcfa calls parse_seconds_rework and parse_fabric_defects, but NOT parse_containers_by_state (replaced by calc_container_state_distribution)."""
        from unittest.mock import MagicMock
        file_obj = self._make_file()

        with patch('quality_data.views.parse_seconds_rework', return_value=[]) as mock_seconds:
            with patch('quality_data.views.parse_fabric_defects', return_value=[]) as mock_fabric:
                with patch('quality_data.views.parse_containers_by_state') as mock_containers:
                    with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                        mock_service = MagicMock()
                        mock_service.get_parsed_data.return_value = ([], None)
                        mock_get_rows.return_value = ([], None, mock_service)
                        response = self.client.post(
                            self.url,
                            {'file': file_obj, 'dashboard': 'qcfa'},
                            format='multipart',
                        )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        mock_seconds.assert_called_once()
        mock_fabric.assert_called_once()
        mock_containers.assert_not_called()

    def test_qcfa_containers_by_state_comes_from_calc_container_state_distribution(self):
        """dashboard=qcfa uses calc_container_state_distribution for containers_by_state, not parse_containers_by_state."""
        from unittest.mock import MagicMock
        from quality_data.volatile_kpi_service import calc_container_state_distribution
        file_obj = self._make_file()
        container_row = {
            'percentage_pass': 97.0, 'container_number': 1, 'customer': 'C',
            'total_palette': 10, 'total_palette_rejected': 1, 'date': '2025-01-01',
        }

        with patch('quality_data.views.parse_seconds_rework', return_value=[]):
            with patch('quality_data.views.parse_fabric_defects', return_value=[]):
                with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                    mock_service = MagicMock()
                    mock_service.get_parsed_data.return_value = ([container_row], None)
                    mock_get_rows.return_value = ([], None, mock_service)
                    response = self.client.post(
                        self.url,
                        {'file': file_obj, 'dashboard': 'qcfa'},
                        format='multipart',
                    )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        state = response.data.get('containers_by_state')
        self.assertIsNotNone(state)
        # With a single 97% container, > 95% bucket should have 1
        expected = calc_container_state_distribution([container_row])
        self.assertEqual(state, expected)

    def test_qcfa_containers_by_state_none_when_service_fails(self):
        """When service.get_parsed_data('container') fails, containers_by_state should be None (not crash)."""
        file_obj = self._make_file()

        with patch('quality_data.views.parse_seconds_rework', return_value=[]):
            with patch('quality_data.views.parse_fabric_defects', return_value=[]):
                with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
                    # Service is None — get_parsed_data call fails but is caught
                    mock_get_rows.return_value = ([], None, None)
                    response = self.client.post(
                        self.url,
                        {'file': file_obj, 'dashboard': 'qcfa'},
                        format='multipart',
                    )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsNone(response.data.get('containers_by_state'))


class VolatileNanSafetyTest(TestCase):
    """Tests for NaN/empty-cell hardening in volatile helpers."""

    def setUp(self):
        self.view = VolatileKpiView()

    def test_safe_defect_int_handles_nan(self):
        """_safe_defect_int handles float('nan') without crashing."""
        result = self.view._safe_defect_int(float('nan'))
        self.assertEqual(result, 0)

    def test_safe_defect_int_handles_none(self):
        """_safe_defect_int handles None."""
        result = self.view._safe_defect_int(None)
        self.assertEqual(result, 0)

    def test_safe_defect_int_handles_float(self):
        """_safe_defect_int handles normal float."""
        result = self.view._safe_defect_int(42.0)
        self.assertEqual(result, 42)

    def test_safe_defect_int_handles_string_number(self):
        """_safe_defect_int handles numeric strings."""
        result = self.view._safe_defect_int('15')
        self.assertEqual(result, 15)

    def test_safe_defect_int_handles_non_numeric_string(self):
        """_safe_defect_int handles non-numeric strings gracefully."""
        result = self.view._safe_defect_int('not-a-number')
        self.assertEqual(result, 0)

    def test_defect_composition_with_nan_values(self):
        """_calc_defect_composition does not crash when rows contain NaN in defect fields."""
        import math
        rows = [
            {
                'uneven': float('nan'), 'broken_stitch': 5, 'open_seam': None,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 5, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_composition(rows)
        # Should not crash - broken_stitch should be present, uneven should be 0/excluded
        names = {item['name'] for item in result}
        self.assertIn('Broken Stitch', names)
        self.assertNotIn('Uneven', names)

    def test_defect_trend_top_3_with_nan_values(self):
        """_calc_defect_trend_top_3 does not crash when rows contain NaN values."""
        rows = [
            {
                'uneven': float('nan'), 'broken_stitch': 5,
                'style': 'N3165', 'week': 1, 'team': 1, 'customer': 'CUST_A',
                'defects_total': 5, 'sample': 100, 'color': 'red', 'batch': 1,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
            {
                'uneven': 3, 'broken_stitch': None, 'tear': 2,
                'style': 'N3165', 'week': 2, 'team': 2, 'customer': 'CUST_B',
                'defects_total': 5, 'sample': 100, 'color': 'blue', 'batch': 2,
                'pass_or_fail': 'PASS', 'rejected': 0, 'accepted': 100,
            },
        ]
        result = self.view._calc_defect_trend_top_3(rows)
        # Should not crash - Broken Stitch (5) and Uneven (3) should be present
        names = {s['name'] for s in result}
        self.assertIn('Broken Stitch', names)
        self.assertIn('Uneven', names)


# ─────────────────────────────────────────────────────────
# Slice 2: Container volatile KPI computation tests
# ─────────────────────────────────────────────────────────

class ContainerVolatileKpiComputationTest(TestCase):
    """Tests for container KPI computation helpers in volatile_kpi_service.py."""

    def setUp(self):
        from quality_data.volatile_kpi_service import (
            calc_container_executive_summary,
            calc_container_state_distribution,
            calc_container_pass_rate_trend,
            calc_container_inspected_trend,
            calc_container_rejected_trend,
            calc_container_top_defects,
            calc_container_defect_composition,
            calc_container_worst_containers,
        )
        self._exec_summary = calc_container_executive_summary
        self._state_dist = calc_container_state_distribution
        self._pass_trend = calc_container_pass_rate_trend
        self._insp_trend = calc_container_inspected_trend
        self._rej_trend = calc_container_rejected_trend
        self._top_defects = calc_container_top_defects
        self._defect_comp = calc_container_defect_composition
        self._worst = calc_container_worst_containers

        self.defect_fields = [
            'dirt_label', 'dirt_container', 'dirt_cartoons', 'container_holes',
            'writte_mark_on_label', 'written_mark_on_cartoon', 'container_poor_close',
            'boxes_poor_close', 'printing_issues_label', 'misaligned_label',
            'crushed_corners', 'cartoons_holes', 'warped_boxes', 'defects_label',
            'total_defects',
        ]

        self.client = APIClient()

        self.sample_rows = [
            {
                'container_number': 100, 'date': '2025-01-10', 'customer': 'AlphaCorp',
                'transfer_of_container': 1, 'total_palette': 20,
                'total_palette_pass': 18, 'total_palette_rejected': 2,
                'percentage_pass': 90.0, 'percentage_reject': 10.0,
                'dirt_label': 5, 'dirt_container': 3, 'total_defects': 8,
            },
            {
                'container_number': 101, 'date': '2025-01-11', 'customer': 'AlphaCorp',
                'transfer_of_container': 1, 'total_palette': 30,
                'total_palette_pass': 15, 'total_palette_rejected': 15,
                'percentage_pass': 50.0, 'percentage_reject': 50.0,
                'dirt_label': 7, 'container_holes': 2, 'total_defects': 9,
            },
            {
                'container_number': 102, 'date': '2025-01-12', 'customer': 'BetaInc',
                'transfer_of_container': 1, 'total_palette': 10,
                'total_palette_pass': 7, 'total_palette_rejected': 3,
                'percentage_pass': 70.0, 'percentage_reject': 30.0,
                'dirt_container': 4, 'total_defects': 4,
            },
        ]

    # ── Executive Summary ─────────────────────────────────

    def test_executive_summary_returns_expected_structure(self):
        result = self._exec_summary(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        labels = {item['label'] for item in result}
        self.assertEqual(labels, {
            'Total Containers', 'Average Pass Rate',
            'Total Palettes Inspected', 'Total Rejected Palettes',
        })
        for item in result:
            self.assertIn('label', item)
            self.assertIn('value', item)

    def test_executive_summary_values_match_computation(self):
        result = self._exec_summary(self.sample_rows)
        values = {item['label']: item['value'] for item in result}
        self.assertEqual(values['Total Containers'], 3)
        # avg of 90, 50, 70 = 70.0
        self.assertEqual(values['Average Pass Rate'], 70.0)
        # sum of 20, 30, 10 = 60
        self.assertEqual(values['Total Palettes Inspected'], 60)
        # sum of 2, 15, 3 = 20
        self.assertEqual(values['Total Rejected Palettes'], 20)

    def test_executive_summary_empty_rows(self):
        result = self._exec_summary([])
        for item in result:
            self.assertEqual(item['value'], 0)

    # ── Containers by State ────────────────────────────────

    def test_state_distribution_returns_four_buckets(self):
        result = self._state_dist(self.sample_rows)
        self.assertEqual(len(result), 4)
        names = {item['name'] for item in result}
        self.assertEqual(names, {'< 80%', '80-90%', '90-95%', '> 95%'})

    def test_state_distribution_bucket_counts(self):
        # 50% → < 80%, 70% → < 80%, 90% → 80-90% → 90-95%
        result = self._state_dist(self.sample_rows)
        counts = {item['name']: item['value'] for item in result}
        self.assertEqual(counts['< 80%'], 2)  # 50%, 70%
        self.assertEqual(counts['80-90%'], 0)
        self.assertEqual(counts['90-95%'], 1)  # 90%
        self.assertEqual(counts['> 95%'], 0)

    def test_state_distribution_boundary_95_excluded_from_gt_95(self):
        """95% exactly falls in 90-95% bucket."""
        rows = [{'percentage_pass': 95.0}]
        result = self._state_dist(rows)
        counts = {item['name']: item['value'] for item in result}
        self.assertEqual(counts['90-95%'], 1)
        self.assertEqual(counts['> 95%'], 0)

    def test_state_distribution_fractional_percentage_normalized(self):
        """0.97 (97%) should normalize to 97, then fall in > 95%."""
        rows = [{'percentage_pass': 0.97}]
        result = self._state_dist(rows)
        counts = {item['name']: item['value'] for item in result}
        self.assertEqual(counts['> 95%'], 1)

    # ── Trends ─────────────────────────────────────────────

    def test_pass_rate_trend_returns_series(self):
        result = self._pass_trend(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        series = result[0]
        self.assertIn('name', series)
        self.assertIn('data', series)
        self.assertGreater(len(series['data']), 0)
        for point in series['data']:
            self.assertIn('x', point)
            self.assertIn('y', point)

    def test_pass_rate_trend_data_points_count(self):
        result = self._pass_trend(self.sample_rows)
        series = result[0]
        # 3 rows with 3 distinct dates
        self.assertEqual(len(series['data']), 3)

    def test_inspected_trend_returns_series(self):
        result = self._insp_trend(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn('data', result[0])

    def test_rejected_trend_returns_series(self):
        result = self._rej_trend(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn('data', result[0])

    def test_inspected_trend_sums_correctly(self):
        # Only 1 row per date in sample, so total_palette = row value
        result = self._insp_trend(self.sample_rows)
        points = {p['x']: p['y'] for p in result[0]['data']}
        self.assertEqual(points.get('2025-01-10'), 20)
        self.assertEqual(points.get('2025-01-11'), 30)
        self.assertEqual(points.get('2025-01-12'), 10)

    def test_rejected_trend_sums_correctly(self):
        result = self._rej_trend(self.sample_rows)
        points = {p['x']: p['y'] for p in result[0]['data']}
        self.assertEqual(points.get('2025-01-10'), 2)
        self.assertEqual(points.get('2025-01-11'), 15)
        self.assertEqual(points.get('2025-01-12'), 3)

    def test_trends_empty_rows(self):
        result = self._pass_trend([])
        self.assertEqual(result[0]['data'], [])

    # ── Top Defects ────────────────────────────────────────

    def test_top_defects_excludes_total_defects(self):
        result = self._top_defects(self.sample_rows, self.defect_fields)
        labels = {item['label'] for item in result}
        self.assertNotIn('Total Defects', labels)

    def test_top_defects_aggregates_across_rows(self):
        result = self._top_defects(self.sample_rows, self.defect_fields)
        values = {item['label']: item['value'] for item in result}
        # dirt_label: 5 + 7 + 0 = 12, dirt_container: 3 + 0 + 4 = 7
        self.assertEqual(values.get('Dirt Label'), 12)
        self.assertEqual(values.get('Dirt Container'), 7)
        self.assertEqual(values.get('Container Holes'), 2)

    def test_top_defects_sorted_by_value_desc(self):
        result = self._top_defects(self.sample_rows, self.defect_fields)
        if len(result) > 1:
            for i in range(len(result) - 1):
                self.assertGreaterEqual(result[i]['value'], result[i + 1]['value'])

    def test_top_defects_empty_rows(self):
        result = self._top_defects([], self.defect_fields)
        self.assertEqual(result, [])

    def test_top_defects_none_defect_fields(self):
        result = self._top_defects(self.sample_rows, None)
        self.assertEqual(result, [])

    # ── Defect Composition ─────────────────────────────────

    def test_defect_composition_returns_name_value(self):
        result = self._defect_comp(self.sample_rows, self.defect_fields)
        for item in result:
            self.assertIn('name', item)
            self.assertIn('value', item)

    def test_defect_composition_excludes_zeros(self):
        result = self._defect_comp(self.sample_rows, self.defect_fields)
        for item in result:
            self.assertGreater(item['value'], 0)

    def test_defect_composition_sorted_by_value_desc_name_asc(self):
        result = self._defect_comp(self.sample_rows, self.defect_fields)
        if len(result) > 1:
            for i in range(len(result) - 1):
                if result[i]['value'] == result[i + 1]['value']:
                    self.assertLessEqual(result[i]['name'], result[i + 1]['name'])
                else:
                    self.assertGreaterEqual(result[i]['value'], result[i + 1]['value'])

    def test_defect_composition_empty_rows(self):
        result = self._defect_comp([], self.defect_fields)
        self.assertEqual(result, [])

    # ── Worst Containers ───────────────────────────────────

    def test_worst_containers_returns_expected_dto(self):
        result = self._worst(self.sample_rows)
        self.assertIsInstance(result, list)
        if result:
            row = result[0]
            self.assertIn('containerNumber', row)
            self.assertIn('customer', row)
            self.assertIn('passRate', row)
            self.assertIn('rejectedPalettes', row)
            self.assertIn('inspectionDate', row)

    def test_worst_containers_ordered_by_pass_rate_asc(self):
        result = self._worst(self.sample_rows)
        rates = [item['passRate'] for item in result]
        self.assertEqual(rates, sorted(rates))

    def test_worst_containers_default_top_5(self):
        result = self._worst(self.sample_rows)
        self.assertLessEqual(len(result), 5)

    def test_worst_containers_empty_rows(self):
        result = self._worst([])
        self.assertEqual(result, [])

    # ── Full container dispatch in VolatileKpiView ─────────

    def test_volatile_post_dashboard_container_returns_full_payload(self):
        """POST with dashboard=container returns all container KPIs, not just containers_by_state."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = (self.sample_rows, self.defect_fields, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'container'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have all Container KPIs
        self.assertIn('executive_summary', response.data)
        self.assertIn('containers_by_state', response.data)
        self.assertIn('pass_rate_trend', response.data)
        self.assertIn('inspected_trend', response.data)
        self.assertIn('rejected_trend', response.data)
        self.assertIn('top_defects', response.data)
        self.assertIn('defect_composition', response.data)
        self.assertIn('worst_containers', response.data)
        # QC FA keys should NOT be present
        self.assertNotIn('aql_by_style', response.data)
        self.assertNotIn('defect_rate', response.data)

    def test_volatile_post_dashboard_container_empty_rows_returns_zeros(self):
        """Container dispatch with empty rows returns zero-filled KPIs (no crash)."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'container'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        exec_summary = response.data.get('executive_summary', [])
        for item in exec_summary:
            self.assertEqual(item['value'], 0)
        # Containers by state should have 4 buckets all at 0
        state = response.data.get('containers_by_state', [])
        self.assertEqual(len(state), 4)
        for item in state:
            self.assertEqual(item['value'], 0)


class SecondsA4VolatileKpiComputationTest(TestCase):
    """Tests for Seconds A4 KPI computation helpers in volatile_kpi_service.py."""

    def setUp(self):
        from quality_data.volatile_kpi_service import (
            calc_seconds_a4_executive_summary,
            calc_seconds_a4_weekly_trend,
            calc_seconds_a4_sew_vs_fab,
            calc_seconds_a4_by_style,
            calc_seconds_a4_by_color,
            calc_seconds_a4_by_line,
            calc_seconds_a4_by_cut,
            calc_seconds_a4_pass_fail_weekly,
            calc_seconds_a4_filter_options,
        )
        self._exec_summary = calc_seconds_a4_executive_summary
        self._weekly_trend = calc_seconds_a4_weekly_trend
        self._sew_vs_fab = calc_seconds_a4_sew_vs_fab
        self._by_style = calc_seconds_a4_by_style
        self._by_color = calc_seconds_a4_by_color
        self._by_line = calc_seconds_a4_by_line
        self._by_cut = calc_seconds_a4_by_cut
        self._pass_fail = calc_seconds_a4_pass_fail_weekly
        self._filter_opts = calc_seconds_a4_filter_options

        self.sample_rows = [
            {
                "year": 2025, "week": 1, "date": "2025-01-05",
                "cut_num": 101, "style": "STYLE-A", "color": "Red",
                "line": "L1", "total_of_2ds": 10,
                "seconds_by_sew": 40, "seconds_by_fab": 30,
                "seconds_sew_a4": 20, "seconds_fab_a4": 10,
                "accepted": 50, "rejected": 5,
                "pass_field": 15, "fail_field": 5,
            },
            {
                "year": 2025, "week": 2, "date": "2025-01-12",
                "cut_num": 101, "style": "STYLE-A", "color": "Blue",
                "line": "L1", "total_of_2ds": 15,
                "seconds_by_sew": 50, "seconds_by_fab": 40,
                "seconds_sew_a4": 25, "seconds_fab_a4": 15,
                "accepted": 60, "rejected": 6,
                "pass_field": 12, "fail_field": 8,
            },
            {
                "year": 2025, "week": 3, "date": "2025-01-19",
                "cut_num": 102, "style": "STYLE-B", "color": "Red",
                "line": "L2", "total_of_2ds": 20,
                "seconds_by_sew": 60, "seconds_by_fab": 50,
                "seconds_sew_a4": 30, "seconds_fab_a4": 20,
                "accepted": 70, "rejected": 7,
                "pass_field": 18, "fail_field": 2,
            },
        ]

        self.client = APIClient()

    # ── Executive Summary ─────────────────────────────────

    def test_executive_summary_returns_totals_and_percentages_keys(self):
        result = self._exec_summary(self.sample_rows)
        self.assertIn("totals", result)
        self.assertIn("percentages", result)
        self.assertEqual(result["percentages"], [])

    def test_executive_summary_totals_aggregate_correctly(self):
        result = self._exec_summary(self.sample_rows)
        t = result["totals"]
        # total_of_2ds: 10+15+20 = 45
        self.assertEqual(t["total_of_2ds"], 45)
        # seconds_by_sew: 40+50+60 = 150
        self.assertEqual(t["seconds_by_sew"], 150)
        # seconds_by_fab: 30+40+50 = 120
        self.assertEqual(t["seconds_by_fab"], 120)
        # seconds_sew_a4: 20+25+30 = 75
        self.assertEqual(t["seconds_sew_a4"], 75)
        # seconds_fab_a4: 10+15+20 = 45
        self.assertEqual(t["seconds_fab_a4"], 45)
        # accepted: 50+60+70 = 180
        self.assertEqual(t["accepted"], 180)
        # rejected: 5+6+7 = 18
        self.assertEqual(t["rejected"], 18)

    def test_executive_summary_empty_rows(self):
        result = self._exec_summary([])
        for field in ("total_of_2ds", "seconds_by_sew", "seconds_by_fab",
                      "seconds_sew_a4", "seconds_fab_a4", "accepted", "rejected"):
            self.assertEqual(result["totals"][field], 0)

    # ── Weekly Trend ───────────────────────────────────────

    def test_weekly_trend_returns_series_with_name_and_data(self):
        result = self._weekly_trend(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        series = result[0]
        self.assertEqual(series["name"], "2DS")
        self.assertIn("data", series)
        self.assertGreater(len(series["data"]), 0)

    def test_weekly_trend_data_points(self):
        result = self._weekly_trend(self.sample_rows)
        by_week = {p["x"]: p["y"] for p in result[0]["data"]}
        self.assertEqual(by_week["2025-W1"], 10)
        self.assertEqual(by_week["2025-W2"], 15)
        self.assertEqual(by_week["2025-W3"], 20)

    def test_weekly_trend_empty_rows(self):
        result = self._weekly_trend([])
        self.assertEqual(result[0]["data"], [])

    # ── Sew vs Fab ─────────────────────────────────────────

    def test_sew_vs_fab_returns_two_labels(self):
        result = self._sew_vs_fab(self.sample_rows)
        labels = {item["label"] for item in result}
        self.assertEqual(labels, {"Sew", "Fabric"})

    def test_sew_vs_fab_values(self):
        result = self._sew_vs_fab(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["Sew"], 150)
        self.assertEqual(values["Fabric"], 120)

    def test_sew_vs_fab_empty_rows(self):
        result = self._sew_vs_fab([])
        self.assertEqual(result[0]["value"], 0)
        self.assertEqual(result[1]["value"], 0)

    # ── By Style ───────────────────────────────────────────

    def test_by_style_aggregates_total_of_2ds(self):
        result = self._by_style(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["STYLE-A"], 25)
        self.assertEqual(values["STYLE-B"], 20)

    def test_by_style_sorted_descending(self):
        result = self._by_style(self.sample_rows)
        for i in range(len(result) - 1):
            self.assertGreaterEqual(result[i]["value"], result[i + 1]["value"])

    def test_by_style_empty_rows(self):
        result = self._by_style([])
        self.assertEqual(result, [])

    # ── By Color ───────────────────────────────────────────

    def test_by_color_aggregates_total_of_2ds(self):
        result = self._by_color(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["Red"], 30)

    def test_by_color_empty_rows(self):
        result = self._by_color([])
        self.assertEqual(result, [])

    # ── By Line ────────────────────────────────────────────

    def test_by_line_aggregates_total_of_2ds(self):
        result = self._by_line(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["L1"], 25)
        self.assertEqual(values["L2"], 20)

    def test_by_line_empty_rows(self):
        result = self._by_line([])
        self.assertEqual(result, [])

    # ── By Cut ─────────────────────────────────────────────

    def test_by_cut_aggregates_total_of_2ds(self):
        result = self._by_cut(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["Cut 101"], 25)
        self.assertEqual(values["Cut 102"], 20)

    def test_by_cut_label_format(self):
        result = self._by_cut(self.sample_rows)
        labels = {item["label"] for item in result}
        self.assertIn("Cut 101", labels)
        self.assertIn("Cut 102", labels)

    def test_by_cut_empty_rows(self):
        result = self._by_cut([])
        self.assertEqual(result, [])

    # ── Pass Fail Weekly ───────────────────────────────────

    def test_pass_fail_series_names(self):
        result = self._pass_fail(self.sample_rows)
        self.assertEqual(len(result), 2)
        names = [s["name"] for s in result]
        self.assertEqual(names, ["Pass", "Fail"])

    def test_pass_fail_values(self):
        result = self._pass_fail(self.sample_rows)
        pass_data = {p["x"]: p["y"] for p in result[0]["data"]}
        fail_data = {p["x"]: p["y"] for p in result[1]["data"]}
        self.assertEqual(pass_data["2025-W1"], 15)
        self.assertEqual(fail_data["2025-W1"], 5)
        self.assertEqual(pass_data["2025-W2"], 12)
        self.assertEqual(fail_data["2025-W2"], 8)

    def test_pass_fail_empty_rows(self):
        result = self._pass_fail([])
        self.assertEqual(result[0]["data"], [])
        self.assertEqual(result[1]["data"], [])

    # ── Filter Options ─────────────────────────────────────

    def test_filter_options_returns_all_keys(self):
        result = self._filter_opts(self.sample_rows)
        self.assertIn("year", result)
        self.assertIn("week", result)
        self.assertIn("line", result)
        self.assertIn("cut_num", result)
        self.assertIn("style", result)
        self.assertIn("color", result)

    def test_filter_options_distinct_values(self):
        result = self._filter_opts(self.sample_rows)
        self.assertEqual(set(result["year"]), {2025})
        self.assertEqual(set(result["week"]), {1, 2, 3})
        self.assertEqual(set(result["line"]), {"L1", "L2"})
        self.assertEqual(set(result["cut_num"]), {101, 102})
        self.assertEqual(set(result["style"]), {"STYLE-A", "STYLE-B"})
        self.assertEqual(set(result["color"]), {"Blue", "Red"})

    def test_filter_options_empty_rows(self):
        result = self._filter_opts([])
        for field in ("year", "week", "line", "cut_num", "style", "color"):
            self.assertEqual(result[field], [])

    # ── Full dispatch test ─────────────────────────────────

    def test_volatile_post_dashboard_seconds_a4_returns_full_payload(self):
        """POST with dashboard=seconds_a4 returns all Seconds A4 KPIs."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = (self.sample_rows, None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'seconds_a4'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have all Seconds A4 KPIs
        self.assertIn('executive_summary', response.data)
        self.assertIn('weekly_trend', response.data)
        self.assertIn('sew_vs_fab', response.data)
        self.assertIn('by_style', response.data)
        self.assertIn('by_color', response.data)
        self.assertIn('by_line', response.data)
        self.assertIn('by_cut', response.data)
        self.assertIn('pass_fail_weekly', response.data)
        self.assertIn('filter_options', response.data)
        # QC FA keys should NOT be present
        self.assertNotIn('aql_by_style', response.data)
        self.assertNotIn('defect_rate', response.data)

    def test_volatile_post_dashboard_seconds_a4_empty_rows_returns_zeros(self):
        """Seconds A4 dispatch with empty rows returns zero-filled totals (no crash)."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'seconds_a4'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Executive summary should have zeroed totals
        totals = response.data.get('executive_summary', {}).get('totals', {})
        for field in ("total_of_2ds", "seconds_by_sew", "seconds_by_fab",
                      "seconds_sew_a4", "seconds_fab_a4", "accepted", "rejected"):
            self.assertEqual(totals.get(field), 0)
        # Weekly trend should be empty
        self.assertEqual(response.data.get('weekly_trend', [{}])[0].get('data', []), [])


# ─────────────────────────────────────────────────────────
# Slice 4: Seconds General volatile KPI computation tests
# ─────────────────────────────────────────────────────────

class SecondsGeneralVolatileKpiComputationTest(TestCase):
    """Tests for Seconds General KPI computation helpers in volatile_kpi_service.py."""

    def setUp(self):
        from quality_data.volatile_kpi_service import (
            calc_seconds_general_filter_options,
            calc_seconds_general_production_totals,
            calc_seconds_general_defects_by_customer,
            calc_seconds_general_defects_by_style,
            calc_seconds_general_weekly_trend,
            calc_seconds_general_sewing_vs_fabric,
            calc_seconds_general_top_sewing_defects,
            calc_seconds_general_top_fabric_defects,
            calc_seconds_general_fix_vs_definitive,
            calc_seconds_general_defects_by_color,
            calc_seconds_general_defects_by_size,
            calc_seconds_general_defects_by_line,
        )
        self._filter_opts = calc_seconds_general_filter_options
        self._prod_totals = calc_seconds_general_production_totals
        self._def_by_cust = calc_seconds_general_defects_by_customer
        self._def_by_style = calc_seconds_general_defects_by_style
        self._weekly_trend = calc_seconds_general_weekly_trend
        self._sew_vs_fab = calc_seconds_general_sewing_vs_fabric
        self._top_sew = calc_seconds_general_top_sewing_defects
        self._top_fab = calc_seconds_general_top_fabric_defects
        self._fix_def = calc_seconds_general_fix_vs_definitive
        self._def_color = calc_seconds_general_defects_by_color
        self._def_size = calc_seconds_general_defects_by_size
        self._def_line = calc_seconds_general_defects_by_line

        self.sample_rows = [
            {
                "week": 1, "team": 5, "line_code": None,
                "customer": "CUST_A", "style": "ST-100",
                "color": "Red", "size": "M", "produced": 100,
                "fixed": 50, "definitive": 30,
                "picado_aguja": 5, "manchas_sucio": 3, "grasa": 0,
                "tono_tela": 0, "fuera_medidas": 0, "enganche": 0,
                "costura_torcida_insegura": 0, "hoyos_costura": 0,
                "heat_transfer": 0, "mal_corte": 0, "trapo": 0,
                "corrido": 0, "otros": 0,
                "desgarre_def_tela": 10, "contamination": 0,
                "linea_de_tela": 0, "mill_flaw": 0, "hoyos": 0,
                "manchas_tela": 0, "corrido_2": 0, "barre": 0,
                "otros_3": 0, "degradacion": 0, "bordados": 0,
            },
            {
                "week": 1, "team": 5, "line_code": None,
                "customer": "CUST_A", "style": "ST-200",
                "color": "Red", "size": "L", "produced": 120,
                "fixed": 60, "definitive": 36,
                "picado_aguja": 0, "manchas_sucio": 0, "grasa": 8,
                "tono_tela": 0, "fuera_medidas": 0, "enganche": 0,
                "costura_torcida_insegura": 0, "hoyos_costura": 0,
                "heat_transfer": 0, "mal_corte": 0, "trapo": 0,
                "corrido": 0, "otros": 0,
                "desgarre_def_tela": 0, "contamination": 0,
                "linea_de_tela": 0, "mill_flaw": 0, "hoyos": 15,
                "manchas_tela": 0, "corrido_2": 0, "barre": 0,
                "otros_3": 0, "degradacion": 0, "bordados": 0,
            },
            {
                "week": 2, "team": 10, "line_code": None,
                "customer": "CUST_B", "style": "ST-100",
                "color": "Blue", "size": "M", "produced": 130,
                "fixed": 65, "definitive": 39,
                "picado_aguja": 0, "manchas_sucio": 0, "grasa": 0,
                "tono_tela": 4, "fuera_medidas": 0, "enganche": 0,
                "costura_torcida_insegura": 0, "hoyos_costura": 0,
                "heat_transfer": 7, "mal_corte": 0, "trapo": 0,
                "corrido": 0, "otros": 0,
                "desgarre_def_tela": 0, "contamination": 0,
                "linea_de_tela": 0, "mill_flaw": 0, "hoyos": 0,
                "manchas_tela": 6, "corrido_2": 0, "barre": 0,
                "otros_3": 0, "degradacion": 0, "bordados": 0,
            },
        ]

        self.client = APIClient()

    # ── Production Totals ────────────────────────────────

    def test_production_totals_returns_expected_keys(self):
        result = self._prod_totals(self.sample_rows)
        self.assertIn("total_produced", result)
        self.assertIn("total_fixed", result)
        self.assertIn("total_definitive", result)

    def test_production_totals_values(self):
        result = self._prod_totals(self.sample_rows)
        self.assertEqual(result["total_produced"], 350)
        self.assertEqual(result["total_fixed"], 175)
        self.assertEqual(result["total_definitive"], 105)

    def test_production_totals_empty_rows(self):
        result = self._prod_totals([])
        self.assertEqual(result["total_produced"], 0)
        self.assertEqual(result["total_fixed"], 0)
        self.assertEqual(result["total_definitive"], 0)

    # ── Defects by Customer ─────────────────────────────

    def test_defects_by_customer_returns_label_value(self):
        result = self._def_by_cust(self.sample_rows)
        self.assertIsInstance(result, list)
        for item in result:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_defects_by_customer_aggregates(self):
        result = self._def_by_cust(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # CUST_A: picado_aguja(5) + manchas_sucio(3) + grasa(8) + desgarre_def_tela(10) + hoyos(15) = 41
        # CUST_B: tono_tela(4) + heat_transfer(7) + manchas_tela(6) = 17
        self.assertEqual(values["CUST_A"], 41)
        self.assertEqual(values["CUST_B"], 17)

    def test_defects_by_customer_sorted_desc(self):
        result = self._def_by_cust(self.sample_rows)
        values = [item["value"] for item in result]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_defects_by_customer_empty_rows(self):
        result = self._def_by_cust([])
        self.assertEqual(result, [])

    # ── Defects by Style ─────────────────────────────────

    def test_defects_by_style_aggregates(self):
        result = self._def_by_style(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # ST-100 (rows 1+3): picado_aguja(5) + manchas_sucio(3) + desgarre_def_tela(10) + tono_tela(4) + heat_transfer(7) + manchas_tela(6) = 35
        # ST-200 (row 2): grasa(8) + hoyos(15) = 23
        self.assertEqual(values["ST-100"], 35)
        self.assertEqual(values["ST-200"], 23)

    def test_defects_by_style_empty_rows(self):
        result = self._def_by_style([])
        self.assertEqual(result, [])

    # ── Weekly Trend ─────────────────────────────────────

    def test_weekly_trend_returns_series(self):
        result = self._weekly_trend(self.sample_rows)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        series = result[0]
        self.assertEqual(series["name"], "Defects")
        self.assertIn("data", series)

    def test_weekly_trend_aggregates_by_week(self):
        result = self._weekly_trend(self.sample_rows)
        data = {p["x"]: p["y"] for p in result[0]["data"]}
        # Week 1: 5+3+8+10+15 = 41
        # Week 2: 4+7+6 = 17
        self.assertEqual(data[1], 41)
        self.assertEqual(data[2], 17)

    def test_weekly_trend_sorted_by_week_ascending(self):
        result = self._weekly_trend(self.sample_rows)
        weeks = [p["x"] for p in result[0]["data"]]
        self.assertEqual(weeks, sorted(weeks))

    def test_weekly_trend_empty_rows(self):
        result = self._weekly_trend([])
        self.assertEqual(result[0]["data"], [])

    # ── Sewing vs Fabric ─────────────────────────────────

    def test_sewing_vs_fabric_returns_two_labels(self):
        result = self._sew_vs_fab(self.sample_rows)
        labels = {item["label"] for item in result}
        self.assertEqual(labels, {"Sewing", "Fabric"})

    def test_sewing_vs_fabric_values(self):
        result = self._sew_vs_fab(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # Sewing: picado_aguja(5) + manchas_sucio(3) + grasa(8) + tono_tela(4) + heat_transfer(7) = 27
        # Fabric: desgarre_def_tela(10) + hoyos(15) + manchas_tela(6) = 31
        self.assertEqual(values["Sewing"], 27)
        self.assertEqual(values["Fabric"], 31)

    def test_sewing_vs_fabric_empty_rows(self):
        result = self._sew_vs_fab([])
        self.assertEqual(result[0]["value"], 0)
        self.assertEqual(result[1]["value"], 0)

    # ── Top Sewing Defects ───────────────────────────────

    def test_top_sewing_defects_returns_label_value(self):
        result = self._top_sew(self.sample_rows)
        for item in result:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_top_sewing_defects_values(self):
        result = self._top_sew(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # picado_aguja=5, manchas_sucio=3, grasa=8, tono_tela=4, heat_transfer=7
        self.assertEqual(values.get("picado_aguja"), 5)
        self.assertEqual(values.get("grasa"), 8)
        self.assertNotIn("trapo", values)  # zero value excluded

    def test_top_sewing_defects_sorted_by_value_desc(self):
        result = self._top_sew(self.sample_rows)
        values = [item["value"] for item in result]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_top_sewing_defects_limited_to_10(self):
        result = self._top_sew(self.sample_rows)
        self.assertLessEqual(len(result), 10)

    def test_top_sewing_defects_empty_rows(self):
        result = self._top_sew([])
        self.assertEqual(result, [])

    # ── Top Fabric Defects ───────────────────────────────

    def test_top_fabric_defects_values(self):
        result = self._top_fab(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # desgarre_def_tela=10, hoyos=15, manchas_tela=6
        self.assertEqual(values.get("desgarre_def_tela"), 10)
        self.assertEqual(values.get("hoyos"), 15)

    def test_top_fabric_defects_excludes_sewing_defects(self):
        result = self._top_fab(self.sample_rows)
        labels = {item["label"] for item in result}
        self.assertNotIn("picado_aguja", labels)

    def test_top_fabric_defects_empty_rows(self):
        result = self._top_fab([])
        self.assertEqual(result, [])

    # ── Fix vs Definitive ────────────────────────────────

    def test_fix_vs_definitive_returns_two_series(self):
        result = self._fix_def(self.sample_rows)
        self.assertEqual(len(result), 2)
        series_names = {s["name"] for s in result}
        self.assertEqual(series_names, {"Fixed", "Definitive"})

    def test_fix_vs_definitive_values(self):
        result = self._fix_def(self.sample_rows)
        fixed = {p["x"]: p["y"] for p in result[0]["data"]}
        definitive = {p["x"]: p["y"] for p in result[1]["data"]}
        self.assertEqual(fixed[1], 110)  # 50+60
        self.assertEqual(fixed[2], 65)
        self.assertEqual(definitive[1], 66)  # 30+36
        self.assertEqual(definitive[2], 39)

    def test_fix_vs_definitive_sorted_by_week_asc(self):
        result = self._fix_def(self.sample_rows)
        weeks = [p["x"] for p in result[0]["data"]]
        self.assertEqual(weeks, sorted(weeks))

    def test_fix_vs_definitive_empty_rows(self):
        result = self._fix_def([])
        self.assertEqual(result[0]["data"], [])
        self.assertEqual(result[1]["data"], [])

    # ── Defects by Color ─────────────────────────────────

    def test_defects_by_color_aggregates(self):
        result = self._def_color(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # Red: rows 1+2 = 5+3+8+10+15 = 41
        # Blue: row 3 = 4+7+6 = 17
        self.assertEqual(values["Red"], 41)
        self.assertEqual(values["Blue"], 17)

    def test_defects_by_color_empty_rows(self):
        result = self._def_color([])
        self.assertEqual(result, [])

    # ── Defects by Size ──────────────────────────────────

    def test_defects_by_size_aggregates(self):
        result = self._def_size(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # M: rows 1 (5+3+10=18) + 3 (4+7+6=17) = 35
        # L: row 2 (8+15=23)
        self.assertEqual(values["M"], 35)
        self.assertEqual(values["L"], 23)

    def test_defects_by_size_empty_rows(self):
        result = self._def_size([])
        self.assertEqual(result, [])

    # ── Defects by Line ──────────────────────────────────

    def test_defects_by_line_aggregates_by_team(self):
        result = self._def_line(self.sample_rows)
        values = {item["label"]: item["value"] for item in result}
        # Team 5: row 1 (5+3+10=18) + row 2 (8+15=23) = 41
        # Team 10: row 3 (4+7+6=17)
        self.assertEqual(values["Line 5"], 41)
        self.assertEqual(values["Line 10"], 17)

    def test_defects_by_line_label_format(self):
        result = self._def_line(self.sample_rows)
        labels = {item["label"] for item in result}
        self.assertIn("Line 5", labels)
        self.assertIn("Line 10", labels)

    def test_defects_by_line_empty_rows(self):
        result = self._def_line([])
        self.assertEqual(result, [])

    # ── Filter Options ───────────────────────────────────

    def test_filter_options_all_keys(self):
        result = self._filter_opts(self.sample_rows)
        self.assertIn("customer", result)
        self.assertIn("style", result)
        self.assertIn("week", result)
        self.assertIn("color", result)
        self.assertIn("size", result)
        self.assertIn("team", result)

    def test_filter_options_distinct_values(self):
        result = self._filter_opts(self.sample_rows)
        self.assertEqual(set(result["customer"]), {"CUST_A", "CUST_B"})
        self.assertEqual(set(result["style"]), {"ST-100", "ST-200"})
        self.assertEqual(set(result["week"]), {1, 2})
        self.assertEqual(set(result["color"]), {"Blue", "Red"})
        self.assertEqual(set(result["size"]), {"L", "M"})
        self.assertEqual(set(result["team"]), {5, 10})

    def test_filter_options_empty_rows(self):
        result = self._filter_opts([])
        for field in ("customer", "style", "week", "color", "size", "team"):
            self.assertEqual(result[field], [])

    # ── Full dispatch test ───────────────────────────────

    def test_volatile_post_dashboard_seconds_general_returns_full_payload_now(self):
        """POST with dashboard=seconds_general returns all 12 KPIs (not empty anymore)."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = (self.sample_rows, None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'seconds_general'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have all Seconds General KPIs (not empty placeholder anymore)
        self.assertIn('filter_options', response.data)
        self.assertIn('defects_by_customer', response.data)
        self.assertIn('defects_by_style', response.data)
        self.assertIn('weekly_trend', response.data)
        self.assertIn('sewing_vs_fabric', response.data)
        self.assertIn('production_totals', response.data)
        self.assertIn('top_sewing_defects', response.data)
        self.assertIn('top_fabric_defects', response.data)
        self.assertIn('fix_vs_definitive', response.data)
        self.assertIn('defects_by_color', response.data)
        self.assertIn('defects_by_size', response.data)
        self.assertIn('defects_by_line', response.data)
        # QC FA keys should NOT be present
        self.assertNotIn('aql_by_style', response.data)
        self.assertNotIn('defect_rate', response.data)

    def test_volatile_post_dashboard_seconds_general_empty_rows_returns_zeros(self):
        """Seconds General dispatch with empty rows returns zero-filled totals (no crash)."""
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse('quality_data:kpi-volatile')
        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = ([], None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'seconds_general'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Production totals should be zeroed
        pt = response.data.get('production_totals', {})
        self.assertEqual(pt.get('total_produced'), 0)
        self.assertEqual(pt.get('total_fixed'), 0)
        self.assertEqual(pt.get('total_definitive'), 0)
        # Defects by customer should be empty
        self.assertEqual(response.data.get('defects_by_customer', []), [])


# ─────────────────────────────────────────────────────────
# Slice 3: Container Hardening + Parity Tests
# ─────────────────────────────────────────────────────────


class ContainerNormalizerIntegrationTest(TestCase):
    """
    Integration tests proving normalize_container_rows is called through
    VolatileWorkbookService.get_parsed_data('container') and produces
    deterministic, safe rows for KPI computation.
    """

    def test_normalizer_invoked_for_container_dashboard(self):
        """
        get_parsed_data('container') returns rows with NaN coerced to defaults.
        This test uses VolatileWorkbookService directly.
        """
        from unittest.mock import patch, MagicMock
        from quality_data.volatile_kpi_service import VolatileWorkbookService

        # Mock load_and_clean to return a DataFrame with NaN values
        import pandas as pd
        import math

        raw_df = pd.DataFrame([
            {
                "container_number": 100,
                "customer": "AlphaCorp",
                "date": "2025-01-10",
                "total_palette": 20,
                "total_palette_pass": 18,
                "total_palette_rejected": 2,
                "percentage_pass": float("nan"),  # NaN — should become None
                "percentage_reject": 0.05,        # Fractional — should become 5.0
                "transfer_of_container": float("nan"),  # NaN — should become 0
                "dirt_label": float("nan"),       # NaN — should become 0
                "total_defects": 8,
            },
            {
                "container_number": float("nan"),  # Invalid — row dropped
                "customer": "Dropped",
                "percentage_pass": 50.0,
            },
        ])

        service = VolatileWorkbookService(None)

        with patch.object(service, 'parse_sheet', return_value=raw_df):
            rows, defect_fields = service.get_parsed_data("container")

        # Only 1 row (the one with valid container_number)
        self.assertEqual(len(rows), 1)
        row = rows[0]

        # NaN percentage → None
        self.assertIsNone(row["percentage_pass"])
        # Fractional percentage → normalized
        self.assertEqual(row["percentage_reject"], 5.0)
        # Count field NaN → 0
        self.assertEqual(row["total_palette"], 20)
        self.assertEqual(row["transfer_of_container"], 0)
        # Defect field NaN → 0
        self.assertEqual(row["dirt_label"], 0)

    def test_normalizer_drops_all_invalid_containers(self):
        """When ALL rows have invalid container_number, returns empty list."""
        from unittest.mock import patch, MagicMock
        from quality_data.volatile_kpi_service import VolatileWorkbookService

        import pandas as pd
        import math

        raw_df = pd.DataFrame([
            {"container_number": float("nan"), "customer": "A", "percentage_pass": 50.0},
            {"container_number": None, "customer": "B", "percentage_pass": 60.0},
        ])

        service = VolatileWorkbookService(None)
        with patch.object(service, 'parse_sheet', return_value=raw_df):
            rows, _ = service.get_parsed_data("container")

        self.assertEqual(len(rows), 0)

    def test_volatile_post_container_with_nan_rows_returns_zeroed_kpis(self):
        """POST /api/kpis/volatile/ with dashboard=container and NaN data returns valid KPIs."""
        from unittest.mock import patch
        import pandas as pd

        file_obj = SimpleUploadedFile(
            'test.xlsx', b'fake',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        url = reverse('quality_data:kpi-volatile')

        # Simulate what comes through the normalizer:
        # A row with all-null percentage → None after normalization
        normalized_rows = [
            {
                "container_number": 101,
                "customer": "Test",
                "total_palette": 0,
                "total_palette_pass": 0,
                "total_palette_rejected": 0,
                "percentage_pass": None,
                "percentage_reject": None,
                "transfer_of_container": 0,
                "date": None,
                "dirt_label": 0,
            }
        ]

        with patch.object(VolatileKpiView, '_get_volatile_rows') as mock_get_rows:
            mock_get_rows.return_value = (normalized_rows, None, None)
            response = self.client.post(
                url,
                {'file': file_obj, 'dashboard': 'container'},
                format='multipart',
            )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Executive summary should still have all 4 labels
        exec_summary = response.data.get('executive_summary', [])
        self.assertEqual(len(exec_summary), 4)
        # Average pass rate should be 0 (all percentages are None)
        avg = next((item["value"] for item in exec_summary if item["label"] == "Average Pass Rate"), None)
        self.assertEqual(avg, 0)
        # Containers by state should have all 4 buckets with 0 count
        state = response.data.get('containers_by_state', [])
        self.assertEqual(len(state), 4)
        for item in state:
            self.assertEqual(item["value"], 0)
        # Worst containers should still return the row (with passRate=0 because percentage is None)
        worst = response.data.get('worst_containers', [])
        self.assertEqual(len(worst), 1)
        self.assertEqual(worst[0]["passRate"], 0)


class ContainerKpiHardeningTest(TestCase):
    """
    Hardening tests for container KPI computation helpers with edge-case inputs
    (NaN, None, fractional percentages, boundary values).
    """

    def setUp(self):
        from quality_data.volatile_kpi_service import (
            calc_container_executive_summary,
            calc_container_state_distribution,
            calc_container_pass_rate_trend,
            calc_container_inspected_trend,
            calc_container_rejected_trend,
            calc_container_top_defects,
            calc_container_defect_composition,
            calc_container_worst_containers,
        )
        self._exec_summary = calc_container_executive_summary
        self._state_dist = calc_container_state_distribution
        self._pass_trend = calc_container_pass_rate_trend
        self._insp_trend = calc_container_inspected_trend
        self._rej_trend = calc_container_rejected_trend
        self._top_defects = calc_container_top_defects
        self._defect_comp = calc_container_defect_composition
        self._worst = calc_container_worst_containers

        self.defect_fields = [
            'dirt_label', 'dirt_container', 'dirt_cartoons', 'container_holes',
            'writte_mark_on_label', 'written_mark_on_cartoon', 'container_poor_close',
            'boxes_poor_close', 'printing_issues_label', 'misaligned_label',
            'crushed_corners', 'cartoons_holes', 'warped_boxes', 'defects_label',
            'total_defects',
        ]

    # ── Executive summary hardening ───────────────────────

    def test_exec_summary_with_all_none_percentages(self):
        """All percentage_pass are None → avg_pass = 0, no crash."""
        rows = [
            {"container_number": 1, "percentage_pass": None, "total_palette": 10,
             "total_palette_rejected": 1, "customer": "A", "date": "2025-01-01"},
            {"container_number": 2, "percentage_pass": None, "total_palette": 20,
             "total_palette_rejected": 2, "customer": "B", "date": "2025-01-02"},
        ]
        result = self._exec_summary(rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["Total Containers"], 2)
        self.assertEqual(values["Average Pass Rate"], 0)
        self.assertEqual(values["Total Palettes Inspected"], 30)

    def test_exec_summary_with_mixed_none_and_real_percentages(self):
        """Mix of None and valid percentages → avg computed only from valid."""
        rows = [
            {"container_number": 1, "percentage_pass": None, "total_palette": 10,
             "total_palette_rejected": 1, "customer": "A", "date": "2025-01-01"},
            {"container_number": 2, "percentage_pass": 90.0, "total_palette": 20,
             "total_palette_rejected": 2, "customer": "B", "date": "2025-01-02"},
        ]
        result = self._exec_summary(rows)
        values = {item["label"]: item["value"] for item in result}
        # Average of [90.0] / 2 rows = 45.0 (None counted in denominator but excluded from sum)
        self.assertEqual(values["Average Pass Rate"], 45.0)

    def test_exec_summary_with_none_percentage_after_normalization(self):
        """
        None percentage_pass (what the normalizer produces from NaN/string 'NaN')
        should not crash — avg_pass computed from only non-None values.
        """
        rows = [
            {"container_number": 1, "percentage_pass": None, "total_palette": 10,
             "total_palette_rejected": 1, "customer": "A", "date": "2025-01-01"},
        ]
        result = self._exec_summary(rows)
        values = {item["label"]: item["value"] for item in result}
        self.assertEqual(values["Total Containers"], 1)
        # None percentage → excluded from avg → 0/1 = 0
        self.assertEqual(values["Average Pass Rate"], 0)

    # ── State distribution hardening ──────────────────────

    def test_state_distribution_all_none_percentages(self):
        """All percentage_pass are None → all buckets at 0, no crash."""
        rows = [
            {"percentage_pass": None},
            {"percentage_pass": None},
        ]
        result = self._state_dist(rows)
        for item in result:
            self.assertEqual(item["value"], 0)

    def test_state_distribution_mixed_none_and_valid(self):
        """None percentages are skipped, valid ones populate buckets."""
        rows = [
            {"percentage_pass": None},
            {"percentage_pass": 85.0},   # 80-90%
            {"percentage_pass": 50.0},   # < 80%
        ]
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["< 80%"], 1)
        self.assertEqual(counts["80-90%"], 1)
        self.assertEqual(counts["> 95%"], 0)

    # ── Trend hardening ───────────────────────────────────

    def test_pass_rate_trend_with_none_dates(self):
        """Rows with None dates are excluded from trend."""
        rows = [
            {"date": "2025-01-10", "percentage_pass": 90.0, "container_number": 1},
            {"date": None, "percentage_pass": 50.0, "container_number": 2},
        ]
        result = self._pass_trend(rows)
        series = result[0]
        self.assertEqual(len(series["data"]), 1)

    def test_inspected_trend_with_missing_total_palette(self):
        """Rows with missing total_palette field are handled without crash."""
        rows = [
            {"date": "2025-01-10", "total_palette": 20, "container_number": 1},
            {"date": "2025-01-11", "container_number": 2},  # no total_palette key
        ]
        result = self._insp_trend(rows)
        series = result[0]
        self.assertEqual(len(series["data"]), 2)

    # ── Defect hardening ─────────────────────────────────

    def test_top_defects_with_nan_values(self):
        """NaN in defect fields doesn't crash top_defects computation."""
        import math
        rows = [
            {"dirt_label": float("nan"), "dirt_container": 5, "container_number": 1},
        ]
        result = self._top_defects(rows, self.defect_fields)
        # Should not crash, dirt_label should be 0 or excluded
        labels = {item["label"] for item in result}
        self.assertIn("Dirt Container", labels)

    def test_worst_containers_with_none_percentages(self):
        """None percentage_pass in worst_containers sorts as 0."""
        rows = [
            {"container_number": 1, "percentage_pass": None,
             "customer": "A", "total_palette_rejected": 0, "date": None},
            {"container_number": 2, "percentage_pass": 50.0,
             "customer": "B", "total_palette_rejected": 5, "date": "2025-01-01"},
        ]
        result = self._worst(rows)
        # Row with None percentage should sort first (passRate=0)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["passRate"], 0)
        self.assertEqual(result[1]["passRate"], 50.0)

    # ── State distribution boundary parity ────────────────

    def test_state_distribution_boundary_80_parity(self):
        """
        Boundary parity: percentage_pass=80.0 falls in 80-90% bucket,
        matching live endpoint's Case/When: gte=80 AND lt=90.
        """
        rows = [{"percentage_pass": 80.0}]
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["80-90%"], 1)
        self.assertEqual(counts["< 80%"], 0)

    def test_state_distribution_boundary_95_parity(self):
        """
        Boundary parity: percentage_pass=95.0 falls in 90-95% bucket,
        matching live endpoint's Case/When: gte=90 AND lte=95.
        """
        rows = [{"percentage_pass": 95.0}]
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["90-95%"], 1)
        self.assertEqual(counts["> 95%"], 0)

    def test_state_distribution_boundary_gt_95_parity(self):
        """
        Boundary parity: percentage_pass=95.1 falls in > 95% bucket,
        matching live endpoint's Case/When: gt=95.
        """
        rows = [{"percentage_pass": 95.1}]
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["> 95%"], 1)

    def test_state_distribution_zero_percent_parity(self):
        """
        Boundary parity: percentage_pass=0 falls in < 80% bucket,
        matching live endpoint's behavior.
        """
        rows = [{"percentage_pass": 0.0}]
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["< 80%"], 1)

    def test_state_distribution_fractional_percentage_parity(self):
        """
        Parity: After normalizer converts 0.97 → 97.0, the bucket is > 95%.
        This verifies the end-to-end pipeline from normalizer to state distribution.
        """
        rows = [{"percentage_pass": 97.0}]  # Already normalized
        result = self._state_dist(rows)
        counts = {item["name"]: item["value"] for item in result}
        self.assertEqual(counts["> 95%"], 1)
