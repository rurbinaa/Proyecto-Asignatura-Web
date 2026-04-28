"""
Date parsing utility for normalizing CharField dates from Excel.

The quality_data models store dates as CharField (not DateField), so we need
a utility to parse various date formats into a normalized 'YYYY-MM-DD' string
for comparison during Time-Window Sync.
"""

import datetime
import numbers
import re

import pandas as pd


def parse_date(value):
    """
    Parse a date value into a normalized 'YYYY-MM-DD' string.

    Handles:
    - String dates in various formats (ISO, US, EU, with month names)
    - Datetime objects
    - Pandas Timestamps
    - Excel serial numbers (days since 1899-12-30)
    - None, empty strings, pandas NaT, and invalid values → returns None

    Args:
        value: The date value to parse (str, datetime, Timestamp, int, None)

    Returns:
        str: Normalized date string 'YYYY-MM-DD', or None if unparseable.
    """
    if value is None:
        return None

    # Handle pandas NaT (Not a Time) — must be checked BEFORE datetime check
    # because NaT inherits from datetime.datetime in some pandas versions
    # but does NOT support strftime()
    if isinstance(value, type(pd.NaT)):
        return None

    # Handle datetime objects (includes pandas Timestamp)
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")

    # Handle datetime.date objects
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")

    # Handle numeric values (Excel serial dates)
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return _parse_excel_serial(value)

    # Handle strings
    if isinstance(value, str):
        value = value.strip()
        if not value or value.upper() in ("UNKNOWN", "N/A", "NONE", "NULL", ""):
            return None
        return _parse_date_string(value)

    return None


def _parse_date_string(value):
    """Parse a date string using multiple format attempts."""
    # Try common formats in order of likelihood
    formats = [
        "%Y-%m-%d",       # 2025-01-15 (ISO)
        "%Y/%m/%d",       # 2025/01/15
        "%m/%d/%Y",       # 01/15/2025 (US)
        "%m/%d/%y",       # 01/15/25
        "%d/%m/%Y",       # 15/01/2025 (EU)
        "%d/%m/%y",       # 15/01/25
        "%d.%m.%Y",       # 15.01.2025 (dot)
        "%d.%m.%y",       # 15.01.25
        "%Y-%m-%d %H:%M:%S",  # 2025-01-15 00:00:00
        "%m-%d-%Y",       # 01-15-2025
        "%d-%m-%Y",       # 15-01-2025
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try month name formats (e.g., "January 15, 2025")
    month_name_patterns = [
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",   # January 15, 2025
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",       # 15 January 2025
    ]

    for pattern in month_name_patterns:
        match = re.fullmatch(pattern, value)
        if match:
            groups = match.groups()
            try:
                # Try both orderings
                try:
                    dt = datetime.datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%B %d %Y")
                except ValueError:
                    dt = datetime.datetime.strptime(f"{groups[1]} {groups[0]} {groups[2]}", "%B %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    dt = datetime.datetime.strptime(f"{groups[0]} {groups[1]} {groups[2]}", "%b %d %Y")
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    return None


def _parse_excel_serial(serial):
    """
    Convert an Excel serial date number to 'YYYY-MM-DD' string.

    Excel uses a serial number system where day 1 maps to 1900-01-01,
    with a historical leap-year bug at serial 60 (1900-02-29, non-existent).
    We collapse serial 60 to 1900-02-28 so Python date conversion stays valid.
    """
    try:
        serial_int = int(serial)

        if serial_int <= 0:
            return None

        # Serial 60 represents Excel's fake 1900-02-29; collapse to 1900-02-28.
        if serial_int >= 60:
            serial_int -= 1

        epoch = datetime.date(1899, 12, 31)
        result_date = epoch + datetime.timedelta(days=serial_int)
        return result_date.strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def normalize_container_date(value):
    """Return a Python date for Container.date or None when unparseable."""
    normalized = parse_date(value)
    if not normalized:
        return None

    try:
        return datetime.date.fromisoformat(normalized)
    except (TypeError, ValueError):
        return None


def normalize_date_bounds(date_from, date_to):
    """Normalize mixed date inputs into validated Python date bounds."""
    normalized_from = _normalize_date_bound_value(date_from)
    normalized_to = _normalize_date_bound_value(date_to)

    if normalized_from and normalized_to and normalized_from > normalized_to:
        raise ValueError("Invalid date range. Start date must be on or before end date.")

    return normalized_from, normalized_to


def apply_charfield_iso_date_range(queryset, field_name, date_from, date_to):
    """Filter CharField-ISO dates with normalized date bounds."""
    normalized_from, normalized_to = normalize_date_bounds(date_from, date_to)

    if normalized_from:
        queryset = queryset.filter(**{f"{field_name}__gte": normalized_from.isoformat()})
    if normalized_to:
        queryset = queryset.filter(**{f"{field_name}__lte": normalized_to.isoformat()})

    return queryset


def apply_datefield_date_range(queryset, field_name, date_from, date_to):
    """Filter DateField values with normalized date bounds."""
    normalized_from, normalized_to = normalize_date_bounds(date_from, date_to)

    if normalized_from:
        queryset = queryset.filter(**{f"{field_name}__gte": normalized_from})
    if normalized_to:
        queryset = queryset.filter(**{f"{field_name}__lte": normalized_to})

    return queryset


def _normalize_date_bound_value(value):
    if value is None:
        return None

    if isinstance(value, datetime.datetime):
        return value.date()

    if isinstance(value, datetime.date):
        return value

    if isinstance(value, str):
        normalized = parse_date(value)
        if normalized:
            return datetime.date.fromisoformat(normalized)
        return None

    normalized = parse_date(value)
    if normalized:
        return datetime.date.fromisoformat(normalized)

    return None
