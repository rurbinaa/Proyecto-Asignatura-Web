from django.test import TestCase
from excel_importer.date_utils import parse_date


class ParseDateTest(TestCase):
    """Tests for parse_date() utility that normalizes CharField dates for comparison."""

    def test_parse_iso_date(self):
        """Given a date in ISO format '2025-01-15', returns normalized '2025-01-15'."""
        result = parse_date("2025-01-15")
        self.assertEqual(result, "2025-01-15")

    def test_parse_us_date(self):
        """Given a date in US format '01/15/2025', returns normalized '2025-01-15'."""
        result = parse_date("01/15/2025")
        self.assertEqual(result, "2025-01-15")

    def test_parse_us_date_single_digit(self):
        """Given a date '1/5/2025', returns normalized '2025-01-05'."""
        result = parse_date("1/5/2025")
        self.assertEqual(result, "2025-01-05")

    def test_parse_dot_date(self):
        """Given a date '15.01.2025', returns normalized '2025-01-15'."""
        result = parse_date("15.01.2025")
        self.assertEqual(result, "2025-01-15")

    def test_parse_excel_serial_date(self):
        """Given a numeric Excel serial date (e.g., 45672), returns normalized date string."""
        result = parse_date(45672)
        self.assertIsNotNone(result)
        self.assertRegex(result, r"^\d{4}-\d{2}-\d{2}$")

    def test_parse_empty_string(self):
        """Given an empty string, returns None."""
        result = parse_date("")
        self.assertIsNone(result)

    def test_parse_none(self):
        """Given None, returns None."""
        result = parse_date(None)
        self.assertIsNone(result)

    def test_parse_invalid_string(self):
        """Given an unparseable string 'UNKNOWN', returns None."""
        result = parse_date("UNKNOWN")
        self.assertIsNone(result)

    def test_parse_with_whitespace(self):
        """Given ' 2025-01-15 ', returns normalized '2025-01-15'."""
        result = parse_date(" 2025-01-15 ")
        self.assertEqual(result, "2025-01-15")

    def test_parse_datetime_object(self):
        """Given a datetime object, returns normalized string."""
        import datetime
        dt = datetime.datetime(2025, 3, 15)
        result = parse_date(dt)
        self.assertEqual(result, "2025-03-15")

    def test_parse_pandas_timestamp(self):
        """Given a pandas Timestamp, returns normalized string."""
        import pandas as pd
        ts = pd.Timestamp("2025-06-20")
        result = parse_date(ts)
        self.assertEqual(result, "2025-06-20")

    def test_parse_pandas_nat(self):
        """Given a pandas NaT (empty date cell), returns None instead of crashing."""
        import pandas as pd
        result = parse_date(pd.NaT)
        self.assertIsNone(result)

    def test_parse_day_month_year_format(self):
        """Given '20/06/2025' (DD/MM/YYYY), returns normalized '2025-06-20'."""
        result = parse_date("20/06/2025")
        self.assertEqual(result, "2025-06-20")

    def test_parse_month_name_format(self):
        """Given 'January 15, 2025', returns normalized '2025-01-15'."""
        result = parse_date("January 15, 2025")
        self.assertEqual(result, "2025-01-15")
