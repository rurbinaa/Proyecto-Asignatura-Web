"""
Tests for handler_service bulk insert functions, specifically the defects-only path.
"""
import io
import datetime
from django.test import TestCase
from quality_data.models import (
    Color,
    Container,
    ContainerDefectType,
    ContainerInspectionDefect,
    DefectType,
    QualityQcFa,
    InspectionDefect,
)
from excel_importer.handler_service import (
    _bulk_insert_defects_only,
    bulk_insert_container,
    load_and_clean,
    load_pivot_range,
    _normalize_defects_fields,
    _truncate_charfields,
)
from excel_importer.sheet_configs import CONTAINER_REMAP, CONTAINER_NOT_NUMERIC_COLUMNS
from quality_data.models import QualityQcFa as QfaModel


class BulkInsertDefectsOnlyTest(TestCase):
    """Tests for _bulk_insert_defects_only function."""

    def setUp(self):
        self.color = Color.objects.create(name="red", is_active=True)
        self.defect_type = DefectType.objects.create(name="sew_def")

    def test_insert_new_defects(self):
        """New InspectionDefect records are created when no duplicates exist."""
        # Create parent QualityQcFa
        quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=3,
            customer="A4",
            team=1,
            coord="JAVIER",
            po=195221,
            style="N3165",
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

        df_data = [
            {
                "date_1": "2025-01-15",
                "po": 195221,
                "style": "N3165",
                "team": 1,
                "color": "red",
                "sew_def": 5,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        _bulk_insert_defects_only(df, ["sew_def"], "QFA")

        self.assertEqual(InspectionDefect.objects.count(), 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, quality)
        self.assertEqual(defect.defect_type, self.defect_type)
        self.assertEqual(defect.amount, 5)

    def test_duplicate_defects_ignored(self):
        """Duplicate (inspection, defect_type) pairs are ignored without crashing."""
        # Create parent QualityQcFa
        quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=3,
            customer="A4",
            team=1,
            coord="JAVIER",
            po=195221,
            style="N3165",
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

        # Create existing InspectionDefect with same (inspection, defect_type)
        InspectionDefect.objects.create(
            inspection=quality,
            defect_type=self.defect_type,
            amount=3,
        )

        # Try to insert duplicate via _bulk_insert_defects_only
        df_data = [
            {
                "date_1": "2025-01-15",
                "po": 195221,
                "style": "N3165",
                "team": 1,
                "color": "red",
                "sew_def": 5,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        # This should NOT raise IntegrityError - duplicates should be ignored
        _bulk_insert_defects_only(df, ["sew_def"], "QFA")

        # Only one record should exist (the original, not the duplicate)
        self.assertEqual(InspectionDefect.objects.count(), 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.amount, 3)  # Original amount preserved

    def test_multiple_defects_same_inspection(self):
        """Multiple different defect types for same inspection are all created."""
        _defect_type2 = DefectType.objects.create(name="fab_def")
        _quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=3,
            customer="A4",
            team=1,
            coord="JAVIER",
            po=195221,
            style="N3165",
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

        df_data = [
            {
                "date_1": "2025-01-15",
                "po": 195221,
                "style": "N3165",
                "team": 1,
                "color": "red",
                "sew_def": 5,
                "fab_def": 2,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        _bulk_insert_defects_only(df, ["sew_def", "fab_def"], "QFA")

        self.assertEqual(InspectionDefect.objects.count(), 2)
        defects = InspectionDefect.objects.all()
        amounts = {d.defect_type.name: d.amount for d in defects}
        self.assertEqual(amounts.get("sew_def"), 5)
        self.assertEqual(amounts.get("fab_def"), 2)

    def test_missing_parent_skipped(self):
        """Rows with no matching parent QualityQcFa are skipped silently."""
        df_data = [
            {
                "date_1": "2025-01-20",  # Different date - no parent
                "po": 999999,
                "style": "NONEXISTENT",
                "team": 99,
                "color": "red",
                "sew_def": 5,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        # Should not raise - missing parents are skipped
        _bulk_insert_defects_only(df, ["sew_def"], "QFA")

        self.assertEqual(InspectionDefect.objects.count(), 0)


class BulkInsertDefectsOnlyDedupeTest(TestCase):
    """Regression test: duplicate (inspection, defect_type) should not crash."""

    def setUp(self):
        self.color = Color.objects.create(name="blue", is_active=True)
        self.defect_type = DefectType.objects.create(name="test_def")

    def test_duplicate_key_no_crash_regression(self):
        """
        Regression: When confirm/apply runs on already-imported data,
        duplicate (inspection, defect_type) should not raise IntegrityError.
        This is the core bug being fixed.
        """
        # Create parent
        _quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=5,
            customer="A4",
            team=2,
            coord="TEST",
            po=123456,
            style="TEST001",
            batch=1,
            color=self.color,
            qty=50,
            seconds=25,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )

        # Insert first time
        df_data = [
            {
                "date_1": "2025-02-01",
                "po": 123456,
                "style": "TEST001",
                "team": 2,
                "color": "blue",
                "test_def": 10,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        _bulk_insert_defects_only(df, ["test_def"], "QFA")
        self.assertEqual(InspectionDefect.objects.count(), 1)

        # Insert AGAIN - this simulates re-confirming same file
        # Should NOT crash with IntegrityError
        _bulk_insert_defects_only(df, ["test_def"], "QFA")

        # Still only one record (duplicate ignored, not added)
        self.assertEqual(InspectionDefect.objects.count(), 1)

    def test_mixed_new_and_duplicate_defects_in_same_batch(self):
        """
        Scenario: A batch contains both new (inspection, defect_type) pairs AND duplicates.
        Only new records should be inserted; duplicates should be skipped.
        This proves idempotent behavior in a single execution with mixed data.
        """
        color2 = Color.objects.create(name="green", is_active=True)
        defect_type_new = DefectType.objects.create(name="new_def")

        # Create one parent for new defect
        quality_new = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-10",
            week=6,
            customer="B5",
            team=3,
            coord="TEST",
            po=654321,
            style="NEW001",
            batch=1,
            color=color2,
            qty=60,
            seconds=30,
            accepted=50,
            rejected=10,
            sample=5,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )

        # Create another parent for duplicate
        quality_dup = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-11",
            week=6,
            customer="B5",
            team=3,
            coord="TEST",
            po=654322,
            style="DUP001",
            batch=1,
            color=color2,
            qty=70,
            seconds=35,
            accepted=55,
            rejected=15,
            sample=5,
            defects_total=0,
            aql=2.5,
            pass_or_fail="Pass",
        )

        # Pre-existing defect for duplicate scenario
        InspectionDefect.objects.create(
            inspection=quality_dup,
            defect_type=self.defect_type,
            amount=5,
        )

        # Batch with: (1) new defect, (2) existing defect (duplicate)
        # Note: Each row must have all defect_fields present (NaN if not applicable)
        df_data = [
            {
                "date_1": "2025-02-10",
                "po": 654321,
                "style": "NEW001",
                "team": 3,
                "color": "green",
                "new_def": 8,  # NEW - should be inserted
                "test_def": 0,  # Not applicable for this row
            },
            {
                "date_1": "2025-02-11",
                "po": 654322,
                "style": "DUP001",
                "team": 3,
                "color": "green",
                "new_def": 0,  # Not applicable for this row
                "test_def": 10,  # DUPLICATE - should be ignored
            },
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        # Execute - should NOT raise IntegrityError
        _bulk_insert_defects_only(df, ["new_def", "test_def"], "QFA")

        # Verify: 1 new defect inserted + 1 existing (duplicate ignored)
        self.assertEqual(InspectionDefect.objects.count(), 2)

        # Check new defect was created
        new_defect = InspectionDefect.objects.filter(
            inspection=quality_new,
            defect_type=defect_type_new
        ).first()
        self.assertIsNotNone(new_defect)
        self.assertEqual(new_defect.amount, 8)

        # Check duplicate was NOT modified (original preserved)
        dup_defect = InspectionDefect.objects.filter(
            inspection=quality_dup,
            defect_type=self.defect_type
        ).first()
        self.assertEqual(dup_defect.amount, 5)  # Original value, not 10


class BulkInsertContainerTest(TestCase):
    """Tests for bulk_insert_container function."""

    def setUp(self):
        self.container_defect_type = ContainerDefectType.objects.create(name="cont_sew_def")

    def test_insert_container_no_conflict(self):
        """New Container records are created when no duplicate container_number exists."""
        df_data = [
            {
                "container_number": 1001,
                "customer": "CUST_A",
                "transfer_of_container": 5,
                "total_palette": 100,
                "total_palette_pass": 95,
                "total_palette_rejected": 5,
                "percentage_pass": 95.0,
                "percentage_reject": 5.0,
                "cont_sew_def": 5,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number"],
            ["cont_sew_def"]
        )

        self.assertEqual(Container.objects.count(), 1)
        container = Container.objects.first()
        self.assertEqual(container.container_number, 1001)

    def test_duplicate_container_number_no_crash(self):
        """
        RED TEST: Duplicate container_number should NOT raise IntegrityError.
        This is the core bug being fixed - bulk_create with conflicts should be handled.
        """
        # First, create a container
        Container.objects.create(
            container_number=1001,
            customer="CUST_A",
            transfer_of_container=5,
            total_palette=100,
            total_palette_pass=95,
            total_palette_rejected=5,
            percentage_pass=95.0,
            percentage_reject=5.0,
        )

        df_data = [
            {
                "container_number": 1001,  # Duplicate!
                "customer": "CUST_A",
                "transfer_of_container": 5,
                "total_palette": 100,
                "total_palette_pass": 95,
                "total_palette_rejected": 5,
                "percentage_pass": 95.0,
                "percentage_reject": 5.0,
                "cont_sew_def": 5,
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        # This should NOT raise IntegrityError - conflicts should be handled
        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number"],
            ["cont_sew_def"]
        )

        # Should have only one container (the original)
        self.assertEqual(Container.objects.count(), 1)

    def test_container_defects_linked_after_upsert(self):
        """
        RED TEST: ContainerInspectionDefect rows should be linked to the correct
        container after upsert, even when container_number was duplicate.
        """
        # Pre-create container
        existing_container = Container.objects.create(
            container_number=1002,
            customer="CUST_B",
            transfer_of_container=3,
            total_palette=50,
            total_palette_pass=48,
            total_palette_rejected=2,
            percentage_pass=96.0,
            percentage_reject=4.0,
        )

        df_data = [
            {
                "container_number": 1002,  # Duplicate - should upsert
                "customer": "CUST_B",
                "transfer_of_container": 3,
                "total_palette": 50,
                "total_palette_pass": 48,
                "total_palette_rejected": 2,
                "percentage_pass": 96.0,
                "percentage_reject": 4.0,
                "cont_sew_def": 10,  # New defect count
            }
        ]
        import pandas as pd
        df = pd.DataFrame(df_data)

        # Should complete without crash and link defects to correct container
        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number"],
            ["cont_sew_def"]
        )

        # Verify defect is linked to the EXISTING container, not a new one
        self.assertEqual(Container.objects.count(), 1)
        container = Container.objects.first()
        self.assertEqual(container.container_number, 1002)

        # Verify defect was created and linked correctly
        self.assertEqual(ContainerInspectionDefect.objects.count(), 1)
        defect = ContainerInspectionDefect.objects.first()
        self.assertEqual(defect.container, existing_container)
        self.assertEqual(defect.amount, 10)

    def test_reimport_updates_container_date_when_valid_date_is_present(self):
        Container.objects.create(
            container_number=2001,
            customer="CUST_DATE",
            transfer_of_container=1,
            total_palette=10,
            total_palette_pass=9,
            total_palette_rejected=1,
            percentage_pass=90.0,
            percentage_reject=10.0,
            date=datetime.date(2025, 1, 10),
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "container_number": 2001,
                "customer": "CUST_DATE",
                "transfer_of_container": 1,
                "total_palette": 10,
                "total_palette_pass": 9,
                "total_palette_rejected": 1,
                "percentage_pass": 90.0,
                "percentage_reject": 10.0,
                "date": "2025-02-15",
                "cont_sew_def": 0,
            }
        ])

        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number", "date"],
            ["cont_sew_def"],
        )

        container = Container.objects.get(container_number=2001)
        self.assertEqual(container.date, datetime.date(2025, 2, 15))

    def test_reimport_with_empty_date_preserves_existing_non_null_date(self):
        Container.objects.create(
            container_number=2002,
            customer="CUST_KEEP_DATE",
            transfer_of_container=1,
            total_palette=10,
            total_palette_pass=9,
            total_palette_rejected=1,
            percentage_pass=90.0,
            percentage_reject=10.0,
            date=datetime.date(2025, 3, 1),
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "container_number": 2002,
                "customer": "CUST_KEEP_DATE",
                "transfer_of_container": 2,
                "total_palette": 11,
                "total_palette_pass": 10,
                "total_palette_rejected": 1,
                "percentage_pass": 91.0,
                "percentage_reject": 9.0,
                "date": "",
                "cont_sew_def": 0,
            }
        ])

        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number", "date"],
            ["cont_sew_def"],
        )

        container = Container.objects.get(container_number=2002)
        self.assertEqual(container.date, datetime.date(2025, 3, 1))


# ─────────────────────────────────────────────────────────
# Phase 1: load_and_clean Edge Case Tests
# ─────────────────────────────────────────────────────────

class LoadAndCleanEdgeCasesTest(TestCase):
    """Edge case tests for load_and_clean function."""

    def test_load_and_clean_empty_file(self):
        """
        Empty Excel file (no data rows) returns empty DataFrame
        instead of crashing.
        """
        import pandas as pd
        # Create an empty Excel file
        df_empty = pd.DataFrame()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_empty.to_excel(writer, sheet_name="QC FA Plant", index=False)
        buffer.seek(0)

        remap_columns = {'PO': 'po'}
        numeric_columns = ['qty', 'sample']
        defeacts_fields = ['sew_def']

        df = load_and_clean(
            buffer,
            remap_columns,
            numeric_columns,
            defeacts_fields,
            "QC FA Plant",
            0,  # header at row 0
            5,
        )

        self.assertTrue(df.empty)

    def test_load_and_clean_missing_columns(self):
        """
        Missing remapped columns should be filled with default values (0 for
        numeric, ''/UNKNOWN for text) instead of crashing.
        """
        import pandas as pd
        # Excel with PO column only - load_and_clean will add missing numeric/defect columns as 0
        df_data = pd.DataFrame({'PO': [100, 200, 300]})
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_data.to_excel(writer, sheet_name="QC FA Plant", index=False)
        buffer.seek(0)

        remap_columns = {'PO': 'po'}
        numeric_columns = ['qty', 'sample']
        defeacts_fields = ['sew_def']

        df = load_and_clean(
            buffer,
            remap_columns,
            numeric_columns,
            defeacts_fields,
            "QC FA Plant",
            0,
            1,  # Only 1 column exists in the file
        )

        # Missing columns should be added with default values
        self.assertIn('po', df.columns)
        self.assertIn('qty', df.columns)
        self.assertIn('sew_def', df.columns)

    def test_load_and_clean_invalid_extension(self):
        """
        File with invalid extension (.csv, .pdf) should raise
        ValueError or BadZipFile when read as Excel.
        """
        # CSV content (not a real Excel file)
        csv_content = b"col1,col2\n1,2\n3,4"

        remap_columns = {}
        numeric_columns = []
        defeacts_fields = []

        # Test CSV content
        buffer = io.BytesIO(csv_content)
        with self.assertRaises(Exception):  # Could be ValueError, BadZipFile, or xlrd error
            load_and_clean(
                buffer,
                remap_columns,
                numeric_columns,
                defeacts_fields,
                "QC FA Plant",
                0,
                2,
            )

    def test_load_and_clean_corrupted_file(self):
        """
        Non-Excel binary content should raise an exception
        (BadZipFile, ValueError, or similar) rather than silently processing.
        """
        # Random binary content that is not a valid Excel file
        corrupted_content = b"\x00\x01\x02\x03 NOT AN EXCEL FILE \xff\xfe\xfd"

        remap_columns = {}
        numeric_columns = []
        defeacts_fields = []

        buffer = io.BytesIO(corrupted_content)
        with self.assertRaises(Exception):
            load_and_clean(
                buffer,
                remap_columns,
                numeric_columns,
                defeacts_fields,
                "QC FA Plant",
                0,
                5,
            )

    def test_container_sheet_config_maps_date_column(self):
        self.assertEqual(CONTAINER_REMAP.get("Date"), "date")
        self.assertIn("date", CONTAINER_NOT_NUMERIC_COLUMNS)


class LoadPivotRangeIOTest(TestCase):
    """Tests for load_pivot_range I/O exception handling."""

    def test_load_pivot_range_file_read_exception(self):
        """
        File read exception during upload (e.g., connection reset, timeout)
        should propagate as exception (as BadZipFile - zipfile's error handling
        converts I/O errors to BadZipFile when reading zip structure fails).
        """
        import pandas as pd
        import zipfile

        # Create a valid Excel file first
        df_data = pd.DataFrame({'col_a': [1, 2, 3], 'col_b': [4, 5, 6]})
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_data.to_excel(writer, sheet_name='Sheet1', index=False)
        buffer.seek(0)

        # Now make the file object raise an I/O error on read
        class FailingFileObj:
            def __init__(self, backing):
                self._backing = backing

            def seek(self, pos, whence=0):
                return self._backing.seek(pos, whence)

            def tell(self):
                return self._backing.tell()

            def read(self, size=-1):
                raise IOError("Connection reset by peer")

        failing_file = FailingFileObj(buffer)

        # Should raise an exception, not silently return empty DataFrame.
        # Note: zipfile converts I/O errors to BadZipFile when reading fails.
        with self.assertRaises((IOError, zipfile.BadZipFile)):
            load_pivot_range(
                failing_file,
                sheet='Sheet1',
                header_row=1,
                usecols='A:B',
                nrows=10,
            )


class NormalizeDefectsFieldsTest(TestCase):
    """Tests for _normalize_defects_fields helper."""

    def test_normalize_defects_fields_none_input(self):
        """Returns empty list when input is None."""
        result = _normalize_defects_fields(None)
        self.assertEqual(result, [])

    def test_normalize_defects_fields_zero_input(self):
        """Returns empty list when input is 0."""
        result = _normalize_defects_fields(0)
        self.assertEqual(result, [])

    def test_normalize_defects_fields_list_input(self):
        """Returns list unchanged when given a list."""
        result = _normalize_defects_fields(['sew_def', 'fab_def'])
        self.assertEqual(result, ['sew_def', 'fab_def'])


class TruncateCharFieldsTest(TestCase):
    """Tests for _truncate_charfields helper."""

    def test_truncate_charfields_under_limit(self):
        """Strings shorter than max_length are unchanged."""
        data = {'style': 'N3165', 'customer': 'ACME'}
        result = _truncate_charfields(QfaModel, data)
        self.assertEqual(result['style'], 'N3165')
        self.assertEqual(result['customer'], 'ACME')

    def test_truncate_charfields_over_limit(self):
        """Strings longer than max_length are truncated."""
        # Create a model instance to inspect field max_length
        data = {'style': 'A' * 100, 'customer': 'B' * 200}
        result = _truncate_charfields(QfaModel, data)
        # style max_length should truncate the string
        self.assertLessEqual(len(result['style']), 50)  # Approximate max_length for style
