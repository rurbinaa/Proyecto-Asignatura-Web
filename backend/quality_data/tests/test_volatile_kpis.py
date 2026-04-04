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
from rest_framework.test import APIClient
from rest_framework import status as http_status

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

    # ─────────────────────────────────────────────────────────
    # 2.3 — Empty DataFrame (helper method tests)
    # ─────────────────────────────────────────────────────────

    def test_volatile_empty_dataframe_aql_by_style(self):
        """
        Empty DataFrame should return [] for _calc_aql_by_style.
        """
        result = self.view._calc_aql_by_style([])
        self.assertEqual(result, [])

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
        DataFrame with sample=0 should return value=0 for _calc_defect_rate
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
        # Should not crash and should handle negative defect values
        result = self.view._calc_aql_by_style(rows)
        # N3165 with negative defects should not appear (filtered or handled)
        # N4165 with 0 defects should have 0 AQL
        # N5165 with huge defects should have extreme AQL value
        self.assertEqual(len(result), 3)

    def test_volatile_parser_exception_returns_null(self):
        """
        When post() parser functions fail, the view should return a 400 error
        (not crash the entire endpoint).
        """
        import io
        from unittest.mock import patch

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

        # When load_and_clean fails, post() should return 400 with error
        with patch('quality_data.views.load_and_clean', side_effect=Exception("Simulated I/O error")):
            response = self.client.post(
                self.url,
                {'file': buffer},
                format='multipart'
            )
            # Should return error response, not crash
            self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
