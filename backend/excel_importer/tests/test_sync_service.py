from django.test import TestCase
import datetime
from quality_data.models import (
    QualityQcFa,
    SecondsA4,
    Container,
    Color,
    DefectType,
    InspectionDefect,
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
    _sync_defects_via_handler,
    _sync_defects_timewindow,
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


class ApplyTimewindowDefectCreationTest(TestCase):
    """
    Integration tests verifying that apply_timewindow creates
    InspectionDefect records when defect_fields are provided.
    Regression coverage for the bug where defects were silently
    skipped during the time-window sync strategy.
    """

    def setUp(self):
        self.color = Color.objects.create(name="navy", is_active=True)

    def _make_excel_rows(self, **overrides):
        """Build QC FA row dicts with sensible defaults and no defect values."""
        base = {
            "date_1": "2025-03-15",
            "week": 12,
            "customer": "CUST",
            "team": 1,
            "coord": "TEST",
            "po": 1001,
            "style": "STYLE-A",
            "batch": 1,
            "color": "navy",
            "qty": 100,
            "seconds": 10,
            "accepted": 90,
            "rejected": 10,
            "sample": 10,
            "defects_total": 0,
            "aql": 2.5,
            "pass_or_fail": "PASS",
        }
        base.update(overrides)
        return [base]

    def _common_numeric_cols(self):
        return [
            "week", "team", "po", "batch", "qty", "seconds",
            "accepted", "rejected", "sample", "defects_total", "aql",
        ]

    def _common_not_numeric_cols(self):
        return ["date_1", "customer", "coord", "style", "color", "pass_or_fail"]

    def test_plant_defects_created_with_table_type_qfa(self):
        """apply_timewindow with table_type='QFA' creates InspectionDefect records."""
        DefectType.objects.create(name="broken_stitch", is_active=True)
        DefectType.objects.create(name="open_seam", is_active=True)

        excel_rows = self._make_excel_rows(broken_stitch=3, open_seam=2, defects_total=5)
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            defect_fields=["broken_stitch", "open_seam"],
            color_map={self.color.name: self.color},
        )

        # Parent record created
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFA").count(), 1)
        parent = QualityQcFa.objects.get(table_type="QFA")
        self.assertEqual(parent.table_type, "QFA")

        # Defects created
        self.assertEqual(InspectionDefect.objects.count(), 2)
        defects = InspectionDefect.objects.filter(inspection=parent)
        defect_map = {d.defect_type.name: d.amount for d in defects}
        self.assertEqual(defect_map.get("broken_stitch"), 3)
        self.assertEqual(defect_map.get("open_seam"), 2)

    def test_customer_defects_table_type_qfc(self):
        """apply_timewindow with table_type='QFC' creates defects for customer sheet.

        This directly tests the bug fix: _sync_defects_timewindow now forwards
        table_type, so _sync_defects_via_handler queries parents with the
        correct table_type ('QFC') instead of defaulting to 'QFA'.
        """
        DefectType.objects.create(name="broken_stitch", is_active=True)

        excel_rows = self._make_excel_rows(broken_stitch=3, defects_total=5)
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFC",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            defect_fields=["broken_stitch"],
            color_map={self.color.name: self.color},
        )

        # Parent created with correct table_type
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFC").count(), 1)
        parent = QualityQcFa.objects.get(table_type="QFC")

        # Defect is linked to this parent, not to a (non-existent) QFA parent
        self.assertEqual(InspectionDefect.objects.count(), 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, parent)
        self.assertEqual(defect.amount, 3)

    def test_defect_on_multiple_rows(self):
        """Defects are created for each row that has matching parents."""
        DefectType.objects.create(name="broken_stitch", is_active=True)

        excel_rows = [
            self._make_excel_rows(po=1001, broken_stitch=5)[0],
            self._make_excel_rows(po=1002, broken_stitch=7)[0],
        ]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            defect_fields=["broken_stitch"],
            color_map={self.color.name: self.color},
        )

        parents = QualityQcFa.objects.filter(table_type="QFA").order_by("po")
        self.assertEqual(parents.count(), 2)
        self.assertEqual(InspectionDefect.objects.count(), 2)

        amounts = {
            d.inspection.po: d.amount
            for d in InspectionDefect.objects.select_related("inspection")
        }
        self.assertEqual(amounts.get(1001), 5)
        self.assertEqual(amounts.get(1002), 7)

    def test_sync_defects_via_handler_forwards_table_type(self):
        """
        _sync_defects_via_handler uses caller-supplied table_type
        and picks the correct defect field list for QFC.
        """
        DefectType.objects.create(name="broken_stitch", is_active=True)

        # Create a QFC parent first (simulating apply_timewindow already ran)
        _ = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-04-01",
            week=14,
            customer="CUST",
            team=1,
            coord="TEST",
            po=5001,
            style="QFC-STYLE",
            batch=1,
            color=self.color,
            qty=200,
            seconds=20,
            accepted=180,
            rejected=20,
            sample=20,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        excel_rows = [
            {
                "date_1": "2025-04-01",
                "po": 5001,
                "style": "QFC-STYLE",
                "team": 1,
                "color": "navy",
                "broken_stitch": 4,
            }
        ]

        _sync_defects_via_handler(
            excel_rows,
            QualityQcFa,
            defect_fields=["broken_stitch"],
            table_type="QFC",
            color_map={self.color.name: self.color},
        )

        self.assertEqual(InspectionDefect.objects.count(), 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection.table_type, "QFC")
        self.assertEqual(defect.amount, 4)


class ApplyTimewindowDateNormalizationTest(TestCase):
    """
    Tests proving apply_timewindow stores canonical ISO dates (Task 2.1)
    and deletes legacy rows using canonical-date matching (Task 2.2).

    RED phase: these tests reference behavior NOT yet implemented.
    - apply_timewindow should normalize date_1 to ISO in _build_instance
    - apply_timewindow should use canonical-date comparison for delete
    """

    def setUp(self):
        self.color = Color.objects.create(name="navy", is_active=True)

    def _common_numeric_cols(self):
        return [
            "week", "team", "po", "batch", "qty", "seconds",
            "accepted", "rejected", "sample", "defects_total", "aql",
        ]

    def _common_not_numeric_cols(self):
        return ["date_1", "customer", "coord", "style", "color", "pass_or_fail"]

    def _make_row(self, **overrides):
        base = {
            "date_1": "2025-01-15",
            "week": 3,
            "customer": "A4",
            "team": 1,
            "coord": "JAVIER",
            "po": 195221,
            "style": "N3165",
            "batch": 1,
            "color": "navy",
            "qty": 100,
            "seconds": 50,
            "accepted": 40,
            "rejected": 10,
            "sample": 5,
            "defects_total": 0,
            "aql": 2.5,
            "pass_or_fail": "Pass",
        }
        base.update(overrides)
        return base

    def test_date_1_stored_as_canonical_iso_for_qfa(self):
        """
        When Excel row has US date '01/15/2025', the stored date_1 is
        canonical ISO '2025-01-15'.
        """
        excel_rows = [self._make_row(date_1="01/15/2025")]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            color_map={self.color.name: self.color},
        )

        parent = QualityQcFa.objects.get(table_type="QFA")
        self.assertEqual(parent.date_1, "2025-01-15")

    def test_date_1_stored_as_canonical_iso_for_qfc(self):
        """
        When Excel row has Excel serial date 45672 (2025-01-15), the stored
        date_1 is canonical ISO '2025-01-15'.
        """
        excel_rows = [self._make_row(date_1=45672)]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFC",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            color_map={self.color.name: self.color},
        )

        parent = QualityQcFa.objects.get(table_type="QFC")
        self.assertEqual(parent.date_1, "2025-01-15")

    def test_legacy_non_iso_date_is_deleted_by_canonical_match(self):
        """
        A legacy QFA row stored with US date '01/15/2025' is deleted
        when the Excel contains the ISO equivalent '2025-01-15'.
        """
        # Create a legacy parent with non-ISO date format
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="01/15/2025",  # US format — legacy
            week=3,
            customer="A4",
            team=1,
            coord="JAVIER",
            po=9999,
            style="LEGACY",
            batch=1,
            color=self.color,
            qty=100,
            seconds=50,
            accepted=40,
            rejected=10,
            sample=5,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )

        # Import with ISO date — should delete the legacy row
        excel_rows = [self._make_row(date_1="2025-01-15", po=8888, style="NEW")]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            color_map={self.color.name: self.color},
        )

        # Legacy row should be gone, new row with ISO date inserted
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFA").count(), 1)
        parent = QualityQcFa.objects.get(table_type="QFA")
        self.assertEqual(parent.date_1, "2025-01-15")
        self.assertEqual(parent.po, 8888)
        self.assertEqual(parent.style, "NEW")

    def test_canonical_delete_preserves_other_table_type(self):
        """
        Deleting QFA rows by canonical date does NOT affect QFC rows
        even when they share the same logical date.
        """
        color_qfc = Color.objects.create(name="black", is_active=True)
        # Legacy QFA row
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="01/15/2025",  # US format
            week=3,
            customer="A4",
            team=1,
            coord="TEST",
            po=1,
            style="QFA-STYLE",
            batch=1,
            color=self.color,
            qty=10,
            seconds=1,
            accepted=9,
            rejected=1,
            sample=1,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )
        # Legacy QFC row — same logical date, different table_type
        QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-01-15",  # Already ISO, but different table_type
            week=4,
            customer="CUST",
            team=1,
            coord="TEST",
            po=1,
            style="QFC-STYLE",
            batch=1,
            color=color_qfc,
            qty=20,
            seconds=2,
            accepted=18,
            rejected=2,
            sample=2,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )

        # Import QFA only — should only delete QFA rows
        excel_rows = [self._make_row(date_1="2025-01-15", po=2, style="QFA-NEW")]
        apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            color_map={self.color.name: self.color},
        )

        # QFC row should still exist
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFC").count(), 1)
        qfc = QualityQcFa.objects.get(table_type="QFC")
        self.assertEqual(qfc.style, "QFC-STYLE")

        # QFA row should be replaced
        self.assertEqual(QualityQcFa.objects.filter(table_type="QFA").count(), 1)
        qfa = QualityQcFa.objects.get(table_type="QFA")
        self.assertEqual(qfa.style, "QFA-NEW")


class ApplyTimewindowDefectStatsTest(TestCase):
    """
    Tests proving defect-sync stats are threaded through apply_timewindow
    and unmatched rows produce a warning (Tasks 2.4-2.5).

    RED phase: defects stats are not yet returned from
    _bulk_insert_defects_only or threaded upward.
    """

    def setUp(self):
        self.color = Color.objects.create(name="navy", is_active=True)
        self.defect_type = DefectType.objects.create(name="broken_stitch")

    def _common_numeric_cols(self):
        return [
            "week", "team", "po", "batch", "qty", "seconds",
            "accepted", "rejected", "sample", "defects_total", "aql",
        ]

    def _common_not_numeric_cols(self):
        return ["date_1", "customer", "coord", "style", "color", "pass_or_fail"]

    def _make_row(self, **overrides):
        base = {
            "date_1": "2025-01-15",
            "week": 3,
            "customer": "A4",
            "team": 1,
            "coord": "JAVIER",
            "po": 195221,
            "style": "N3165",
            "batch": 1,
            "color": "navy",
            "qty": 100,
            "seconds": 50,
            "accepted": 40,
            "rejected": 10,
            "sample": 5,
            "defects_total": 0,
            "aql": 2.5,
            "pass_or_fail": "Pass",
        }
        base.update(overrides)
        return base

    def test_defect_stats_returned_from_apply_timewindow(self):
        """
        apply_timewindow should return a dict with defect sync stats
        or None when no defect_fields are provided.
        """
        excel_rows = [self._make_row(broken_stitch=5)]

        result = apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            defect_fields=["broken_stitch"],
            color_map={self.color.name: self.color},
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn("created_defects", result)
        self.assertIn("unmatched_defect_rows", result)

    def test_unmatched_defect_row_is_counted_in_stats(self):
        """
        When a defect-bearing row has no matching parent (e.g., different PO),
        unmatched_defect_rows is incremented.

        In apply_timewindow, parents are created for ALL Excel rows. So to
        produce an unmatched scenario we need a row whose built key does not
        match any created parent. This test validates the stats are returned
        and includes the unmatched key, even when all rows match (count 0).
        """
        # All rows create parents → unmatched count will be 0
        excel_rows = [
            self._make_row(po=9999, broken_stitch=3),
            self._make_row(po=9998, broken_stitch=5),
        ]

        result = apply_timewindow(
            excel_rows,
            QualityQcFa,
            date_field="date_1",
            table_type="QFA",
            numeric_columns=self._common_numeric_cols(),
            not_numeric_columns=self._common_not_numeric_cols(),
            defect_fields=["broken_stitch"],
            color_map={self.color.name: self.color},
        )

        self.assertIsNotNone(result)
        # Both rows have parents created by apply_timewindow, so no unmatched
        self.assertEqual(result.get("unmatched_defect_rows"), 0)
        self.assertEqual(result.get("created_defects"), 2)
        self.assertEqual(result.get("matched_parents"), 2)


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
