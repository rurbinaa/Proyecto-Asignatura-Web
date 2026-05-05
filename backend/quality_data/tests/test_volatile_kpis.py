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

    def test_volatile_post_uses_dto_serialization_helpers(self):
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

        with patch('quality_data.views.load_and_clean', return_value=qc_df):
            with patch('quality_data.views.parse_seconds_rework', return_value=[]):
                with patch('quality_data.views.parse_fabric_defects', return_value=[]):
                    with patch('quality_data.views.parse_containers_by_state', return_value=[]):
                        with patch('quality_data.views.parse_top_defects', return_value=[]):
                            with patch('quality_data.views.parse_defects_by_style', return_value=[]):
                                with patch(
                                    'quality_data.views._serialize_payload',
                                    wraps=__import__('quality_data.views', fromlist=['_serialize_payload'])._serialize_payload,
                                ) as serialize_payload:
                                    response = self.client.post(
                                        self.url,
                                        {'file': file_obj},
                                        format='multipart',
                                    )

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertGreaterEqual(serialize_payload.call_count, 1)

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

        # When load_and_clean fails, post() should return 400 with error
        with patch('quality_data.views.load_and_clean', side_effect=Exception("Simulated I/O error")):
            response = self.client.post(
                self.url,
                {'file': uploaded_file},
                format='multipart'
            )
            # Should return error response, not crash
            self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)


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

        with patch('quality_data.views.load_and_clean', return_value=qc_df):
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
