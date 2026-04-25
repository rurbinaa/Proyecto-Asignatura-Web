from django.test import TestCase
import datetime
import numpy as np
import pandas as pd

from excel_importer.date_utils import parse_date, normalize_container_date


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
        ts = pd.Timestamp("2025-06-20")
        result = parse_date(ts)
        self.assertEqual(result, "2025-06-20")

    def test_parse_pandas_nat(self):
        """Given a pandas NaT (empty date cell), returns None instead of crashing."""
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

    def test_parse_month_name_with_trailing_text_returns_none(self):
        self.assertIsNone(parse_date("January 15, 2025 trailing"))
        self.assertIsNone(parse_date("15 January 2025 trailing"))


class NormalizeContainerDateTest(TestCase):
    def test_returns_python_date_for_valid_input(self):
        result = normalize_container_date("2025-03-12")
        self.assertEqual(result, datetime.date(2025, 3, 12))

    def test_returns_none_for_invalid_or_empty_input(self):
        self.assertIsNone(normalize_container_date("UNKNOWN"))
        self.assertIsNone(normalize_container_date(""))

    def test_returns_python_date_for_excel_serial_float(self):
        result = normalize_container_date(45672.9)
        self.assertIsInstance(result, datetime.date)


class ParseDateAdditionalCoverageTest(TestCase):
    def test_parse_date_object(self):
        result = parse_date(datetime.date(2025, 4, 7))
        self.assertEqual(result, "2025-04-07")

    def test_parse_invalid_types_and_placeholders(self):
        self.assertIsNone(parse_date(object()))
        self.assertIsNone(parse_date("N/A"))
        self.assertIsNone(parse_date("NONE"))
        self.assertIsNone(parse_date("NULL"))

    def test_parse_month_name_with_day_first_and_abbrev(self):
        self.assertEqual(parse_date("15 January 2025"), "2025-01-15")
        self.assertEqual(parse_date("Jan 15 2025"), "2025-01-15")

    def test_parse_excel_serial_invalid_number_returns_none(self):
        self.assertIsNone(parse_date(float("inf")))

    def test_parse_excel_serial_exact_early_values(self):
        self.assertEqual(parse_date(1), "1900-01-01")
        self.assertEqual(parse_date(59), "1900-02-28")
        self.assertEqual(parse_date(60), "1900-02-28")
        self.assertEqual(parse_date(61), "1900-03-01")

    def test_parse_excel_serial_zero_and_negative_values(self):
        self.assertIsNone(parse_date(0))
        self.assertIsNone(parse_date(-1))

    def test_parse_excel_serial_numpy_integer_scalar(self):
        self.assertEqual(parse_date(np.int64(45672)), "2025-01-15")

    def test_parse_excel_serial_pandas_integer_scalar(self):
        serial = pd.array([45672], dtype="Int64")[0]
        self.assertEqual(parse_date(serial), "2025-01-15")
