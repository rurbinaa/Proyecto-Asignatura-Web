from django.test import TestCase
import datetime
import numpy as np
import pandas as pd

from excel_importer.date_utils import (
    parse_date,
    normalize_container_date,
    canonicalize_qc_fa_date,
    build_qc_fa_key,
)


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


class CanonicalizeQcFaDateTest(TestCase):
    """Tests for canonicalize_qc_fa_date() — QC FA date canonicalization helper."""

    # ── Happy path: equivalent formats produce same canonical output ──

    def test_iso_date_stays_iso(self):
        """ISO date string returns unchanged."""
        self.assertEqual(canonicalize_qc_fa_date("2025-01-15"), "2025-01-15")

    def test_us_date_canonicalizes_to_iso(self):
        """US format '01/15/2025' canonicalizes to '2025-01-15'."""
        self.assertEqual(canonicalize_qc_fa_date("01/15/2025"), "2025-01-15")

    def test_eu_dot_date_canonicalizes_to_iso(self):
        """EU dot format '15.01.2025' canonicalizes to '2025-01-15'."""
        self.assertEqual(canonicalize_qc_fa_date("15.01.2025"), "2025-01-15")

    def test_excel_serial_canonicalizes_to_iso(self):
        """Excel serial number 45672 canonicalizes to '2025-01-15'."""
        self.assertEqual(canonicalize_qc_fa_date(45672), "2025-01-15")

    def test_datetime_object_canonicalizes_to_iso(self):
        """Python datetime canonicalizes to ISO string."""
        dt = datetime.datetime(2025, 3, 15)
        self.assertEqual(canonicalize_qc_fa_date(dt), "2025-03-15")

    def test_pandas_timestamp_canonicalizes_to_iso(self):
        """Pandas Timestamp canonicalizes to ISO string."""
        ts = pd.Timestamp("2025-06-20")
        self.assertEqual(canonicalize_qc_fa_date(ts), "2025-06-20")

    # ── Equivalent dates across formats all canonicalize to the SAME string ──

    def test_equivalent_dates_produce_same_canonical_string(self):
        """Different representations of 2025-01-15 yield identical canonical output."""
        inputs = [
            "2025-01-15",
            "01/15/2025",
            "1/15/2025",
            "15.01.2025",
            "15.1.2025",
            "January 15, 2025",
            "Jan 15 2025",
            45672,
            datetime.date(2025, 1, 15),
            datetime.datetime(2025, 1, 15),
            pd.Timestamp("2025-01-15"),
        ]
        results = {canonicalize_qc_fa_date(v) for v in inputs}
        self.assertEqual(len(results), 1, f"All should normalize to the same string, got {results}")
        self.assertIn("2025-01-15", results)

    # ── Edge: empty, None, unparsable, whitespace ──

    def test_empty_string_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date(""))

    def test_none_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date(None))

    def test_unparsable_placeholder_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date("UNKNOWN"))
        self.assertIsNone(canonicalize_qc_fa_date("N/A"))
        self.assertIsNone(canonicalize_qc_fa_date("NONE"))
        self.assertIsNone(canonicalize_qc_fa_date("NULL"))

    def test_pandas_nat_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date(pd.NaT))

    def test_whitespace_only_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date("   "))

    def test_garbage_string_returns_none(self):
        """Totally unparsable string returns None."""
        self.assertIsNone(canonicalize_qc_fa_date("not-a-date-at-all"))

    # ── Edge: numeric zero and negative serials ──

    def test_excel_serial_zero_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date(0))

    def test_excel_serial_negative_returns_none(self):
        self.assertIsNone(canonicalize_qc_fa_date(-1))


class BuildQcFaKeyTest(TestCase):
    """Tests for build_qc_fa_key() — shared QC FA natural-key builder."""

    def _make_row(self, date_1="2025-01-15", po=12345, style="STYLE-A",
                  team=1, color="red", table_type="QFA"):
        return {
            "date_1": date_1,
            "po": po,
            "style": style,
            "team": team,
            "color": color,
            "table_type": table_type,
        }

    # ── Basic key construction ──

    def test_builds_key_with_explicit_table_type(self):
        """Key built from a QFA row dict includes (canonical_date, po, style, team, color, table_type, line_code)."""
        row = self._make_row()
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key, ("2025-01-15", 12345, "STYLE-A", 1, "red", "QFA", None))

    def test_builds_key_for_qfc_with_explicit_table_type(self):
        """Key built for a QFC row includes 'QFC' as table_type."""
        row = self._make_row(table_type="QFC")
        key = build_qc_fa_key(row, table_type="QFC")
        self.assertEqual(key[5], "QFC")

    # ── Table type fallback from row ──

    def test_falls_back_to_row_table_type_when_not_explicit(self):
        """When table_type arg is None, derives from row['table_type']."""
        row = self._make_row(table_type="QFC")
        key = build_qc_fa_key(row)
        self.assertEqual(key[5], "QFC")

    def test_defaults_to_qfa_when_table_type_missing(self):
        """When neither arg nor row has table_type, defaults to 'QFA'."""
        row = self._make_row()
        del row["table_type"]
        key = build_qc_fa_key(row)
        self.assertEqual(key[5], "QFA")

    # ── Color normalization ──

    def test_normalizes_color_to_lowercase_underscored(self):
        """Color 'Dark Blue' becomes 'dark_blue' in the key."""
        row = self._make_row(color="Dark Blue")
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[4], "dark_blue")

    def test_strips_whitespace_from_color_and_style(self):
        """Color and style have leading/trailing whitespace stripped."""
        row = self._make_row(color="  red  ", style="  STYLE-X  ")
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[2], "STYLE-X")
        self.assertEqual(key[4], "red")

    # ── Equivalent dates produce identical keys ──

    def test_equivalent_dates_produce_identical_keys(self):
        """Two rows with different date representations of the same day yield identical keys."""
        row_iso = self._make_row(date_1="2025-01-15")
        row_us = self._make_row(date_1="01/15/2025")
        row_serial = self._make_row(date_1=45672)
        row_dt = self._make_row(date_1=datetime.date(2025, 1, 15))

        key_iso = build_qc_fa_key(row_iso, table_type="QFA")
        key_us = build_qc_fa_key(row_us, table_type="QFA")
        key_serial = build_qc_fa_key(row_serial, table_type="QFA")
        key_dt = build_qc_fa_key(row_dt, table_type="QFA")

        self.assertEqual(key_iso, key_us, "ISO vs US should match")
        self.assertEqual(key_iso, key_serial, "ISO vs Excel serial should match")
        self.assertEqual(key_iso, key_dt, "ISO vs datetime.date should match")

    # ── Keys are hashable and usable as dict keys ──

    def test_key_is_hashable(self):
        """The returned key tuple can be used as a dict key."""
        row = self._make_row()
        key = build_qc_fa_key(row, table_type="QFA")
        d = {key: "found"}
        self.assertEqual(d[key], "found")
        # Prove that an otherwise identical QFC row gets a DIFFERENT key
        row_qfc = self._make_row(table_type="QFC")
        key_qfc = build_qc_fa_key(row_qfc, table_type="QFC")
        self.assertNotEqual(key, key_qfc)
        d[key_qfc] = "also found"
        self.assertEqual(len(d), 2)

    # ── Missing fields are handled gracefully ──

    def test_missing_date_returns_none_first_element(self):
        """When date_1 is absent from the row, canonical date is None."""
        row = self._make_row()
        del row["date_1"]
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[0])

    def test_missing_po_returns_zero(self):
        row = self._make_row()
        del row["po"]
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[1], 0)

    def test_missing_style_returns_empty_string(self):
        row = self._make_row()
        del row["style"]
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[2], "")

    def test_missing_team_returns_zero(self):
        row = self._make_row()
        del row["team"]
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[3], 0)

    def test_missing_color_returns_unknown(self):
        row = self._make_row()
        del row["color"]
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[4], "unknown")

    # ── PO and team are coerced to int ──

    def test_po_string_coerced_to_int(self):
        row = self._make_row(po="12345")
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsInstance(key[1], int)
        self.assertEqual(key[1], 12345)

    def test_team_string_coerced_to_int(self):
        row = self._make_row(team="1")
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsInstance(key[3], int)
        self.assertEqual(key[3], 1)

    # ── line_code normalization (NaN → None) ──

    def test_nan_line_code_normalized_to_none(self):
        """float('nan') as line_code is converted to None in the key."""
        row = self._make_row()
        row["line_code"] = float("nan")
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[6])

    def test_empty_string_line_code_normalized_to_none(self):
        """Empty string as line_code is converted to None."""
        row = self._make_row()
        row["line_code"] = ""
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[6])

    def test_pandas_nan_line_code_normalized_to_none(self):
        """Pandas NaN (np.nan) as line_code is converted to None in the key."""
        import numpy as np
        row = self._make_row()
        row["line_code"] = np.nan
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[6])

    def test_string_nan_line_code_normalized_to_none(self):
        """The string 'nan' as line_code is converted to None."""
        row = self._make_row()
        row["line_code"] = "nan"
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[6])

    def test_valid_line_code_preserved(self):
        """A valid dual-line code like '35-36' is preserved as-is in the key."""
        row = self._make_row()
        row["line_code"] = "35-36"
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertEqual(key[6], "35-36")

    def test_none_line_code_remains_none(self):
        """Explicit None as line_code remains None."""
        row = self._make_row()
        row["line_code"] = None
        key = build_qc_fa_key(row, table_type="QFA")
        self.assertIsNone(key[6])
