"""
Tests for handler_service bulk insert functions, specifically the defects-only path.
"""
import io
import datetime
import pandas as pd
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
    bulk_insert,
    bulk_insert_container,
    bulk_insert_seconds_a4,
    bulk_insert_seconds_general,
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

    def test_missing_color_skips_row_without_crashing(self):
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
        self.assertIsNotNone(quality)

        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "2025-01-15",
                "po": 195221,
                "style": "N3165",
                "team": 1,
                "color": "missing-color",
                "sew_def": 5,
            }
        ])

        _bulk_insert_defects_only(df, ["sew_def"], "QFA")
        self.assertEqual(InspectionDefect.objects.count(), 0)

    def test_missing_style_or_date_skips_row(self):
        QualityQcFa.objects.create(
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

        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "",
                "po": 195221,
                "style": "N3165",
                "team": 1,
                "color": "red",
                "sew_def": 5,
            },
            {
                "date_1": "2025-01-15",
                "po": 195221,
                "style": "",
                "team": 1,
                "color": "red",
                "sew_def": 5,
            },
        ])

        _bulk_insert_defects_only(df, ["sew_def"], "QFA")
        self.assertEqual(InspectionDefect.objects.count(), 0)


class BulkInsertDefectsOnlyAutoSeedTest(TestCase):
    """
    Tests that _bulk_insert_defects_only auto-creates DefectType records
    that don't exist yet, instead of silently skipping those defects.
    """

    def setUp(self):
        self.color = Color.objects.create(name="green", is_active=True)

    def test_auto_creates_missing_defect_types(self):
        """DefectType records are auto-seeded when they don't exist in DB."""
        # Pre-condition: no DefectType named "auto_def" exists
        self.assertEqual(DefectType.objects.filter(name="auto_def").count(), 0)

        # Create parent QualityQcFa
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-01",
            week=10,
            customer="CUST",
            team=1,
            coord="TEST",
            po=9999,
            style="AUTO",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=0,
            aql=2.5,
            pass_or_fail="PASS",
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "2025-03-01",
                "po": 9999,
                "style": "AUTO",
                "team": 1,
                "color": "green",
                "auto_def": 7,
            }
        ])

        # Call with a defect field that has NO pre-existing DefectType
        _bulk_insert_defects_only(df, ["auto_def"], "QFA")

        # DefectType should now exist
        self.assertEqual(DefectType.objects.filter(name="auto_def").count(), 1)

        # InspectionDefect should have been created
        self.assertEqual(InspectionDefect.objects.count(), 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.defect_type.name, "auto_def")
        self.assertEqual(defect.amount, 7)

    def test_auto_seed_idempotent(self):
        """Calling twice with the same missing defect field is idempotent."""
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-03-02",
            week=10,
            customer="CUST",
            team=1,
            coord="TEST",
            po=8888,
            style="IDEM",
            batch=1,
            color=self.color,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=0,
            aql=2.0,
            pass_or_fail="PASS",
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "2025-03-02",
                "po": 8888,
                "style": "IDEM",
                "team": 1,
                "color": "green",
                "idem_def": 3,
            }
        ])

        # First call — auto-creates DefectType
        _bulk_insert_defects_only(df, ["idem_def"], "QFA")
        self.assertEqual(DefectType.objects.filter(name="idem_def").count(), 1)
        self.assertEqual(InspectionDefect.objects.count(), 1)

        # Second call — should NOT duplicate DefectType, should NOT crash
        _bulk_insert_defects_only(df, ["idem_def"], "QFA")
        self.assertEqual(DefectType.objects.filter(name="idem_def").count(), 1)


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

    def test_reimport_with_invalid_date_preserves_existing_non_null_date(self):
        Container.objects.create(
            container_number=2003,
            customer="CUST_KEEP_INVALID",
            transfer_of_container=1,
            total_palette=10,
            total_palette_pass=9,
            total_palette_rejected=1,
            percentage_pass=90.0,
            percentage_reject=10.0,
            date=datetime.date(2025, 4, 2),
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "container_number": 2003,
                "customer": "CUST_KEEP_INVALID",
                "transfer_of_container": 2,
                "total_palette": 11,
                "total_palette_pass": 10,
                "total_palette_rejected": 1,
                "percentage_pass": 91.0,
                "percentage_reject": 9.0,
                "date": "NOT_A_DATE",
                "cont_sew_def": 0,
            }
        ])

        bulk_insert_container(
            df,
            ["transfer_of_container", "total_palette", "total_palette_pass", "total_palette_rejected", "percentage_pass", "percentage_reject"],
            ["customer", "container_number", "date"],
            ["cont_sew_def"],
        )

        container = Container.objects.get(container_number=2003)
        self.assertEqual(container.date, datetime.date(2025, 4, 2))


class BulkInsertCoverageTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="teal", is_active=True)
        self.defect_type = DefectType.objects.create(name="sew_def")

    def test_bulk_insert_returns_when_dataframe_is_empty(self):
        import pandas as pd
        df = pd.DataFrame([])

        bulk_insert(
            df,
            numeric_columns=["qty", "seconds"],
            not_numeric_columns=["customer", "style", "date_1", "table_type", "coord", "pass_or_fail"],
            defeacts_fields=["sew_def"],
            table_type="QFA",
        )

        self.assertEqual(QualityQcFa.objects.count(), 0)

    def test_bulk_insert_creates_quality_and_defects(self):
        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "2025-01-15",
                "week": 3,
                "customer": "A4",
                "team": 1,
                "coord": "JAVIER",
                "po": 195221,
                "style": "N3165",
                "batch": 1,
                "color": "teal",
                "qty": 100,
                "seconds": 50,
                "accepted": 40,
                "rejected": 10,
                "sample": 5,
                "defects_total": 5,
                "aql": 2.5,
                "pass_or_fail": "PASS",
                "sew_def": 3,
            }
        ])

        bulk_insert(
            df,
            numeric_columns=["week", "team", "po", "batch", "qty", "seconds", "accepted", "rejected", "sample", "defects_total", "aql"],
            not_numeric_columns=["date_1", "customer", "coord", "style", "pass_or_fail"],
            defeacts_fields=["sew_def"],
            table_type="QFA",
        )

        self.assertEqual(QualityQcFa.objects.count(), 1)
        created = QualityQcFa.objects.first()
        self.assertEqual(created.table_type, "QFA")
        self.assertEqual(created.color.name, "teal")
        self.assertEqual(InspectionDefect.objects.count(), 1)
        self.assertEqual(InspectionDefect.objects.first().amount, 3)

    def test_bulk_insert_defects_only_uses_existing_parents(self):
        quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-02-01",
            week=1,
            customer="A4",
            team=1,
            coord="TEST",
            po=123,
            style="STYLE",
            batch=1,
            color=self.color,
            qty=10,
            seconds=2,
            accepted=8,
            rejected=2,
            sample=2,
            defects_total=0,
            aql=1.0,
            pass_or_fail="PASS",
        )

        import pandas as pd
        df = pd.DataFrame([
            {
                "date_1": "2025-02-01",
                "po": 123,
                "style": "STYLE",
                "team": 1,
                "color": "teal",
                "sew_def": 4,
            }
        ])

        bulk_insert(
            df,
            numeric_columns=[],
            not_numeric_columns=[],
            defeacts_fields=["sew_def"],
            table_type="QFA",
            defects_only=True,
        )

        defect = InspectionDefect.objects.get()
        self.assertEqual(defect.inspection, quality)
        self.assertEqual(defect.amount, 4)


class BulkInsertSecondsCoverageTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="orange", is_active=True)

    def test_bulk_insert_seconds_a4_noop_with_empty_dataframe(self):
        import pandas as pd
        from quality_data.models import SecondsA4

        bulk_insert_seconds_a4(pd.DataFrame([]), ["year"], ["date"])
        self.assertEqual(SecondsA4.objects.count(), 0)

    def test_bulk_insert_seconds_general_noop_with_empty_dataframe(self):
        import pandas as pd
        from quality_data.models import SecondsGeneral

        bulk_insert_seconds_general(pd.DataFrame([]), ["week"], ["date"])
        self.assertEqual(SecondsGeneral.objects.count(), 0)

    def test_bulk_insert_seconds_a4_creates_records(self):
        import pandas as pd
        df = pd.DataFrame([
            {
                "year": 2025,
                "week": 10,
                "date": "2025-03-01",
                "cut_num": 10,
                "style": "STYLE-A",
                "cut_qty": 200,
                "color": "orange",
                "first_quality_qty_sewing": 150,
                "sample": 10,
                "pass_field": 140,
                "fail_field": 10,
                "sew_def": 4,
                "fab_def": 6,
                "accepted": 180,
                "rejected": 20,
                "total_of_2ds": 5,
                "percentage_of_2ds": 2.5,
                "line": "L1",
                "seconds_by_sew": 3,
                "seconds_by_fab": 2,
                "seconds_sew_a4": 1,
                "seconds_fab_a4": 1,
            }
        ])

        bulk_insert_seconds_a4(
            df,
            [
                "year", "week", "cut_num", "cut_qty", "first_quality_qty_sewing", "sample", "pass_field", "fail_field",
                "sew_def", "fab_def", "accepted", "rejected", "total_of_2ds", "percentage_of_2ds",
                "seconds_by_sew", "seconds_by_fab", "seconds_sew_a4", "seconds_fab_a4",
            ],
            ["date", "style", "line", "color"],
        )

        from quality_data.models import SecondsA4
        self.assertEqual(SecondsA4.objects.count(), 1)
        self.assertEqual(SecondsA4.objects.first().style, "STYLE-A")

    def test_bulk_insert_seconds_general_creates_records(self):
        import pandas as pd
        from quality_data.models import SecondsGeneralDefectType, SecondsGeneralDefect

        for name in ["corrido_2", "barre", "otros_3", "degradacion", "bordados"]:
            SecondsGeneralDefectType.objects.get_or_create(name=name)

        df = pd.DataFrame([
            {
                "date": "2025-03-01",
                "week": 10,
                "produced": 100,
                "corrido_2": 5,
                "barre": 3,
                "otros_3": 2,
                "degradacion": 1,
                "bordados": 0,
            }
        ])

        bulk_insert_seconds_general(
            df,
            ["week", "produced"],
            ["date"],
        )

        from quality_data.models import SecondsGeneral
        self.assertEqual(SecondsGeneral.objects.count(), 1)
        sg = SecondsGeneral.objects.first()
        self.assertEqual(sg.week, 10)
        defects = SecondsGeneralDefect.objects.filter(seconds_general=sg)
        defect_map = {d.defect_type.name: d.amount for d in defects}
        self.assertEqual(defect_map.get("corrido_2"), 5)
        self.assertEqual(defect_map.get("barre"), 3)
        self.assertEqual(defect_map.get("otros_3"), 2)


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


class BulkInsertDefectsOnlyStatsTest(TestCase):
    """
    Tests for _bulk_insert_defects_only returning defect sync stats (Task 2.4).

    RED phase: these tests reference behavior NOT yet implemented.
    Currently _bulk_insert_defects_only returns None.
    After implementation, it returns a dict with keys:
    created_defects, matched_parents, unmatched_defect_rows,
    invalid_date_rows, missing_color_rows.
    """

    def setUp(self):
        self.color = Color.objects.create(name="navy", is_active=True)
        self.color2 = Color.objects.create(name="white", is_active=True)
        self.defect_type = DefectType.objects.create(name="broken_stitch")

    def test_returns_stats_dict(self):
        """
        _bulk_insert_defects_only returns a dict with the expected keys.
        """
        quality = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-06-01",
            week=22,
            customer="A4",
            team=3,
            coord="TEST",
            po=3001,
            style="VALKYRIE",
            batch=1,
            color=self.color,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-06-01",
                "po": 3001,
                "style": "VALKYRIE",
                "team": 3,
                "color": "navy",
                "broken_stitch": 8,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertIsInstance(result, dict)
        for key in ("created_defects", "matched_parents",
                     "unmatched_defect_rows", "invalid_date_rows",
                     "missing_color_rows"):
            self.assertIn(key, result, f"Stats must include key '{key}'")

    def test_stats_counts_created_defects(self):
        """created_defects reflects the number of InspectionDefect rows created."""
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-06-02",
            week=22,
            customer="A4",
            team=3,
            coord="TEST",
            po=3002,
            style="VALKYRIE",
            batch=1,
            color=self.color,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-06-02",
                "po": 3002,
                "style": "VALKYRIE",
                "team": 3,
                "color": "navy",
                "broken_stitch": 3,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["created_defects"], 1)

    def test_stats_counts_matched_parents(self):
        """matched_parents counts unique parent rows that received defects."""
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-06-03",
            week=22,
            customer="A4",
            team=3,
            coord="TEST",
            po=3003,
            style="VALKYRIE",
            batch=1,
            color=self.color,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-06-03",
                "po": 3003,
                "style": "VALKYRIE",
                "team": 3,
                "color": "navy",
                "broken_stitch": 5,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["matched_parents"], 1)

    def test_stats_tracks_unmatched_defect_rows(self):
        """
        Rows with positive defect amounts but NO matching parent
        increment unmatched_defect_rows.
        """
        df = pd.DataFrame([
            {
                "date_1": "2025-06-04",
                "po": 9999,
                "style": "GHOST",
                "team": 99,
                "color": "navy",
                "broken_stitch": 10,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["unmatched_defect_rows"], 1)
        self.assertEqual(result["created_defects"], 0)

    def test_stats_tracks_invalid_date_rows(self):
        """
        Rows where date_1 cannot be canonicalized AND have positive defect
        amounts increment invalid_date_rows.
        """
        df = pd.DataFrame([
            {
                "date_1": "NOT_A_REAL_DATE",
                "po": 4001,
                "style": "STYLE-X",
                "team": 1,
                "color": "navy",
                "broken_stitch": 7,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["invalid_date_rows"], 1)
        self.assertEqual(result["created_defects"], 0)
        self.assertEqual(result["unmatched_defect_rows"], 0)

    def test_stats_tracks_missing_color_rows(self):
        """
        Rows where the color does not exist in the DB increment missing_color_rows.
        """
        df = pd.DataFrame([
            {
                "date_1": "2025-06-05",
                "po": 5001,
                "style": "STYLE-Y",
                "team": 2,
                "color": "invisible_pink",
                "broken_stitch": 4,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["missing_color_rows"], 1)
        self.assertEqual(result["created_defects"], 0)

    def test_empty_df_returns_zeroed_stats(self):
        """Empty DataFrame returns dict with all counters at 0."""
        df = pd.DataFrame([])
        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["created_defects"], 0)
        self.assertEqual(result["matched_parents"], 0)
        self.assertEqual(result["unmatched_defect_rows"], 0)
        self.assertEqual(result["invalid_date_rows"], 0)
        self.assertEqual(result["missing_color_rows"], 0)


class BulkInsertDefectsOnlySharedKeyTest(TestCase):
    """
    Tests proving _bulk_insert_defects_only uses build_qc_fa_key for
    deterministic parent-child matching across equivalent date/color
    representations (Task 2.3).
    """

    def setUp(self):
        self.color = Color.objects.create(name="dark_navy", is_active=True)
        self.defect_type = DefectType.objects.create(name="broken_stitch")

    def test_equivalent_dates_match_via_shared_key(self):
        """
        A parent with ISO date '2025-07-01' is matched by a row with
        equivalent US date '07/01/2025'.
        """
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-07-01",
            week=26,
            customer="A4",
            team=2,
            coord="TEST",
            po=6001,
            style="SPECTRE",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "07/01/2025",  # US format — equivalent to 2025-07-01
                "po": 6001,
                "style": "SPECTRE",
                "team": 2,
                "color": "dark navy",  # mixed case with space
                "broken_stitch": 6,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["created_defects"], 1)
        self.assertEqual(result["matched_parents"], 1)
        self.assertEqual(result["unmatched_defect_rows"], 0)

    def test_parent_index_includes_table_type(self):
        """
        When both QFA and QFC parents exist for the same natural key
        (except table_type), the defect row matches only the correct
        table_type parent.
        """
        color2 = Color.objects.create(name="red", is_active=True)
        qfa_parent = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-07-02",
            week=26,
            customer="A4",
            team=2,
            coord="TEST",
            po=6002,
            style="SPECTRE",
            batch=1,
            color=color2,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )
        qfc_parent = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-07-02",
            week=26,
            customer="CUSTOMER_X",
            team=2,
            coord="TEST",
            po=6002,
            style="SPECTRE",
            batch=1,
            color=color2,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-07-02",
                "po": 6002,
                "style": "SPECTRE",
                "team": 2,
                "color": "red",
                "broken_stitch": 2,
            }
        ])

        # When called with table_type='QFA', should match QFA parent only
        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["created_defects"], 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, qfa_parent)
        self.assertNotEqual(defect.inspection, qfc_parent)

    def test_mixed_date_formats_all_match_same_parent(self):
        """
        Multiple rows with different date representations of the same
        calendar day all match the same parent.
        """
        _ = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-07-03",
            week=26,
            customer="A4",
            team=2,
            coord="TEST",
            po=6003,
            style="SPECTRE",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        # Different representations of 2025-07-03
        df = pd.DataFrame([
            {
                "date_1": "2025-07-03",   # ISO
                "po": 6003,
                "style": "SPECTRE",
                "team": 2,
                "color": "dark_navy",
                "broken_stitch": 1,
            },
            {
                "date_1": "07/03/2025",   # US
                "po": 6003,
                "style": "SPECTRE",
                "team": 2,
                "color": "dark_navy",
                "broken_stitch": 2,
            },
            {
                "date_1": datetime.date(2025, 7, 3),  # Python date
                "po": 6003,
                "style": "SPECTRE",
                "team": 2,
                "color": "dark_navy",
                "broken_stitch": 3,
            },
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA")

        self.assertEqual(result["created_defects"], 3)
        self.assertEqual(result["matched_parents"], 1)
        self.assertEqual(result["unmatched_defect_rows"], 0)


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


# ─────────────────────────────────────────────────────────
# Phase 3: Regression Coverage — Mixed-format QFA/QFC
# ─────────────────────────────────────────────────────────

class BulkInsertDefectsOnlyQfcRegressionTest(TestCase):
    """
    Regression tests proving QFC defect persistence with mixed date
    formats, color_map, and comprehensive stat tracking (Task 3.1).
    """

    def setUp(self):
        self.color_black = Color.objects.create(name="black", is_active=True)
        self.color_white = Color.objects.create(name="white", is_active=True)
        self.defect_type = DefectType.objects.create(name="broken_stitch")
        self.defect_type2 = DefectType.objects.create(name="open_seam")

    def test_qfc_parent_matched_with_iso_date(self):
        """QFC parent with ISO date is matched by row with same ISO date."""
        parent = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-08-01",
            week=31,
            customer="CUST",
            team=5,
            coord="TEST",
            po=7001,
            style="QFC-ISO",
            batch=1,
            color=self.color_black,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-08-01",
                "po": 7001,
                "style": "QFC-ISO",
                "team": 5,
                "color": "black",
                "broken_stitch": 3,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFC")

        self.assertEqual(result["created_defects"], 1)
        self.assertEqual(result["matched_parents"], 1)
        self.assertEqual(result["unmatched_defect_rows"], 0)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, parent)
        self.assertEqual(defect.inspection.table_type, "QFC")

    def test_qfc_parent_matched_with_us_date(self):
        """QFC parent with ISO date is matched by row with US format date."""
        parent = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-08-02",
            week=31,
            customer="CUST",
            team=5,
            coord="TEST",
            po=7002,
            style="QFC-US",
            batch=1,
            color=self.color_black,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "08/02/2025",  # US format
                "po": 7002,
                "style": "QFC-US",
                "team": 5,
                "color": "black",
                "broken_stitch": 4,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFC")

        self.assertEqual(result["created_defects"], 1)
        self.assertEqual(result["matched_parents"], 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, parent)

    def test_qfc_parent_matched_with_excel_serial_date(self):
        """QFC parent with ISO date is matched by row with Excel serial date."""
        parent = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-08-03",
            week=31,
            customer="CUST",
            team=5,
            coord="TEST",
            po=7003,
            style="QFC-SERIAL",
            batch=1,
            color=self.color_black,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        # Excel serial for 2025-08-03: days from 1899-12-30
        from datetime import date
        epoch = date(1899, 12, 30)
        target = date(2025, 8, 3)
        serial = (target - epoch).days

        df = pd.DataFrame([
            {
                "date_1": serial,  # Excel serial number
                "po": 7003,
                "style": "QFC-SERIAL",
                "team": 5,
                "color": "black",
                "broken_stitch": 2,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFC")

        self.assertEqual(result["created_defects"], 1)
        self.assertEqual(result["matched_parents"], 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, parent)

    def test_qfc_parent_isolation_from_qfa(self):
        """QFC defect row does NOT match a QFA parent with same natural key."""
        qfa_parent = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-08-04",
            week=31,
            customer="CUST",
            team=5,
            coord="TEST",
            po=7004,
            style="ISOLATED",
            batch=1,
            color=self.color_black,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )
        qfc_parent = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2025-08-04",
            week=31,
            customer="CUST",
            team=5,
            coord="TEST",
            po=7004,
            style="ISOLATED",
            batch=1,
            color=self.color_black,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=10,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {
                "date_1": "2025-08-04",
                "po": 7004,
                "style": "ISOLATED",
                "team": 5,
                "color": "black",
                "broken_stitch": 1,
            }
        ])

        # Match QFC only — should link to QFC parent, NOT QFA
        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFC")

        self.assertEqual(result["created_defects"], 1)
        defect = InspectionDefect.objects.first()
        self.assertEqual(defect.inspection, qfc_parent)
        self.assertNotEqual(defect.inspection, qfa_parent)

    def test_color_map_parameter_resolves_colors(self):
        """
        When color_map is provided, _bulk_insert_defects_only uses it
        instead of querying Color.objects.filter() per row.
        """
        parent = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-08-05",
            week=31,
            customer="CUST",
            team=3,
            coord="TEST",
            po=8001,
            style="COLORMAP",
            batch=1,
            color=self.color_white,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        color_map = {"white": self.color_white, "black": self.color_black}

        df = pd.DataFrame([
            {
                "date_1": "2025-08-05",
                "po": 8001,
                "style": "COLORMAP",
                "team": 3,
                "color": "white",
                "broken_stitch": 7,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA",
                                            color_map=color_map)

        self.assertEqual(result["created_defects"], 1)
        self.assertEqual(result["matched_parents"], 1)
        self.assertEqual(result["missing_color_rows"], 0)

    def test_color_map_detects_missing_color(self):
        """Color that is NOT in the color_map increments missing_color_rows."""
        parent = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-08-06",
            week=31,
            customer="CUST",
            team=3,
            coord="TEST",
            po=8002,
            style="MISSING-MAP",
            batch=1,
            color=self.color_black,
            qty=50,
            seconds=5,
            accepted=45,
            rejected=5,
            sample=5,
            defects_total=5,
            aql=2.5,
            pass_or_fail="PASS",
        )

        # color_map only has "white" — black is missing
        color_map = {"white": self.color_white}

        df = pd.DataFrame([
            {
                "date_1": "2025-08-06",
                "po": 8002,
                "style": "MISSING-MAP",
                "team": 3,
                "color": "black",  # not in color_map
                "broken_stitch": 5,
            }
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFA",
                                            color_map=color_map)

        self.assertEqual(result["created_defects"], 0)
        self.assertEqual(result["missing_color_rows"], 1)

    def test_mixed_scenario_all_stats_accumulate(self):
        """A single batch with matching, invalid-date, missing-color, and
        unmatched rows accumulates stats correctly."""
        parent = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-08-10",
            week=32,
            customer="CUST",
            team=1,
            coord="TEST",
            po=9001,
            style="MIXED",
            batch=1,
            color=self.color_black,
            qty=200,
            seconds=20,
            accepted=180,
            rejected=20,
            sample=20,
            defects_total=10,
            aql=2.5,
            pass_or_fail="PASS",
        )

        df = pd.DataFrame([
            {  # ✅ Matches parent
                "date_1": "2025-08-10",
                "po": 9001,
                "style": "MIXED",
                "team": 1,
                "color": "black",
                "broken_stitch": 3,
                "open_seam": 2,
            },
            {  # ❌ Invalid date
                "date_1": "NOT_A_DATE",
                "po": 9002,
                "style": "MIXED",
                "team": 1,
                "color": "black",
                "broken_stitch": 5,
            },
            {  # ❌ Missing color
                "date_1": "2025-08-10",
                "po": 9001,
                "style": "MIXED",
                "team": 1,
                "color": "invisible_unicorn",
                "broken_stitch": 4,
            },
            {  # ❌ Unmatched parent (different PO)
                "date_1": "2025-08-10",
                "po": 9999,
                "style": "MIXED",
                "team": 1,
                "color": "black",
                "broken_stitch": 6,
            },
            {  # ✅ No defects — skipped silently, no stat increment
                "date_1": "2025-08-10",
                "po": 9001,
                "style": "MIXED",
                "team": 1,
                "color": "black",
                "broken_stitch": 0,
                "open_seam": 0,
            },
        ])

        result = _bulk_insert_defects_only(df, ["broken_stitch", "open_seam"],
                                            "QFA")

        self.assertEqual(result["created_defects"], 2)  # broken_stitch=3 + open_seam=2
        self.assertEqual(result["matched_parents"], 1)   # only the first row matched
        self.assertEqual(result["unmatched_defect_rows"], 1)  # row 4 with PO 9999
        self.assertEqual(result["invalid_date_rows"], 1)       # row 2 with NOT_A_DATE
        self.assertEqual(result["missing_color_rows"], 1)      # row 3 with invisible_unicorn

    def test_empty_df_with_qfc_returns_zeroed_stats(self):
        """Empty DataFrame with QFC table_type returns all-zero stats."""
        df = pd.DataFrame([])
        result = _bulk_insert_defects_only(df, ["broken_stitch"], "QFC")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["created_defects"], 0)
        self.assertEqual(result["matched_parents"], 0)
        self.assertEqual(result["unmatched_defect_rows"], 0)
        self.assertEqual(result["invalid_date_rows"], 0)
        self.assertEqual(result["missing_color_rows"], 0)
