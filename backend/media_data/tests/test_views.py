"""
Endpoint tests for close_inspection view.

Tests cover:
- Already closed inspection rejection
- Close with defects → REJECT status
- Close without defects → PASS status
- Bridge synchronization result in response
"""

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from quality_data.models import Color, DefectType, QualityQcFa
from media_data.models import InspectionData, RevisionDefect


class CloseInspectionAlreadyClosedTest(APITestCase):
    """Scenario: Close rejects already-closed inspection."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='operator1', password='123')
        self.client.login(username='operator1', password='123')
        self.color = Color.objects.create(name="Red", is_active=True)
        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="POLO-2026",
            size="XL",
            is_closed=True,
            status='PASS',
        )

    def test_close_already_closed_returns_400(self):
        """Closing an already-closed inspection returns 400."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already closed", response.data['error'])


class CloseInspectionWithDefectsTest(APITestCase):
    """Scenario: Close inspection with defects sets REJECT status."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='operator1', password='123')
        self.client.login(username='operator1', password='123')
        self.color = Color.objects.create(name="Blue", is_active=True)
        self.defect_type = DefectType.objects.create(name="Stitching", is_active=True)

        # Create matching QC record for bridge
        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=timezone.now().date().isocalendar()[1],
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
            is_closed=False,
        )
        # Create 5 defects
        for i in range(5):
            RevisionDefect.objects.create(
                inspection=self.inspection,
                inspector=self.user,
                defect_type=self.defect_type,
                defect_size="Medium",
                defect_count=1,
            )

    def test_close_with_defects_returns_reject(self):
        """Closing inspection with defects sets status to REJECT."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], 'REJECT')
        self.assertEqual(response.data['total_defects'], 5)

        self.inspection.refresh_from_db()
        self.assertTrue(self.inspection.is_closed)
        self.assertEqual(self.inspection.status, 'REJECT')
        self.assertIsNotNone(self.inspection.closed_at)

    def test_close_with_defects_includes_bridge_result(self):
        """Response includes quality_data_sync with bridge result."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertIn('quality_data_sync', response.data)
        self.assertEqual(response.data['quality_data_sync']['status'], 'synced')
        self.assertEqual(response.data['quality_data_sync']['matched_records'], 1)


class CloseInspectionWithoutDefectsTest(APITestCase):
    """Scenario: Close inspection without defects sets PASS status."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='operator2', password='123')
        self.client.login(username='operator2', password='123')
        self.color = Color.objects.create(name="Green", is_active=True)

        # Create matching QC record for bridge
        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=timezone.now().date().isocalendar()[1],
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="TSHIRT-2026",
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
            style="TSHIRT-2026",
            size="L",
            is_closed=False,
        )
        # No defects created

    def test_close_without_defects_returns_pass(self):
        """Closing inspection with no defects sets status to PASS."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], 'PASS')
        self.assertEqual(response.data['total_defects'], 0)

        self.inspection.refresh_from_db()
        self.assertTrue(self.inspection.is_closed)
        self.assertEqual(self.inspection.status, 'PASS')
        self.assertIsNotNone(self.inspection.closed_at)

    def test_close_without_defects_includes_bridge_result(self):
        """Response includes quality_data_sync even with no defects."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertIn('quality_data_sync', response.data)
        # Zero defects still syncs with 0 totals
        self.assertEqual(response.data['quality_data_sync']['status'], 'synced')
        self.assertEqual(response.data['quality_data_sync']['total_defects'], 0)


class CloseInspectionBridgeSyncTest(APITestCase):
    """Scenario: Close returns bridge synchronization result."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='operator3', password='123')
        self.client.login(username='operator3', password='123')
        self.color = Color.objects.create(name="Yellow", is_active=True)
        self.defect_type = DefectType.objects.create(name="Tear", is_active=True)

        # Matching QC record
        self.qc_record = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2025-01-15",
            week=timezone.now().date().isocalendar()[1],
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="JEANS-2026",
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
            style="JEANS-2026",
            size="32",
            is_closed=False,
        )
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Large",
            defect_count=2,
        )

    def test_close_includes_bridge_result_keys(self):
        """Response quality_data_sync contains expected keys."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sync = response.data['quality_data_sync']
        self.assertIn('matched_records', sync)
        self.assertIn('synced_defects', sync)
        self.assertIn('status', sync)
        self.assertIn('total_defects', sync)

    def test_close_bridges_to_correct_qc_record(self):
        """QC record matched by style and color is updated."""
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        self.client.post(url)

        self.qc_record.refresh_from_db()
        self.assertEqual(self.qc_record.defects_total, 2)
        self.assertEqual(self.qc_record.pass_or_fail, 'REJECT')


class UndoDefectTest(APITestCase):
    """Scenario: Undo removes the most recently captured defect for an inspection."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='operator_undo', password='123')
        self.client.login(username='operator_undo', password='123')
        self.color = Color.objects.create(name="Purple", is_active=True)
        self.defect_type = DefectType.objects.create(name="Hole", is_active=True)

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="PANTS-2026",
            size="M",
            is_closed=False,
        )
        # Create multiple defects with different timestamps
        for i in range(3):
            RevisionDefect.objects.create(
                inspection=self.inspection,
                inspector=self.user,
                defect_type=self.defect_type,
                defect_size="Small",
                defect_count=1,
            )

    def test_undo_deletes_most_recent_defect(self):
        """Undoing removes the last captured defect for the inspection."""
        initial_count = RevisionDefect.objects.filter(inspection=self.inspection).count()
        self.assertEqual(initial_count, 3)

        url = f"{reverse('media_data:defect-undo')}?inspection={self.inspection.id}"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("removed", response.data['message'])

        remaining_count = RevisionDefect.objects.filter(inspection=self.inspection).count()
        self.assertEqual(remaining_count, 2)

    def test_undo_returns_400_when_inspection_param_missing(self):
        """Undoing without inspection query param returns 400."""
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("required", response.data['error'])

    def test_undo_returns_404_when_no_defects(self):
        """Undoing an inspection with no defects returns 404."""
        # Create an inspection with no defects
        empty_inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="SHIRT-2026",
            size="L",
            is_closed=False,
        )

        url = f"{reverse('media_data:defect-undo')}?inspection={empty_inspection.id}"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No defect captures were found", response.data['message'])

    def test_undo_returns_400_when_inspection_closed(self):
        """Undoing a closed inspection should be rejected with 400."""
        # First close the inspection
        self.inspection.is_closed = True
        self.inspection.status = 'REJECT'
        self.inspection.save()

        url = f"{reverse('media_data:defect-undo')}?inspection={self.inspection.id}"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closed", response.data['error'].lower())
