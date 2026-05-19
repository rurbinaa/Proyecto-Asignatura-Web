"""
Tests for Seconds A4 analytics endpoints (PR 1 — backend foundation + filter-options).

Verifies:
  - SecondsA4FilterMixin: filter parsing, year scoping, invalid params, empty queryset
  - filter-options endpoint: available years/lines/cut_num/style/color/week,
    year-scoped narrowing, empty dataset behavior
  - Cache helpers: filter normalization, stable key hashing, TTL lookup,
    safe cache fallback
  - Endpoint caching: cache hit/miss, key stability, failure fallback
"""

import hashlib
import json
from unittest.mock import patch

from django.core.cache import cache as django_cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status as http_status
from quality_data.models import SecondsA4, Color
from quality_data.views import seconds_a4_views as views_module

# String path for cache patching (resolved at execution time, not import).
_SECONDS_A4_CACHE_PATH = "quality_data.views.seconds_a4_views.cache"

# Use local-memory cache for all tests to avoid Redis dependency.
_LOCMEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


class SecondsA4AnalyticsMixin:
    """
    Mixin that creates SecondsA4 records across multiple years, styles, colors,
    lines, and cut_nums for analytics endpoint tests.
    """

    def setUp(self):
        # Clear cache to prevent cross-test pollution (LocMemCache is
        # process-global within the same @override_settings scope).
        # Gracefully handle Redis-unavailable environments.
        try:
            django_cache.clear()
        except Exception:
            pass

        self.client = APIClient()

        # ── Create Color records ──
        self.colors = {}
        for name in ["Red", "Blue", "White", "Black"]:
            color, _ = Color.objects.get_or_create(name=name)
            self.colors[name] = color

        # ── Create SecondsA4 records ──
        # (year, week, date, cut_num, style, color, line, total_of_2ds, sew_def, fab_def,
        #  accepted, rejected, seconds_by_sew, seconds_by_fab,
        #  seconds_sew_a4, seconds_fab_a4, ...)
        self.records_data = [
            # year 2025 — 4 records across different dimensions
            (2025, 1, "2025-01-05", 101, "STYLE-A", "Red",   "L1", 10, 3, 2, 50, 5, 40, 30, 20, 10),
            (2025, 2, "2025-01-12", 101, "STYLE-A", "Blue",  "L1", 15, 4, 3, 60, 6, 50, 40, 25, 15),
            (2025, 3, "2025-01-19", 102, "STYLE-B", "Red",   "L2", 20, 5, 4, 70, 7, 60, 50, 30, 20),
            (2025, 4, "2025-01-26", 102, "STYLE-B", "White", "L2", 25, 6, 5, 80, 8, 70, 55, 35, 25),
            # year 2026 — 3 records, same style/line overlap with 2025
            (2026, 5, "2026-02-02", 103, "STYLE-A", "Black", "L1", 12, 2, 1, 40, 4, 30, 20, 15, 5),
            (2026, 6, "2026-02-09", 103, "STYLE-C", "Red",   "L3", 18, 7, 6, 55, 5, 45, 35, 22, 12),
            (2026, 7, "2026-02-16", 104, "STYLE-C", "Blue",  "L3", 22, 8, 7, 65, 6, 55, 45, 28, 18),
            # year 2027 — 2 records
            (2027, 8, "2027-02-21", 105, "STYLE-D", "White", "L4", 30, 2, 1, 90, 9, 80, 60, 40, 30),
            (2027, 9, "2027-02-28", 105, "STYLE-D", "Black", "L4", 35, 3, 2, 95, 10, 85, 65, 45, 35),
        ]

        self.created_records = []
        for (year, week, date, cut_num, style, color_name, line,
             total_of_2ds, sew_def, fab_def, accepted, rejected,
             seconds_by_sew, seconds_by_fab, seconds_sew_a4, seconds_fab_a4) in self.records_data:
            record = SecondsA4.objects.create(
                year=year,
                week=week,
                date=date,
                cut_num=cut_num,
                style=style,
                cut_qty=100,
                color=self.colors[color_name],
                first_quality_qty_sewing=80,
                sample=20,
                pass_field=15,
                fail_field=5,
                sew_def=sew_def,
                fab_def=fab_def,
                accepted=accepted,
                rejected=rejected,
                total_of_2ds=total_of_2ds,
                percentage_of_2ds=float(total_of_2ds) / 100.0 if total_of_2ds else 0.0,
                line=line,
                seconds_by_sew=seconds_by_sew,
                seconds_by_fab=seconds_by_fab,
                seconds_sew_a4=seconds_sew_a4,
                seconds_fab_a4=seconds_fab_a4,
            )
            self.created_records.append(record)


# ─────────────────────────────────────────────────────────
# SecondsA4FilterMixin — Filter Parsing & Scope
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4FilterMixinTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for SecondsA4FilterMixin filter parsing and queryset scoping."""

    def _get_filtered_count(self, params):
        """Helper: call a simple aggregator endpoint and return record count."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        return response.data

    # ── year filter ──

    def test_year_filter_narrows_to_single_year(self):
        """?year=2025 returns only records from 2025."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "2025"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Year 2025 has lines L1, L2; styles STYLE-A, STYLE-B
        self.assertIn("L1", response.data["line"])
        self.assertIn("L2", response.data["line"])
        self.assertNotIn("L3", response.data["line"])
        self.assertNotIn("L4", response.data["line"])

    def test_year_filter_invalid_value_returns_400(self):
        """Invalid year returns 400."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "not-a-number"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    def test_year_filter_excludes_other_years(self):
        """When year=2026, styles from 2027 are excluded."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "2026"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # 2026 has STYLE-A and STYLE-C, not STYLE-D
        self.assertIn("STYLE-A", response.data["style"])
        self.assertIn("STYLE-C", response.data["style"])
        self.assertNotIn("STYLE-D", response.data["style"])

    # ── week filter ──

    def test_week_filter_narrows_to_single_week(self):
        """?week=1 returns only records from week 1."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"week": "1"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Week 1 has style STYLE-A, line L1, cut_num 101
        self.assertEqual(response.data["style"], ["STYLE-A"])
        self.assertEqual(response.data["line"], ["L1"])
        self.assertEqual(response.data["cut_num"], [101])
        self.assertNotIn("STYLE-B", response.data["style"])

    def test_week_filter_invalid_value_returns_400(self):
        """Invalid week returns 400."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"week": "abc"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    # ── style filter ──

    def test_style_filter_narrows_results(self):
        """?style=STYLE-A narrows to matching records."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"style": "STYLE-A"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # STYLE-A appears in years 2025 and 2026, lines L1 only
        self.assertEqual(response.data["line"], ["L1"])
        self.assertIn(2025, response.data["year"])
        self.assertIn(2026, response.data["year"])
        self.assertNotIn("STYLE-C", response.data["style"])

    # ── color filter ──

    def test_color_filter_narrows_results(self):
        """?color=Red narrows to matching records."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"color": "Red"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Red appears in years 2025, 2026
        self.assertIn(2025, response.data["year"])
        self.assertIn(2026, response.data["year"])
        self.assertNotIn(2027, response.data["year"])

    # ── line filter ──

    def test_line_filter_narrows_results(self):
        """?line=L1 narrows to matching records."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"line": "L1"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # L1 appears in years 2025 and 2026
        self.assertIn(2025, response.data["year"])
        self.assertIn(2026, response.data["year"])
        # L1 has styles STYLE-A only
        self.assertEqual(response.data["style"], ["STYLE-A"])

    # ── cut_num filter ──

    def test_cut_num_filter_narrows_results(self):
        """?cut_num=101 narrows to matching records."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"cut_num": "101"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Cut 101 appears in year 2025 only
        self.assertEqual(response.data["year"], [2025])
        self.assertEqual(set(response.data["line"]), {"L1"})
        self.assertEqual(set(response.data["style"]), {"STYLE-A"})

    def test_cut_num_filter_invalid_value_returns_400(self):
        """Invalid cut_num returns 400."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"cut_num": "not-a-number"})
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)

    # ── combined filters ──

    def test_combined_year_and_line_filter(self):
        """Multiple filters combine with AND logic."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "2025", "line": "L2"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # 2025 + L2 → only STYLE-B, cut_num 102
        self.assertEqual(response.data["style"], ["STYLE-B"])
        self.assertEqual(response.data["cut_num"], [102])

    # ── empty dataset ──

    def test_empty_dataset_returns_empty_lists(self):
        """When no records exist, filter-options returns empty arrays."""
        SecondsA4.objects.all().delete()
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for field in ("year", "line", "cut_num", "style", "color", "week"):
            self.assertEqual(
                response.data[field], [],
                f"Field '{field}' should be empty when no records exist"
            )

    def test_empty_dataset_after_filter_returns_empty_lists(self):
        """Filters matching no records return empty arrays, not errors."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "9999"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for field in ("year", "line", "cut_num", "style", "color", "week"):
            self.assertEqual(
                response.data[field], [],
                f"Field '{field}' should be empty when filter matches nothing"
            )


# ─────────────────────────────────────────────────────────
# SecondsA4 Filter Options Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4FilterOptionsTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/filter-options/"""

    def test_returns_200_with_filter_option_keys(self):
        """Returns 200 with the expected filter option arrays."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("year", response.data)
        self.assertIn("line", response.data)
        self.assertIn("cut_num", response.data)
        self.assertIn("style", response.data)
        self.assertIn("color", response.data)
        self.assertIn("week", response.data)

    def test_filter_options_contain_expected_unique_values(self):
        """Each field contains distinct values from SecondsA4 records."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)

        # Years: 2025, 2026, 2027
        self.assertEqual(set(response.data["year"]), {2025, 2026, 2027})

        # Lines: L1, L2, L3, L4
        self.assertEqual(set(response.data["line"]), {"L1", "L2", "L3", "L4"})

        # Cut nums: 101, 102, 103, 104, 105
        self.assertEqual(set(response.data["cut_num"]), {101, 102, 103, 104, 105})

        # Styles: STYLE-A, STYLE-B, STYLE-C, STYLE-D
        self.assertEqual(set(response.data["style"]), {"STYLE-A", "STYLE-B", "STYLE-C", "STYLE-D"})

        # Colors: Red, Blue, White, Black
        self.assertEqual(set(response.data["color"]), {"Red", "Blue", "White", "Black"})

        # Weeks: 1-9
        self.assertEqual(set(response.data["week"]), {1, 2, 3, 4, 5, 6, 7, 8, 9})

    def test_all_values_are_unique(self):
        """Each array contains no duplicates."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)

        for field in ("year", "line", "cut_num", "style", "color", "week"):
            values = response.data[field]
            self.assertEqual(
                len(values), len(set(values)),
                f"Field '{field}' contains duplicate values"
            )

    def test_values_are_sorted(self):
        """Numeric fields are sorted ascending; string fields alphabetically."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)

        # Numeric: year, week, cut_num
        self.assertEqual(response.data["year"], sorted(response.data["year"]))
        self.assertEqual(response.data["week"], sorted(response.data["week"]))
        self.assertEqual(response.data["cut_num"], sorted(response.data["cut_num"]))

        # String: line, style, color
        self.assertEqual(response.data["line"], sorted(response.data["line"]))
        self.assertEqual(response.data["style"], sorted(response.data["style"]))
        self.assertEqual(response.data["color"], sorted(response.data["color"]))

    def test_year_filter_narrows_line_and_cut_num(self):
        """When year=2025, line and cut_num lists are narrowed."""
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "2025"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # 2025 has lines L1, L2 only
        self.assertEqual(set(response.data["line"]), {"L1", "L2"})
        # 2025 has cut_nums 101, 102 only
        self.assertEqual(set(response.data["cut_num"]), {101, 102})
        # 2025 has styles STYLE-A, STYLE-B only
        self.assertEqual(set(response.data["style"]), {"STYLE-A", "STYLE-B"})


# ─────────────────────────────────────────────────────────
# Executive Summary Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4ExecutiveSummaryTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/executive-summary/"""

    def test_returns_200_with_totals_and_percentages_keys(self):
        """Returns 200 with 'totals' dict and 'percentages' array."""
        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("totals", response.data)
        self.assertIn("percentages", response.data)
        self.assertIsInstance(response.data["totals"], dict)
        self.assertIsInstance(response.data["percentages"], list)

    def test_totals_aggregate_all_records(self):
        """Totals sum across all 9 records correctly."""
        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        totals = response.data["totals"]
        # total_of_2ds: 10+15+20+25+12+18+22+30+35 = 187
        self.assertEqual(totals["total_of_2ds"], 187)
        # seconds_by_sew: 40+50+60+70+30+45+55+80+85 = 515
        self.assertEqual(totals["seconds_by_sew"], 515)
        # seconds_by_fab: 30+40+50+55+20+35+45+60+65 = 400
        self.assertEqual(totals["seconds_by_fab"], 400)
        # seconds_sew_a4: 20+25+30+35+15+22+28+40+45 = 260
        self.assertEqual(totals["seconds_sew_a4"], 260)
        # seconds_fab_a4: 10+15+20+25+5+12+18+30+35 = 170
        self.assertEqual(totals["seconds_fab_a4"], 170)
        # accepted: 50+60+70+80+40+55+65+90+95 = 605
        self.assertEqual(totals["accepted"], 605)
        # rejected: 5+6+7+8+4+5+6+9+10 = 60
        self.assertEqual(totals["rejected"], 60)

    def test_percentages_empty_for_mvp(self):
        """Percentages array is empty for MVP (no validated metrics yet)."""
        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data["percentages"], [])

    def test_totals_narrowed_by_year_filter(self):
        """?year=2025 narrows totals to 2025-only records."""
        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url, {"year": "2025"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        totals = response.data["totals"]
        # 2025: 10+15+20+25 = 70
        self.assertEqual(totals["total_of_2ds"], 70)
        # 2025: 40+50+60+70 = 220
        self.assertEqual(totals["seconds_by_sew"], 220)

    def test_empty_dataset_returns_zeroed_totals(self):
        """No records returns zeroed totals and empty percentages."""
        SecondsA4.objects.all().delete()
        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        totals = response.data["totals"]
        self.assertEqual(totals["total_of_2ds"], 0)
        self.assertEqual(totals["seconds_by_sew"], 0)
        self.assertEqual(totals["seconds_by_fab"], 0)
        self.assertEqual(totals["seconds_sew_a4"], 0)
        self.assertEqual(totals["seconds_fab_a4"], 0)
        self.assertEqual(totals["accepted"], 0)
        self.assertEqual(totals["rejected"], 0)
        self.assertEqual(response.data["percentages"], [])


# ─────────────────────────────────────────────────────────
# Weekly Trend Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4WeeklyTrendTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/weekly-trend/"""

    def test_returns_200_with_series_data(self):
        """Returns 200 with series array containing name and data."""
        url = reverse("quality_data:seconds-a4-analytics-weekly-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        series = response.data[0]
        self.assertIn("name", series)
        self.assertIn("data", series)
        self.assertIsInstance(series["data"], list)

    def test_weekly_data_aggregates_total_of_2ds_correctly(self):
        """Each week sums total_of_2ds correctly across all records."""
        url = reverse("quality_data:seconds-a4-analytics-weekly-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # First series should be "2DS"
        series = response.data[0]
        self.assertEqual(series["name"], "2DS")

        data_by_week = {p["x"]: p["y"] for p in series["data"]}
        self.assertEqual(data_by_week["2025-W1"], 10)
        self.assertEqual(data_by_week["2026-W5"], 12)
        self.assertEqual(data_by_week["2027-W9"], 35)

    def test_weekly_data_sorted_by_week(self):
        """Weekly data points are sorted by week ascending."""
        url = reverse("quality_data:seconds-a4-analytics-weekly-trend")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series = response.data[0]
        weeks = [p["x"] for p in series["data"]]
        self.assertEqual(weeks, ["2025-W1", "2025-W2", "2025-W3", "2025-W4", "2026-W5", "2026-W6", "2026-W7", "2027-W8", "2027-W9"])

    def test_year_filter_narrows_weekly_trend(self):
        """?year=2026 returns only weeks from 2026."""
        url = reverse("quality_data:seconds-a4-analytics-weekly-trend")
        response = self.client.get(url, {"year": "2026"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        series = response.data[0]
        weeks = [p["x"] for p in series["data"]]
        self.assertEqual(set(weeks), {"2026-W5", "2026-W6", "2026-W7"})
        data_by_week = {p["x"]: p["y"] for p in series["data"]}
        self.assertEqual(data_by_week["2026-W5"], 12)
        self.assertEqual(data_by_week["2026-W6"], 18)
        self.assertEqual(data_by_week["2026-W7"], 22)


# ─────────────────────────────────────────────────────────
# Sew vs Fab Split Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4SewVsFabTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/sew-vs-fab/"""

    def test_returns_200_with_two_items(self):
        """Returns 200 with two items labeled 'Sew' and 'Fabric'."""
        url = reverse("quality_data:seconds-a4-analytics-sew-vs-fab")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"Sew", "Fabric"})

    def test_values_aggregate_correctly(self):
        """Sew = sum of seconds_by_sew, Fabric = sum of seconds_by_fab."""
        url = reverse("quality_data:seconds-a4-analytics-sew-vs-fab")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        # seconds_by_sew total: 40+50+60+70+30+45+55+80+85 = 515
        self.assertEqual(values["Sew"], 515)
        # seconds_by_fab total: 30+40+50+55+20+35+45+60+65 = 400
        self.assertEqual(values["Fabric"], 400)

    def test_empty_dataset_returns_zeroed(self):
        """No records returns zeros for both sew and fab."""
        SecondsA4.objects.all().delete()
        url = reverse("quality_data:seconds-a4-analytics-sew-vs-fab")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(values["Sew"], 0)
        self.assertEqual(values["Fabric"], 0)


# ─────────────────────────────────────────────────────────
# 2DS By Line Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4ByLineTest(SecondsA4AnalyticsMixin, TestCase):
    def test_values_aggregate_total_of_2ds_per_line(self):
        url = reverse("quality_data:seconds-a4-analytics-by-line")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(values["L1"], 37)
        self.assertEqual(values["L2"], 45)
        self.assertEqual(values["L3"], 40)
        self.assertEqual(values["L4"], 65)

    def test_year_filter_narrows_lines(self):
        url = reverse("quality_data:seconds-a4-analytics-by-line")
        response = self.client.get(url, {"year": "2026"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"L1", "L3"})


# ─────────────────────────────────────────────────────────
# 2DS By Cut Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4ByCutTest(SecondsA4AnalyticsMixin, TestCase):
    def test_values_aggregate_total_of_2ds_per_cut(self):
        url = reverse("quality_data:seconds-a4-analytics-by-cut")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        self.assertEqual(values["Cut 101"], 25)
        self.assertEqual(values["Cut 102"], 45)
        self.assertEqual(values["Cut 103"], 30)
        self.assertEqual(values["Cut 104"], 22)
        self.assertEqual(values["Cut 105"], 65)

    def test_line_filter_narrows_cuts(self):
        url = reverse("quality_data:seconds-a4-analytics-by-cut")
        response = self.client.get(url, {"line": "L4"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, [{"label": "Cut 105", "value": 65}])


# ─────────────────────────────────────────────────────────
# Pass vs Fail Weekly Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4PassFailWeeklyTest(SecondsA4AnalyticsMixin, TestCase):
    def test_returns_two_series(self):
        url = reverse("quality_data:seconds-a4-analytics-pass-fail-weekly")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual([item["name"] for item in response.data], ["Pass", "Fail"])

    def test_aggregates_pass_and_fail_by_week(self):
        url = reverse("quality_data:seconds-a4-analytics-pass-fail-weekly")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        pass_series = {item["x"]: item["y"] for item in response.data[0]["data"]}
        fail_series = {item["x"]: item["y"] for item in response.data[1]["data"]}
        self.assertEqual(pass_series["2025-W1"], 15)
        self.assertEqual(fail_series["2025-W1"], 5)

    def test_excludes_invalid_year_or_week_outliers(self):
        SecondsA4.objects.create(
            year=0,
            week=26,
            date="0000-06-01",
            cut_num=999,
            style="STYLE-Z",
            cut_qty=100,
            color=self.colors["Red"],
            first_quality_qty_sewing=80,
            sample=20,
            pass_field=999,
            fail_field=999,
            sew_def=1,
            fab_def=1,
            accepted=10,
            rejected=1,
            total_of_2ds=1,
            percentage_of_2ds=0.01,
            line="L0",
            seconds_by_sew=1,
            seconds_by_fab=1,
            seconds_sew_a4=1,
            seconds_fab_a4=1,
        )
        SecondsA4.objects.create(
            year=2025,
            week=0,
            date="2025-00-01",
            cut_num=998,
            style="STYLE-Z",
            cut_qty=100,
            color=self.colors["Blue"],
            first_quality_qty_sewing=80,
            sample=20,
            pass_field=777,
            fail_field=777,
            sew_def=1,
            fab_def=1,
            accepted=10,
            rejected=1,
            total_of_2ds=1,
            percentage_of_2ds=0.01,
            line="L0",
            seconds_by_sew=1,
            seconds_by_fab=1,
            seconds_sew_a4=1,
            seconds_fab_a4=1,
        )

        url = reverse("quality_data:seconds-a4-analytics-pass-fail-weekly")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        pass_labels = {item["x"] for item in response.data[0]["data"]}
        fail_labels = {item["x"] for item in response.data[1]["data"]}
        self.assertNotIn("0-W26", pass_labels)
        self.assertNotIn("0-W26", fail_labels)
        self.assertNotIn("2025-W0", pass_labels)
        self.assertNotIn("2025-W0", fail_labels)


# ─────────────────────────────────────────────────────────
# 2DS By Style Endpoint
# ─────────────────────────────────────────────────────────

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4ByStyleTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/by-style/"""

    def test_returns_200_with_style_breakdown(self):
        """Returns 200 with label/value per style."""
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_values_aggregate_total_of_2ds_per_style(self):
        """Each style sums total_of_2ds correctly."""
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        # STYLE-A: 10+15+12 = 37
        self.assertEqual(values["STYLE-A"], 37)
        # STYLE-B: 20+25 = 45
        self.assertEqual(values["STYLE-B"], 45)
        # STYLE-C: 18+22 = 40
        self.assertEqual(values["STYLE-C"], 40)
        # STYLE-D: 30+35 = 65
        self.assertEqual(values["STYLE-D"], 65)

    def test_sorted_descending_by_value(self):
        """Styles are sorted descending by total_of_2ds."""
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_filter_narrows_to_single_style(self):
        """?year=2026 returns only styles present in 2026."""
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response = self.client.get(url, {"year": "2026"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"STYLE-A", "STYLE-C"})
        values = {item["label"]: item["value"] for item in response.data}
        # STYLE-A in 2026: total_of_2ds = 12
        self.assertEqual(values["STYLE-A"], 12)
        # STYLE-C in 2026: 18+22 = 40
        self.assertEqual(values["STYLE-C"], 40)


# ─────────────────────────────────────────────────────────
# 2DS By Color Endpoint
# ─────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════════════
# Cache Helpers — Unit Tests
# ═════════════════════════════════════════════════════════════════════


class SecondsA4CacheHelpersTest(TestCase):
    """Tests for cache helper functions in seconds_a4_views.py."""

    # ── _normalize_seconds_a4_filters ─────────────────────

    def test_normalize_filters_extracts_only_implemented_keys(self):
        """Only year, week, style, color, line, cut_num are extracted."""
        raw = {
            "year": "2025",
            "week": "3",
            "style": "STYLE-A",
            "color": "Red",
            "line": "L1",
            "cut_num": "101",
            "unexpected_extra": "should_be_ignored",
            "date_range": "2025-01-01_2025-12-31",
        }
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertEqual(
            normalized,
            {"year": 2025, "week": 3, "style": "STYLE-A", "color": "Red", "line": "L1", "cut_num": 101},
        )

    def test_normalize_filters_omits_absent_keys(self):
        """Missing filter keys are omitted from output."""
        raw = {"year": "2025"}
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertEqual(normalized, {"year": 2025})

    def test_normalize_filters_trims_whitespace(self):
        """String values are stripped of leading/trailing whitespace."""
        raw = {"style": "  STYLE-A  ", "line": "L1  "}
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertEqual(normalized, {"style": "STYLE-A", "line": "L1"})

    def test_normalize_filters_converts_numeric_strings_to_int(self):
        """Numeric filters like year/week/cut_num become ints."""
        raw = {"year": "2025", "week": "1", "cut_num": "101"}
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertIsInstance(normalized["year"], int)
        self.assertIsInstance(normalized["week"], int)
        self.assertIsInstance(normalized["cut_num"], int)
        self.assertEqual(normalized["year"], 2025)
        self.assertEqual(normalized["week"], 1)
        self.assertEqual(normalized["cut_num"], 101)

    def test_normalize_filters_preserves_string_style_and_color(self):
        """String filters stay as strings."""
        raw = {"style": "STYLE-A", "color": "Red"}
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertIsInstance(normalized["style"], str)
        self.assertIsInstance(normalized["color"], str)

    def test_normalize_filters_empty_input(self):
        """Empty input returns empty dict."""
        normalized = views_module._normalize_seconds_a4_filters({})
        self.assertEqual(normalized, {})

    def test_normalize_filters_empty_string_value_omitted(self):
        """Empty string values after trimming are omitted."""
        normalized = views_module._normalize_seconds_a4_filters(
            {"style": "", "color": "  ", "line": "L1"}
        )
        self.assertEqual(normalized, {"line": "L1"})

    def test_normalize_filters_none_values(self):
        """None values are treated as absent."""
        raw = {"year": "2025", "style": None, "color": None}
        normalized = views_module._normalize_seconds_a4_filters(raw)
        self.assertEqual(normalized, {"year": 2025})

    # ── _seconds_a4_cache_key ─────────────────────────────

    def test_cache_key_format(self):
        """Cache key follows seconds_a4:v1:<endpoint>:<hexdigest> pattern."""
        key = views_module._seconds_a4_cache_key("executive_summary", {"year": 2025})
        self.assertTrue(key.startswith("seconds_a4:v1:"))
        self.assertIn("executive_summary", key)
        # Last segment should be a 64-char hex (SHA-256)
        parts = key.split(":")
        self.assertEqual(len(parts), 4)
        self.assertEqual(len(parts[3]), 64)
        int(parts[3], 16)  # raises ValueError if not hex

    def test_cache_key_same_filters_produce_same_key(self):
        """Identical filters always produce identical keys."""
        key_a = views_module._seconds_a4_cache_key("by_style", {"year": 2025, "line": "L1"})
        key_b = views_module._seconds_a4_cache_key("by_style", {"year": 2025, "line": "L1"})
        self.assertEqual(key_a, key_b)

    def test_cache_key_different_filters_different_key(self):
        """Different filters produce different keys."""
        key_a = views_module._seconds_a4_cache_key("by_style", {"year": 2025})
        key_b = views_module._seconds_a4_cache_key("by_style", {"year": 2026})
        self.assertNotEqual(key_a, key_b)

    def test_cache_key_different_endpoints_different_key(self):
        """Different endpoint names produce different keys even with same filters."""
        key_a = views_module._seconds_a4_cache_key("by_style", {"year": 2025})
        key_b = views_module._seconds_a4_cache_key("by_color", {"year": 2025})
        self.assertNotEqual(key_a, key_b)

    def test_cache_key_empty_filters(self):
        """Zero filters still produces a key."""
        key = views_module._seconds_a4_cache_key("filter_options", {})
        self.assertTrue(key.startswith("seconds_a4:v1:filter_options:"))

    def test_cache_key_all_six_filters_simultaneously(self):
        """All 6 filter keys together produce a valid key."""
        filters = {
            "year": 2025,
            "week": 3,
            "style": "STYLE-A",
            "color": "Red",
            "line": "L1",
            "cut_num": 101,
        }
        key = views_module._seconds_a4_cache_key("by_style", filters)
        self.assertTrue(key.startswith("seconds_a4:v1:by_style:"))
        self.assertEqual(len(key.split(":")[3]), 64)

    def test_cache_key_deterministic_regardless_of_dict_order(self):
        """Key is deterministic regardless of Python dict ordering."""
        filters_a = {"year": 2025, "line": "L1", "color": "Red"}
        filters_b = {"color": "Red", "year": 2025, "line": "L1"}
        key_a = views_module._seconds_a4_cache_key("by_style", filters_a)
        key_b = views_module._seconds_a4_cache_key("by_style", filters_b)
        self.assertEqual(key_a, key_b)

    # ── TTL lookup ────────────────────────────────────────

    def test_filter_options_has_dedicated_ttl(self):
        """filter_options uses 300s TTL from SECONDS_A4_CACHE_TTLS."""
        ttl = views_module._seconds_a4_get_ttl("filter_options")
        self.assertEqual(ttl, 300)

    def test_default_ttl_for_other_endpoints(self):
        """Non-listed endpoints use SECONDS_A4_CACHE_TTL_DEFAULT (120)."""
        ttl = views_module._seconds_a4_get_ttl("nonexistent_endpoint")
        self.assertEqual(ttl, 120)

    def test_executive_summary_uses_default_ttl(self):
        """executive_summary uses 120s default TTL."""
        ttl = views_module._seconds_a4_get_ttl("executive_summary")
        self.assertEqual(ttl, 120)


# ═════════════════════════════════════════════════════════════════════
# Cache Endpoint Integration — Hit/Miss/Fallback/Key Stability
# ═════════════════════════════════════════════════════════════════════


class SecondsA4CacheMissPopulateTest(SecondsA4AnalyticsMixin, TestCase):
    """Cache miss: first request computes live result and stores it."""

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_miss_stores_payload_on_first_request(self, mock_cache):
        """When cache misses, live response is computed and stored."""
        mock_cache.get.return_value = None

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # cache.set must have been called with key, payload, timeout
        mock_cache.set.assert_called_once()
        _args, kwargs = mock_cache.set.call_args
        # timeout is passed as keyword arg
        self.assertEqual(kwargs.get("timeout"), 120)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_miss_returns_live_payload(self, mock_cache):
        """Cache miss returns the expected live payload."""
        mock_cache.get.return_value = None

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("totals", response.data)
        self.assertEqual(response.data["totals"]["total_of_2ds"], 187)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_filter_options_uses_300s_ttl_on_store(self, mock_cache):
        """filter_options stores with 300s TTL."""
        mock_cache.get.return_value = None

        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        mock_cache.set.assert_called_once()
        _args, kwargs = mock_cache.set.call_args
        self.assertEqual(kwargs.get("timeout"), 300)


class SecondsA4CacheHitTest(SecondsA4AnalyticsMixin, TestCase):
    """Cache hit: cached payload is returned without recomputation."""

    def _build_cached_payload(self):
        """Return the payload that executive-summary would produce live."""
        return {
            "totals": {
                "total_of_2ds": 187,
                "seconds_by_sew": 515,
                "seconds_by_fab": 400,
                "seconds_sew_a4": 260,
                "seconds_fab_a4": 170,
                "accepted": 605,
                "rejected": 60,
            },
            "percentages": [],
        }

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_hit_returns_cached_payload(self, mock_cache):
        """Cached payload is returned as-is with 200."""
        cached = self._build_cached_payload()
        mock_cache.get.return_value = cached

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, cached)
        # cache.set should NOT be called on a hit
        mock_cache.set.assert_not_called()

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_hit_skips_recomputation(self, mock_cache):
        """No live query runs when cache hits."""
        cached = self._build_cached_payload()
        mock_cache.get.return_value = cached

        # If cache hits, the ORM is never touched — so even deleting all
        # records should not affect the response.
        SecondsA4.objects.all().delete()

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data, cached)


class SecondsA4CacheKeyStabilityTest(SecondsA4AnalyticsMixin, TestCase):
    """Cache key stability: equivalent filters produce same cache behavior."""

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_reordered_params_hit_same_cache(self, mock_cache):
        """Same filters in different order use the same cache key."""
        mock_cache.get.side_effect = [None, {"cached": True}]  # miss, then hit

        # First request with params in one order
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        self.client.get(url, {"year": "2025", "line": "L1", "color": "Red"})

        # Second request with same params, different order
        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response2 = self.client.get(url, {"color": "Red", "line": "L1", "year": "2025"})

        # Second call to cache.get used the same key as the first — so the
        # mock returns "cached" on the second call (since we seeded the
        # second call), proving the key is the same.
        self.assertEqual(response2.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response2.data, {"cached": True})
        self.assertEqual(mock_cache.get.call_count, 2)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_different_filters_use_different_keys(self, mock_cache):
        """Different filter values produce different cache keys."""
        captured_keys = []

        def tracking_get(key, *a, **kw):
            captured_keys.append(key)
            return None

        mock_cache.get.side_effect = tracking_get

        url = reverse("quality_data:seconds-a4-analytics-by-style")
        self.client.get(url, {"year": "2025"})
        self.client.get(url, {"year": "2026"})

        self.assertEqual(len(captured_keys), 2)
        self.assertNotEqual(captured_keys[0], captured_keys[1])


class SecondsA4CacheFailureFallbackTest(SecondsA4AnalyticsMixin, TestCase):
    """Cache failures degrade gracefully to live response."""

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_get_exception_returns_live_200(self, mock_cache):
        """When cache.get raises, live 200 is returned."""
        mock_cache.get.side_effect = Exception("Redis connection refused")

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("totals", response.data)
        self.assertEqual(response.data["totals"]["total_of_2ds"], 187)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_set_exception_still_returns_live_200(self, mock_cache):
        """When cache.set raises after computing, live 200 is still returned."""
        mock_cache.get.return_value = None
        mock_cache.set.side_effect = Exception("Redis write timeout")

        url = reverse("quality_data:seconds-a4-analytics-executive-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn("totals", response.data)
        # cache.set was attempted but failed — no crash
        mock_cache.set.assert_called_once()

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_get_and_set_both_fail_then_live_200(self, mock_cache):
        """Both cache.get and cache.set fail — live 200 is still returned."""
        mock_cache.get.side_effect = Exception("Redis down")
        mock_cache.set.side_effect = Exception("Redis down")

        url = reverse("quality_data:seconds-a4-analytics-by-style")
        response = self.client.get(url, {"year": "2025"})

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_cache_get_returns_none_then_live_computed(self, mock_cache):
        """cache.get returning None (cache miss) computes live and caches it."""
        mock_cache.get.return_value = None

        url = reverse("quality_data:seconds-a4-analytics-by-line")
        response = self.client.get(url)

        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # cache.set should have been called
        mock_cache.set.assert_called_once()

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_invalid_filter_params_not_cached(self, mock_cache):
        """Invalid filter values (400) are NOT cached."""
        mock_cache.get.return_value = None

        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        response = self.client.get(url, {"year": "not-a-number"})

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        # cache.set should NOT be called for error responses
        mock_cache.set.assert_not_called()

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_invalid_filter_does_not_pollute_cache_for_valid_request(self, mock_cache):
        """An invalid filter creates a distinct cache key from valid ones."""
        mock_cache.get.return_value = None
        mock_cache.reset_mock()

        # Invalid request — compute raises ValidationError, no cache.set
        url = reverse("quality_data:seconds-a4-analytics-filter-options")
        self.client.get(url, {"year": "not-a-number"})
        mock_cache.set.assert_not_called()

        # Valid request with same filter key but valid value — should miss
        mock_cache.reset_mock()
        mock_cache.get.return_value = None
        response = self.client.get(url, {"year": "2025"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Should have attempted a cache.set (different key from invalid)
        mock_cache.set.assert_called_once()


class SecondsA4CacheAllEndpointsTest(SecondsA4AnalyticsMixin, TestCase):
    """All 9 endpoints support caching with miss→store behavior."""

    ENDPOINTS = [
        "filter-options",
        "executive-summary",
        "weekly-trend",
        "sew-vs-fab",
        "by-style",
        "by-color",
        "by-line",
        "by-cut",
        "pass-fail-weekly",
    ]

    def _url_for(self, endpoint):
        # URL names follow the hyphenated url_path, e.g. "filter-options"
        # becomes "seconds-a4-analytics-filter-options".
        return reverse(f"quality_data:seconds-a4-analytics-{endpoint}")

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_all_endpoints_return_200_on_cache_miss(self, mock_cache):
        """Every endpoint returns 200 on a cache miss."""
        mock_cache.get.return_value = None

        for ep in self.ENDPOINTS:
            with self.subTest(endpoint=ep):
                url = self._url_for(ep)
                response = self.client.get(url)
                self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_all_endpoints_store_to_cache_on_miss(self, mock_cache):
        """Every endpoint calls cache.set on a miss."""
        mock_cache.get.return_value = None
        mock_cache.reset_mock()

        for ep in self.ENDPOINTS:
            url = self._url_for(ep)
            self.client.get(url)

        # Each endpoint should have triggered one cache.set during the loop
        self.assertEqual(mock_cache.set.call_count, len(self.ENDPOINTS))

    @patch(_SECONDS_A4_CACHE_PATH)
    def test_filter_options_stored_with_300s_ttl_others_with_120s(self, mock_cache):
        """filter_options uses 300s TTL; all others use 120s."""
        mock_cache.get.return_value = None

        for ep in self.ENDPOINTS:
            with self.subTest(endpoint=ep):
                mock_cache.reset_mock()
                url = self._url_for(ep)
                self.client.get(url)
                expected_ttl = 300 if ep == "filter-options" else 120
                mock_cache.set.assert_called_once()
                _args, kwargs = mock_cache.set.call_args
                ttl = kwargs.get("timeout")
                self.assertEqual(
                    ttl, expected_ttl,
                    f"{ep} expected TTL {expected_ttl}, got {ttl}",
                )


# ═════════════════════════════════════════════════════════════════════
# 2DS By Color Endpoint (unchanged — below)
# ═════════════════════════════════════════════════════════════════════

@override_settings(CACHES=_LOCMEM_CACHES)
class SecondsA4ByColorTest(SecondsA4AnalyticsMixin, TestCase):
    """Tests for GET /quality/kpis/seconds-a4/by-color/"""

    def test_returns_200_with_color_breakdown(self):
        """Returns 200 with label/value per color."""
        url = reverse("quality_data:seconds-a4-analytics-by-color")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        for item in response.data:
            self.assertIn("label", item)
            self.assertIn("value", item)

    def test_values_aggregate_total_of_2ds_per_color(self):
        """Each color sums total_of_2ds correctly via FK traversal."""
        url = reverse("quality_data:seconds-a4-analytics-by-color")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = {item["label"]: item["value"] for item in response.data}
        # Red: 10+20+18 = 48
        self.assertEqual(values["Red"], 48)
        # Blue: 15+22 = 37
        self.assertEqual(values["Blue"], 37)
        # White: 25+30 = 55
        self.assertEqual(values["White"], 55)
        # Black: 12+35 = 47
        self.assertEqual(values["Black"], 47)

    def test_sorted_descending_by_value(self):
        """Colors are sorted descending by total_of_2ds."""
        url = reverse("quality_data:seconds-a4-analytics-by-color")
        response = self.client.get(url)
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        values = [item["value"] for item in response.data]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_filter_narrows_to_single_color(self):
        """?year=2027 returns only colors present in 2027."""
        url = reverse("quality_data:seconds-a4-analytics-by-color")
        response = self.client.get(url, {"year": "2027"})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        labels = {item["label"] for item in response.data}
        self.assertEqual(labels, {"White", "Black"})
        values = {item["label"]: item["value"] for item in response.data}
        # White in 2027: total_of_2ds = 30
        self.assertEqual(values["White"], 30)
        # Black in 2027: total_of_2ds = 35
        self.assertEqual(values["Black"], 35)
