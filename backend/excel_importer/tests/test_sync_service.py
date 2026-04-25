from django.test import TestCase
import datetime
from quality_data.models import (
    QualityQcFa,
    SecondsA4,
    Container,
    Color,
    ExcelSyncSession,
)
from excel_importer.sync_service import (
    build_seconds_a4_key,
    build_container_key,
    build_qc_fa_plant_key,
    extract_dates,
    compute_preview_upsert,
    compute_preview_timewindow,
    apply_upsert,
    apply_timewindow,
    apply_session,
    create_session_from_dataframes,
    reject_session,
)


class NaturalKeyBuilderTest(TestCase):
    """Tests for natural key builder functions."""

    def test_build_seconds_a4_key(self):
        row = {"date": "2025-01-15", "cut_num": 123, "color": "Red"}
        key = build_seconds_a4_key(row)
        self.assertEqual(key, ("2025-01-15", 123, "red"))

    def test_build_seconds_a4_key_with_whitespace(self):
        row = {"date": "2025-01-15", "cut_num": 123, "color": " Navy Blue "}
        key = build_seconds_a4_key(row)
        self.assertEqual(key, ("2025-01-15", 123, "navy_blue"))

    def test_build_container_key(self):
        row = {"container_number": 42}
        key = build_container_key(row)
        self.assertEqual(key, (42,))

    def test_build_container_key_zero(self):
        row = {"container_number": 0}
        key = build_container_key(row)
        self.assertEqual(key, (0,))

    def test_build_qc_fa_plant_key(self):
        row = {
            "date_1": "2025-01-15",
            "po": 195221,
            "style": "N3165",
            "team": 1,
            "color": "Black",
        }
        key = build_qc_fa_plant_key(row)
        self.assertEqual(key, ("2025-01-15", 195221, "N3165", 1, "black"))


class ExtractDatesTest(TestCase):
    """Tests for extract_dates utility."""

    def test_extracts_unique_dates(self):
        rows = [
            {"date_1": "2025-01-15"},
            {"date_1": "2025-01-15"},
            {"date_1": "2025-01-16"},
        ]
        dates = extract_dates(rows, "date_1")
        self.assertEqual(dates, {"2025-01-15", "2025-01-16"})

    def test_ignores_invalid_dates(self):
        rows = [
            {"date_1": "2025-01-15"},
            {"date_1": "UNKNOWN"},
            {"date_1": None},
        ]
        dates = extract_dates(rows, "date_1")
        self.assertEqual(dates, {"2025-01-15"})


class PreviewUpsertTest(TestCase):
    """Tests for compute_preview_upsert."""

    def setUp(self):
        self.color = Color.objects.create(name="red", is_active=True)

    def test_all_new_records(self):
        """When DB is empty, all Excel rows are new."""
        excel_rows = [
            {"date": "2025-01-15", "cut_num": 1, "color": "Red", "cut_qty": 100},
            {"date": "2025-01-15", "cut_num": 2, "color": "Red", "cut_qty": 200},
        ]
        preview = compute_preview_upsert(
            excel_rows,
            SecondsA4.objects.all(),
            build_seconds_a4_key,
            date_field="date",
        )
        self.assertEqual(preview["new"], 2)
        self.assertEqual(preview["modified"], 0)
        self.assertEqual(preview["unchanged"], 0)
        self.assertEqual(preview["total"], 2)

    def test_unchanged_records(self):
        """When Excel matches DB exactly, all are unchanged."""
        SecondsA4.objects.create(
            year=2025, week=3, date="2025-01-15", cut_num=1,
            style="N3165", cut_qty=100, color=self.color,
            first_quality_qty_sewing=50, sample=5,
            pass_field=45, fail_field=5, sew_def=3, fab_def=2,
            accepted=40, rejected=10, total_of_2ds=15,
            percentage_of_2ds=10.5, line="1",
            seconds_by_sew=8, seconds_by_fab=7,
            seconds_sew_a4=5.0, seconds_fab_a4=3.0,
        )
        excel_rows = [
            {"date": "2025-01-15", "cut_num": 1, "color": "Red", "cut_qty": 100},
        ]
        preview = compute_preview_upsert(
            excel_rows,
            SecondsA4.objects.all(),
            build_seconds_a4_key,
            date_field="date",
        )
        self.assertEqual(preview["new"], 0)
        self.assertEqual(preview["unchanged"], 1)

    def test_modified_records(self):
        """When Excel has same key but different values, it's modified."""
        SecondsA4.objects.create(
            year=2025, week=3, date="2025-01-15", cut_num=1,
            style="N3165", cut_qty=100, color=self.color,
            first_quality_qty_sewing=50, sample=5,
            pass_field=45, fail_field=5, sew_def=3, fab_def=2,
            accepted=40, rejected=10, total_of_2ds=15,
            percentage_of_2ds=10.5, line="1",
            seconds_by_sew=8, seconds_by_fab=7,
            seconds_sew_a4=5.0, seconds_fab_a4=3.0,
        )
        excel_rows = [
            {"date": "2025-01-15", "cut_num": 1, "color": "Red", "cut_qty": 999},
        ]
        preview = compute_preview_upsert(
            excel_rows,
            SecondsA4.objects.all(),
            build_seconds_a4_key,
            date_field="date",
        )
        self.assertEqual(preview["modified"], 1)


class PreviewTimeWindowTest(TestCase):
    """Tests for compute_preview_timewindow."""

    def test_no_existing_data(self):
        """When DB is empty, no warnings."""
        excel_rows = [
            {"date_1": "2025-01-15"},
            {"date_1": "2025-01-15"},
        ]
        preview = compute_preview_timewindow(
            excel_rows,
            QualityQcFa.objects.none(),
            date_field="date_1",
        )
        self.assertEqual(preview["total"], 2)
        self.assertEqual(preview["warnings"], [])

    def test_data_loss_warning(self):
        """When Excel has fewer rows than DB for a date, warn."""
        color = Color.objects.create(name="black", is_active=True)
        for i in range(5):
            QualityQcFa.objects.create(
                table_type="QFA", date_1="2025-01-15", week=3,
                customer="A4", team=1, coord="JAVIER",
                po=195221, style="N3165", batch=1, color=color,
                qty=100, seconds=50, accepted=40, rejected=10,
                sample=5, defects_total=0, aql=2.5, pass_or_fail="Pass",
            )

        excel_rows = [
            {"date_1": "2025-01-15"},
            {"date_1": "2025-01-15"},
        ]
        preview = compute_preview_timewindow(
            excel_rows,
            QualityQcFa.objects.filter(table_type="QFA"),
            date_field="date_1",
        )
        self.assertEqual(len(preview["warnings"]), 1)
        self.assertIn("3 existing records will be replaced", preview["warnings"][0])


class ApplyUpsertTest(TestCase):
    """Tests for apply_upsert."""

    def setUp(self):
        self.color = Color.objects.create(name="red", is_active=True)

    def test_insert_new_records(self):
        """New records are created."""
        excel_rows = [
            {"date": "2025-01-15", "cut_num": 1, "color": "Red", "cut_qty": 100},
        ]
        apply_upsert(
            excel_rows,
            SecondsA4,
            build_seconds_a4_key,
            not_numeric_columns=["date", "style", "color", "line"],
            numeric_columns=["year", "week", "cut_num", "cut_qty",
                             "first_quality_qty_sewing", "sample",
                             "pass_field", "fail_field", "sew_def", "fab_def",
                             "accepted", "rejected", "total_of_2ds",
                             "percentage_of_2ds", "seconds_by_sew",
                             "seconds_by_fab", "seconds_sew_a4", "seconds_fab_a4"],
        )
        self.assertEqual(SecondsA4.objects.count(), 1)

    def test_update_modified_records(self):
        """Existing records with different values are updated."""
        SecondsA4.objects.create(
            year=2025, week=3, date="2025-01-15", cut_num=1,
            style="N3165", cut_qty=100, color=self.color,
            first_quality_qty_sewing=50, sample=5,
            pass_field=45, fail_field=5, sew_def=3, fab_def=2,
            accepted=40, rejected=10, total_of_2ds=15,
            percentage_of_2ds=10.5, line="1",
            seconds_by_sew=8, seconds_by_fab=7,
            seconds_sew_a4=5.0, seconds_fab_a4=3.0,
        )
        excel_rows = [
            {"date": "2025-01-15", "cut_num": 1, "color": "Red", "cut_qty": 999},
        ]
        apply_upsert(
            excel_rows,
            SecondsA4,
            build_seconds_a4_key,
            not_numeric_columns=["date", "style", "color", "line"],
            numeric_columns=["year", "week", "cut_num", "cut_qty",
                             "first_quality_qty_sewing", "sample",
                             "pass_field", "fail_field", "sew_def", "fab_def",
                             "accepted", "rejected", "total_of_2ds",
                             "percentage_of_2ds", "seconds_by_sew",
                             "seconds_by_fab", "seconds_sew_a4", "seconds_fab_a4"],
        )
        obj = SecondsA4.objects.get(date="2025-01-15", cut_num=1)
        self.assertEqual(obj.cut_qty, 999)

    def test_container_upsert_dedupes_duplicate_keys_in_same_batch(self):
        """Duplicate container_number rows in one Excel batch should not crash and last row wins."""
        excel_rows = [
            {
                "container_number": 8,
                "customer": "A4",
                "transfer_of_container": 10,
                "total_palette": 20,
                "total_palette_pass": 18,
                "total_palette_rejected": 2,
                "percentage_pass": 90.0,
                "percentage_reject": 10.0,
            },
            {
                "container_number": 8,
                "customer": "A4",
                "transfer_of_container": 11,
                "total_palette": 22,
                "total_palette_pass": 20,
                "total_palette_rejected": 2,
                "percentage_pass": 90.9,
                "percentage_reject": 9.1,
            },
        ]

        apply_upsert(
            excel_rows,
            Container,
            build_container_key,
            not_numeric_columns=["customer", "container_number"],
            numeric_columns=[
                "transfer_of_container",
                "total_palette",
                "total_palette_pass",
                "total_palette_rejected",
                "percentage_pass",
                "percentage_reject",
            ],
        )

        self.assertEqual(Container.objects.count(), 1)
        obj = Container.objects.get(container_number=8)
        self.assertEqual(obj.total_palette, 22)
        self.assertEqual(obj.transfer_of_container, 11)

    def test_container_upsert_preserves_existing_date_when_reimport_date_empty(self):
        Container.objects.create(
            container_number=15,
            customer="A4",
            transfer_of_container=10,
            total_palette=20,
            total_palette_pass=18,
            total_palette_rejected=2,
            percentage_pass=90.0,
            percentage_reject=10.0,
            date=datetime.date(2025, 1, 20),
        )

        excel_rows = [
            {
                "container_number": 15,
                "customer": "A4",
                "transfer_of_container": 11,
                "total_palette": 21,
                "total_palette_pass": 19,
                "total_palette_rejected": 2,
                "percentage_pass": 90.4,
                "percentage_reject": 9.6,
                "date": "",
            }
        ]

        apply_upsert(
            excel_rows,
            Container,
            build_container_key,
            not_numeric_columns=["customer", "container_number", "date"],
            numeric_columns=[
                "transfer_of_container",
                "total_palette",
                "total_palette_pass",
                "total_palette_rejected",
                "percentage_pass",
                "percentage_reject",
            ],
        )

        obj = Container.objects.get(container_number=15)
        self.assertEqual(obj.date, datetime.date(2025, 1, 20))

    def test_container_upsert_updates_date_when_reimport_has_valid_date(self):
        Container.objects.create(
            container_number=16,
            customer="A4",
            transfer_of_container=10,
            total_palette=20,
            total_palette_pass=18,
            total_palette_rejected=2,
            percentage_pass=90.0,
            percentage_reject=10.0,
            date=datetime.date(2025, 1, 20),
        )

        excel_rows = [
            {
                "container_number": 16,
                "customer": "A4",
                "transfer_of_container": 11,
                "total_palette": 21,
                "total_palette_pass": 19,
                "total_palette_rejected": 2,
                "percentage_pass": 90.4,
                "percentage_reject": 9.6,
                "date": "2025-02-22",
            }
        ]

        apply_upsert(
            excel_rows,
            Container,
            build_container_key,
            not_numeric_columns=["customer", "container_number", "date"],
            numeric_columns=[
                "transfer_of_container",
                "total_palette",
                "total_palette_pass",
                "total_palette_rejected",
                "percentage_pass",
                "percentage_reject",
            ],
        )

        obj = Container.objects.get(container_number=16)
        self.assertEqual(obj.date, datetime.date(2025, 2, 22))


class ApplyTimeWindowTest(TestCase):
    """Tests for apply_timewindow."""

    def test_replaces_existing_data(self):
        """Existing records for matching dates are replaced."""
        color = Color.objects.create(name="black", is_active=True)
        QualityQcFa.objects.create(
            table_type="QFA", date_1="2025-01-15", week=3,
            customer="A4", team=1, coord="JAVIER",
            po=195221, style="N3165", batch=1, color=color,
            qty=100, seconds=50, accepted=40, rejected=10,
            sample=5, defects_total=0, aql=2.5, pass_or_fail="Pass",
        )

        excel_rows = [
            {
                "date_1": "2025-01-15", "week": 3, "customer": "A4",
                "team": 1, "coord": "JAVIER", "po": 999999,
                "style": "NEW", "batch": 2, "color": "Black",
                "qty": 200, "seconds": 100, "accepted": 80,
                "rejected": 20, "sample": 10, "defects_total": 5,
                "aql": 1.5, "pass_or_fail": "Pass",
            },
        ]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=["week", "team", "po", "batch", "qty", "seconds",
                             "accepted", "rejected", "sample", "defects_total", "aql"],
            not_numeric_columns=["date_1", "customer", "coord", "style",
                                 "color", "pass_or_fail"],
        )

        # Old record gone, new one exists
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFA").count(), 1)
        obj = QualityQcFa.objects.get(table_type="QFA")
        self.assertEqual(obj.po, 999999)

    def test_preserves_other_dates(self):
        """Records for dates NOT in Excel are untouched."""
        color = Color.objects.create(name="black", is_active=True)
        QualityQcFa.objects.create(
            table_type="QFA", date_1="2025-01-10", week=2,
            customer="A4", team=1, coord="JAVIER",
            po=195221, style="N3165", batch=1, color=color,
            qty=100, seconds=50, accepted=40, rejected=10,
            sample=5, defects_total=0, aql=2.5, pass_or_fail="Pass",
        )

        excel_rows = [
            {"date_1": "2025-01-15", "week": 3, "customer": "A4",
             "team": 1, "coord": "JAVIER", "po": 195221,
             "style": "N3165", "batch": 1, "color": "Black",
             "qty": 100, "seconds": 50, "accepted": 40,
             "rejected": 10, "sample": 5, "defects_total": 0,
             "aql": 2.5, "pass_or_fail": "Pass"},
        ]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=["week", "team", "po", "batch", "qty", "seconds",
                             "accepted", "rejected", "sample", "defects_total", "aql"],
            not_numeric_columns=["date_1", "customer", "coord", "style",
                                 "color", "pass_or_fail"],
        )

        # Both records exist
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFA").count(), 2)


class SessionManagementTest(TestCase):
    """Tests for session creation and rejection."""

    def test_create_session(self):
        """create_session_from_dataframes creates a pending session."""
        dataframes = {
            "qc_fa_plant": [{"date_1": "2025-01-15"}],
            "seconds_a4": [],
            "seconds_general": [],
            "qc_fa_customer": [],
            "container": [],
        }
        session = create_session_from_dataframes(dataframes)
        self.assertEqual(session.status, "pending")
        self.assertTrue(session.is_pending)
        self.assertEqual(len(session.qc_fa_plant_data), 1)

    def test_reject_session(self):
        """reject_session marks session as rejected."""
        session = ExcelSyncSession.objects.create()
        reject_session(session)
        session.refresh_from_db()
        self.assertEqual(session.status, "rejected")

    def test_apply_session_confirms(self):
        """apply_session sets status to confirmed."""
        _color = Color.objects.create(name="red", is_active=True)
        session = ExcelSyncSession.objects.create(
            seconds_a4_data=[{
                "date": "2025-01-15", "cut_num": 1, "color": "Red",
                "cut_qty": 100, "year": 2025, "week": 3, "style": "N3165",
                "first_quality_qty_sewing": 50, "sample": 5,
                "pass_field": 45, "fail_field": 5, "sew_def": 3, "fab_def": 2,
                "accepted": 40, "rejected": 10, "total_of_2ds": 15,
                "percentage_of_2ds": 10.5, "line": "1",
                "seconds_by_sew": 8, "seconds_by_fab": 7,
                "seconds_sew_a4": 5.0, "seconds_fab_a4": 3.0,
            }],
        )
        apply_session(session)
        session.refresh_from_db()
        self.assertEqual(session.status, "confirmed")

    def test_create_session_container_preview_tracks_dates_and_invalid_warnings(self):
        dataframes = {
            "qc_fa_plant": [],
            "seconds_a4": [],
            "seconds_general": [],
            "qc_fa_customer": [],
            "container": [
                {"container_number": 33, "date": "2025-02-01"},
                {"container_number": 34, "date": "INVALID-DATE"},
            ],
        }

        session = create_session_from_dataframes(dataframes)

        self.assertEqual(session.container_preview["dates"], ["2025-02-01"])
        self.assertTrue(any("container" in warning.lower() for warning in session.warnings))
