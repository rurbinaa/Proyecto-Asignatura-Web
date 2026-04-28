"""
Bridge unit tests for inspection_bridge.py

Tests cover:
- Unclosed inspection rejection
- No matching QC records handling
- Single/multiple QC record syncing
- Defect aggregation by type
- InspectionDefect through-table sync
- Inactive defect type filtering
- Edge cases: zero defects, sample < defects, null defect_type
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from quality_data.models import (
    Color, DefectType, QualityQcFa, InspectionDefect,
    SecondsGeneral, SecondsA4,
)
from media_data.models import InspectionData, RevisionDefect


def _current_week():
    return timezone.now().date().isocalendar()[1]


class InspectionBridgeUnclosedTest(TestCase):
    """Scenario: Bridge rejects unclosed inspection."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Red", is_active=True)
        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="POLO-2026",
            size="XL",
            is_closed=False,
        )

    def test_bridge_raises_on_open_inspection(self):
        """Bridge raises ValueError if inspection is not closed."""
        from media_data.inspection_bridge import bridge_inspection

        with self.assertRaises(ValueError) as ctx:
            bridge_inspection(self.inspection)
        self.assertIn("Inspection must be closed before bridging", str(ctx.exception))


class InspectionBridgeNoMatchTest(TestCase):
    """Scenario: Bridge handles no matching QC records."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Blue", is_active=True)
        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="NONEXISTENT-STYLE",
            size="M",
            closed_at=timezone.now(),
            is_closed=True,
            status='PASS',
        )

    def test_bridge_no_match_returns_no_match_status(self):
        """Bridge returns no_match when no QualityQcFa record exists."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertEqual(result['status'], 'no_match')
        self.assertEqual(result['matched_records'], 0)
        self.assertEqual(result['synced_defects'], 0)


class InspectionBridgeSingleRecordTest(TestCase):
    """Scenario: Bridge syncs single QC record with defects."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Green", is_active=True)
        self.defect_type_a = DefectType.objects.create(name="Stitching", is_active=True)
        self.defect_type_b = DefectType.objects.create(name="Stain", is_active=True)

        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="POLO-2026",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=100,
            rejected=0,
            sample=100,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="POLO-2026",
            size="XL",
            closed_at=timezone.now(),
            is_closed=True,
            status='REJECT',
        )
        # 2 defects of type A, 1 of type B = 3 total
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type_a,
            defect_size="Medium",
            defect_count=2,
        )
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type_b,
            defect_size="Small",
            defect_count=1,
        )

    def test_bridge_syncs_single_qc_record_with_defects(self):
        """QC record is updated with defect totals."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertEqual(result['status'], 'synced')
        self.assertEqual(result['matched_records'], 1)
        self.assertEqual(result['total_defects'], 3)

        self.qc_record.refresh_from_db()
        self.assertEqual(self.qc_record.defects_total, 3)
        self.assertEqual(self.qc_record.rejected, 3)
        self.assertEqual(self.qc_record.accepted, 97)
        self.assertEqual(self.qc_record.pass_or_fail, 'REJECT')


class InspectionBridgeMultipleRecordsTest(TestCase):
    """Scenario: Bridge syncs multiple QC records for same style/color."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Yellow", is_active=True)
        self.defect_type = DefectType.objects.create(name="Tear", is_active=True)

        # Two QC records for same style/color, different batches
        self.qc_record_1 = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="SHIRT-2026",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=100,
            rejected=0,
            sample=50,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )
        self.qc_record_2 = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="SHIRT-2026",
            batch=2,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=100,
            rejected=0,
            sample=50,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="SHIRT-2026",
            size="L",
            closed_at=timezone.now(),
            is_closed=True,
            status='REJECT',
        )
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Large",
            defect_count=4,
        )

    def test_bridge_syncs_multiple_qc_records(self):
        """Both QC records are updated with same defect totals."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertEqual(result['matched_records'], 2)

        self.qc_record_1.refresh_from_db()
        self.qc_record_2.refresh_from_db()
        self.assertEqual(self.qc_record_1.defects_total, 4)
        self.assertEqual(self.qc_record_2.defects_total, 4)


class InspectionBridgeDefectAggregationTest(TestCase):
    """Scenario: Defect aggregation counts by type name."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Black", is_active=True)
        self.defect_type_a = DefectType.objects.create(name="type_A", is_active=True)
        self.defect_type_b = DefectType.objects.create(name="type_B", is_active=True)

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="JEANS-2026",
            size="32",
            closed_at=timezone.now(),
            is_closed=True,
        )
        # 5 + 3 = 8 of type_A, 2 of type_B
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type_a,
            defect_size="Small",
            defect_count=5,
        )
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type_a,
            defect_size="Medium",
            defect_count=3,
        )
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type_b,
            defect_size="Large",
            defect_count=2,
        )

    def test_aggregate_defects_sums_by_type(self):
        """_aggregate_defects returns correct counts per type."""
        from media_data.inspection_bridge import _aggregate_defects

        counts = _aggregate_defects(self.inspection)

        self.assertEqual(counts["type_A"], 8)
        self.assertEqual(counts["type_B"], 2)


class InspectionBridgeInspectionDefectSyncTest(TestCase):
    """Scenario: InspectionDefect sync creates through-table records."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="White", is_active=True)
        self.defect_type = DefectType.objects.create(name="Button", is_active=True)

        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="TEST-STYLE",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=95,
            rejected=5,
            sample=100,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="TEST-STYLE",
            size="M",
            closed_at=timezone.now(),
            is_closed=True,
            status='REJECT',
        )

    def test_sync_defect_types_creates_records(self):
        """_sync_defect_types creates InspectionDefect records."""
        from media_data.inspection_bridge import _sync_defect_types

        defect_counts = {"Button": 3}
        synced = _sync_defect_types(self.qc_record, defect_counts)

        self.assertEqual(synced, 1)
        self.assertEqual(InspectionDefect.objects.filter(inspection=self.qc_record).count(), 1)
        insp_defect = InspectionDefect.objects.get(inspection=self.qc_record)
        self.assertEqual(insp_defect.defect_type, self.defect_type)
        self.assertEqual(insp_defect.amount, 3)

    def test_sync_defect_types_deletes_existing_before_creating(self):
        """Existing InspectionDefect records are deleted before recreation."""
        from media_data.inspection_bridge import _sync_defect_types

        # Create initial defect record
        InspectionDefect.objects.create(
            inspection=self.qc_record,
            defect_type=self.defect_type,
            amount=99,
        )

        defect_counts = {"Button": 5}
        _sync_defect_types(self.qc_record, defect_counts)

        # Only the new record should exist
        self.assertEqual(InspectionDefect.objects.filter(inspection=self.qc_record).count(), 1)
        insp_defect = InspectionDefect.objects.get(inspection=self.qc_record)
        self.assertEqual(insp_defect.amount, 5)


class InspectionBridgeInactiveDefectTypesTest(TestCase):
    """Scenario: InspectionDefect sync skips inactive defect types."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Purple", is_active=True)
        self.active_type = DefectType.objects.create(name="ActiveDefect", is_active=True)
        self.inactive_type = DefectType.objects.create(name="InactiveDefect", is_active=False)

        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="MIXED-STYLE",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=100,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

    def test_sync_skips_inactive_defect_types(self):
        """Only active defect types create InspectionDefect records."""
        from media_data.inspection_bridge import _sync_defect_types

        defect_counts = {"ActiveDefect": 2, "InactiveDefect": 7}
        synced = _sync_defect_types(self.qc_record, defect_counts)

        # Only 1 synced (the active one)
        self.assertEqual(synced, 1)
        self.assertEqual(InspectionDefect.objects.filter(inspection=self.qc_record).count(), 1)
        insp_defect = InspectionDefect.objects.get(inspection=self.qc_record)
        self.assertEqual(insp_defect.defect_type, self.active_type)


class InspectionBridgeEdgeCasesTest(TestCase):
    """Edge case coverage: zero defects, sample < defects, null defect_type."""

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.color = Color.objects.create(name="Orange", is_active=True)
        self.defect_type = DefectType.objects.create(name="Minor", is_active=True)

        self.qc_record_small_sample = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="EDGE-CASE-SMALL",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=10,
            rejected=0,
            sample=10,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

    def test_zero_defects_produces_pass_and_zero_totals(self):
        """Zero defects: QC record has rejected=0, accepted=sample."""
        from media_data.inspection_bridge import bridge_inspection

        # Create a separate QC record for zero defects test
        qc_zero = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=_current_week(),
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="ZERO-DEFECTS",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=50,
            rejected=0,
            sample=50,
            defects_total=0,
            aql=1.5,
            pass_or_fail="PASS",
        )

        inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="ZERO-DEFECTS",
            size="S",
            closed_at=timezone.now(),
            is_closed=True,
            status='PASS',
        )
        # No defects created

        result = bridge_inspection(inspection)

        self.assertEqual(result['status'], 'synced')
        self.assertEqual(result['total_defects'], 0)

        qc_zero.refresh_from_db()
        self.assertEqual(qc_zero.rejected, 0)
        self.assertEqual(qc_zero.accepted, 50)
        self.assertEqual(qc_zero.defects_total, 0)

    def test_sample_smaller_than_defect_count_handles_gracefully(self):
        """Sample=10, defects=15: rejected=15, accepted=0 (no negative)."""
        from media_data.inspection_bridge import bridge_inspection

        inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="EDGE-CASE-SMALL",
            size="M",
            closed_at=timezone.now(),
            is_closed=True,
            status='REJECT',
        )
        RevisionDefect.objects.create(
            inspection=inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Small",
            defect_count=15,
        )

        bridge_inspection(inspection)

        self.qc_record_small_sample.refresh_from_db()
        self.assertEqual(self.qc_record_small_sample.rejected, 15)
        self.assertEqual(self.qc_record_small_sample.accepted, 0)  # max(0, 10-15) = 0

    def test_null_defect_type_excluded_from_aggregation(self):
        """RevisionDefect with defect_type=None is excluded from count."""
        from media_data.inspection_bridge import _aggregate_defects

        inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="EDGE-CASE",
            size="L",
            closed_at=timezone.now(),
            is_closed=True,
        )
        # One with null defect_type
        RevisionDefect.objects.create(
            inspection=inspection,
            inspector=self.user,
            defect_type=None,
            defect_size="Unknown",
            defect_count=99,
        )
        # One with valid defect_type
        RevisionDefect.objects.create(
            inspection=inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Small",
            defect_count=1,
        )

        counts = _aggregate_defects(inspection)

        # Null type excluded, only "Minor" = 1
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts["Minor"], 1)


class SecondsGeneralBridgeTest(TestCase):
    """SecondsGeneral UPSERT from inspection data."""

    def setUp(self):
        self.user = User.objects.create_user(username='op', password='123')
        self.color = Color.objects.create(name="SG-Test", is_active=True)
        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="SG-STYLE",
            size="XL",
            closed_at=timezone.now(),
            is_closed=True,
            status='PASS',
        )

    def test_seconds_general_upsert_creates_new_record(self):
        """SecondsGeneral created with common fields when no match exists."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertIn('seconds_general', result)
        sg = SecondsGeneral.objects.get(
            style="SG-STYLE",
            color="SG-Test",
            week=_current_week(),
        )
        self.assertEqual(sg.date, self.inspection.date.isoformat())
        self.assertEqual(sg.size, "XL")
        # Production fields stay at defaults
        self.assertEqual(sg.produced, 0)
        self.assertEqual(sg.fixed, 0)

    def test_seconds_general_upsert_preserves_production_fields(self):
        """Re-bridging does NOT overwrite production fields."""
        from media_data.inspection_bridge import bridge_inspection

        # First bridge: create record
        bridge_inspection(self.inspection)

        # Manually set production field
        sg = SecondsGeneral.objects.get(
            style="SG-STYLE", color="SG-Test", week=_current_week(),
        )
        sg.produced = 500
        sg.save()

        # Second bridge: should NOT overwrite produced
        bridge_inspection(self.inspection)

        sg.refresh_from_db()
        self.assertEqual(sg.produced, 500)


class SecondsA4BridgeTest(TestCase):
    """SecondsA4 UPSERT from inspection data."""

    def setUp(self):
        self.user = User.objects.create_user(username='op', password='123')
        self.color = Color.objects.create(name="A4-Test", is_active=True)
        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="A4-STYLE",
            size="M",
            closed_at=timezone.now(),
            is_closed=True,
            status='PASS',
        )

    def test_seconds_a4_upsert_creates_new_record(self):
        """SecondsA4 created with common fields."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertIn('seconds_a4', result)
        a4 = SecondsA4.objects.get(
            style="A4-STYLE",
            color=self.color,
            week=_current_week(),
        )
        self.assertEqual(a4.date, self.inspection.date.isoformat())

    def test_seconds_a4_upsert_preserves_production_fields(self):
        """Re-bridging preserves cut_qty."""
        from media_data.inspection_bridge import bridge_inspection

        bridge_inspection(self.inspection)

        a4 = SecondsA4.objects.get(
            style="A4-STYLE", color=self.color, week=_current_week(),
        )
        a4.cut_qty = 300
        a4.save()

        bridge_inspection(self.inspection)

        a4.refresh_from_db()
        self.assertEqual(a4.cut_qty, 300)


class QualityQcFaWeekMatchTest(TestCase):
    """Week-based matching for QualityQcFa."""

    def setUp(self):
        self.user = User.objects.create_user(username='op', password='123')
        self.color = Color.objects.create(name="Week-Test", is_active=True)
        self.current_week = _current_week()
        self.other_week = self.current_week + 1
        if self.other_week > 52:
            self.other_week = 1

    def test_same_week_matches(self):
        """QC record with same week is matched and updated."""
        from media_data.inspection_bridge import bridge_inspection

        qc = QualityQcFa.objects.create(
            table_type="QFA", date_1="2025-01-15",
            week=self.current_week, customer="Cust", team=1, coord="C",
            po=1, style="WEEK-STYLE", batch=1, color=self.color,
            qty=100, seconds=0, accepted=100, rejected=0, sample=100,
            defects_total=0, aql=0, pass_or_fail="PASS",
        )

        inspection = InspectionData.objects.create(
            inspector=self.user, color=self.color,
            style="WEEK-STYLE", size="M",
            closed_at=timezone.now(), is_closed=True, status='REJECT',
        )

        result = bridge_inspection(inspection)
        self.assertEqual(result['status'], 'synced')
        self.assertEqual(result['matched_records'], 1)

        qc.refresh_from_db()
        self.assertEqual(qc.pass_or_fail, 'REJECT')
        self.assertEqual(qc.date_1, inspection.closed_at.date().isoformat())

    def test_cross_week_blocked(self):
        """QC record with different week is NOT matched."""
        from media_data.inspection_bridge import bridge_inspection

        QualityQcFa.objects.create(
            table_type="QFA", date_1="2025-01-15",
            week=self.other_week, customer="Cust", team=1, coord="C",
            po=1, style="WEEK-STYLE-2", batch=1, color=self.color,
            qty=100, seconds=0, accepted=100, rejected=0, sample=100,
            defects_total=0, aql=0, pass_or_fail="PASS",
        )

        inspection = InspectionData.objects.create(
            inspector=self.user, color=self.color,
            style="WEEK-STYLE-2", size="M",
            closed_at=timezone.now(), is_closed=True, status='REJECT',
        )

        result = bridge_inspection(inspection)
        self.assertEqual(result['status'], 'no_match')


class BridgeTransactionTest(TestCase):
    """Transaction atomicity for bridge."""

    def setUp(self):
        self.user = User.objects.create_user(username='op', password='123')
        self.color = Color.objects.create(name="Tx-Test", is_active=True)
        self.defect_type = DefectType.objects.create(name="TxDefect", is_active=True)

        self.qc = QualityQcFa.objects.create(
            table_type="QFA", date_1="2025-01-15",
            week=_current_week(), customer="Cust", team=1, coord="C",
            po=1, style="TX-STYLE", batch=1, color=self.color,
            qty=100, seconds=0, accepted=100, rejected=0, sample=100,
            defects_total=0, aql=0, pass_or_fail="PASS",
        )

        self.inspection = InspectionData.objects.create(
            inspector=self.user, color=self.color,
            style="TX-STYLE", size="L",
            closed_at=timezone.now(), is_closed=True, status='REJECT',
        )
        RevisionDefect.objects.create(
            inspection=self.inspection, inspector=self.user,
            defect_type=self.defect_type, defect_size="M", defect_count=2,
        )

    def test_all_tables_populated_in_single_transaction(self):
        """QC, SG, SA4 all populated."""
        from media_data.inspection_bridge import bridge_inspection

        result = bridge_inspection(self.inspection)

        self.assertEqual(result['status'], 'synced')
        self.assertIn('seconds_general', result)
        self.assertIn('seconds_a4', result)

        self.qc.refresh_from_db()
        self.assertEqual(self.qc.defects_total, 2)
        self.assertEqual(self.qc.pass_or_fail, 'REJECT')
