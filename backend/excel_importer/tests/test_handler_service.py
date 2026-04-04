"""
Tests for handler_service bulk insert functions, specifically the defects-only path.
"""
from django.test import TestCase
from django.db import IntegrityError
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
)


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
        defect_type2 = DefectType.objects.create(name="fab_def")
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
        quality = QualityQcFa.objects.create(
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
