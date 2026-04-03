"""
Integration tests for Excel V2 preview/confirm/reject workflow.

These tests exercise the full flow: upload → preview → confirm/reject.
"""

import io
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from quality_data.models import (
    QualityQcFa,
    SecondsA4,
    SecondsGeneral,
    Container,
    Color,
    ExcelSyncSession,
)


def _make_mock_dataframe(rows):
    """Create a real pandas DataFrame for testing."""
    import pandas as pd
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


class ExcelPreviewViewTest(TestCase):
    """Tests for POST /excel/preview/<filename>/"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:excel-preview', kwargs={'filename': 'test.xlsx'})

    @patch('quality_data.views.load_and_clean')
    def test_preview_returns_session_id(self, mock_load_and_clean):
        """Preview endpoint returns a session_id and preview data."""
        mock_load_and_clean.return_value = _make_mock_dataframe([
            {"date_1": "2025-01-15", "po": 123, "style": "N3165"},
        ])

        with open('/dev/null', 'rb') as f:
            response = self.client.post(self.url, {'file': f}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('preview', response.data)
        self.assertIn('warnings', response.data)
        self.assertEqual(response.data['status'], 'pending')

    @patch('quality_data.views.load_and_clean')
    def test_preview_creates_pending_session(self, mock_load_and_clean):
        """Preview creates a session with status 'pending'."""
        mock_load_and_clean.return_value = _make_mock_dataframe([])

        with open('/dev/null', 'rb') as f:
            self.client.post(self.url, {'file': f}, format='multipart')

        self.assertEqual(ExcelSyncSession.objects.count(), 1)
        session = ExcelSyncSession.objects.first()
        self.assertEqual(session.status, 'pending')

    @patch('quality_data.views.load_and_clean')
    def test_preview_does_not_modify_database(self, mock_load_and_clean):
        """Preview does not create or modify any data records."""
        mock_load_and_clean.return_value = _make_mock_dataframe([
            {"date_1": "2025-01-15", "po": 123},
        ])
        initial_count = QualityQcFa.objects.count()

        with open('/dev/null', 'rb') as f:
            self.client.post(self.url, {'file': f}, format='multipart')

        self.assertEqual(QualityQcFa.objects.count(), initial_count)

    @patch('quality_data.views.load_and_clean')
    def test_preview_returns_data_loss_warnings(self, mock_load_and_clean):
        """Preview warns when Excel has fewer rows than DB for a date."""
        color = Color.objects.create(name="black", is_active=True)
        for i in range(5):
            QualityQcFa.objects.create(
                table_type="QFA", date_1="2025-01-15", week=3,
                customer="A4", team=1, coord="JAVIER",
                po=195221, style="N3165", batch=1, color=color,
                qty=100, seconds=50, accepted=40, rejected=10,
                sample=5, defects_total=0, aql=2.5, pass_or_fail="Pass",
            )

        mock_load_and_clean.return_value = _make_mock_dataframe([
            {"date_1": "2025-01-15"},
        ])

        with open('/dev/null', 'rb') as f:
            response = self.client.post(self.url, {'file': f}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['warnings']) > 0)


class ExcelConfirmViewTest(TestCase):
    """Tests for POST /excel/confirm/<session_id>/"""

    def setUp(self):
        self.client = APIClient()

    def test_confirm_applies_changes(self):
        """Confirm applies session and sets status to confirmed."""
        color = Color.objects.create(name="red", is_active=True)
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

        url = reverse('quality_data:excel-confirm', kwargs={'session_id': session.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'confirmed')
        self.assertEqual(SecondsA4.objects.count(), 1)

    def test_confirm_rejects_already_confirmed(self):
        """Cannot confirm a session that's already confirmed."""
        session = ExcelSyncSession.objects.create(status='confirmed')
        url = reverse('quality_data:excel-confirm', kwargs={'session_id': session.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_404_for_missing_session(self):
        """Returns 404 if session doesn't exist."""
        url = reverse('quality_data:excel-confirm', kwargs={'session_id': 99999})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExcelRejectViewTest(TestCase):
    """Tests for DELETE /excel/reject/<session_id>/"""

    def setUp(self):
        self.client = APIClient()

    def test_reject_marks_session_as_rejected(self):
        """Reject sets session status to rejected."""
        session = ExcelSyncSession.objects.create()
        url = reverse('quality_data:excel-reject', kwargs={'session_id': session.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'rejected')

    def test_reject_does_not_modify_data(self):
        """Reject does not modify any data records."""
        color = Color.objects.create(name="red", is_active=True)
        SecondsA4.objects.create(
            year=2025, week=3, date="2025-01-15", cut_num=1,
            style="N3165", cut_qty=100, color=color,
            first_quality_qty_sewing=50, sample=5,
            pass_field=45, fail_field=5, sew_def=3, fab_def=2,
            accepted=40, rejected=10, total_of_2ds=15,
            percentage_of_2ds=10.5, line="1",
            seconds_by_sew=8, seconds_by_fab=7,
            seconds_sew_a4=5.0, seconds_fab_a4=3.0,
        )
        initial_count = SecondsA4.objects.count()

        session = ExcelSyncSession.objects.create(
            seconds_a4_data=[{"date": "2025-01-15", "cut_num": 1}],
        )
        url = reverse('quality_data:excel-reject', kwargs={'session_id': session.pk})
        self.client.delete(url)

        self.assertEqual(SecondsA4.objects.count(), initial_count)

    def test_reject_rejects_already_rejected(self):
        """Cannot reject a session that's already rejected."""
        session = ExcelSyncSession.objects.create(status='rejected')
        url = reverse('quality_data:excel-reject', kwargs={'session_id': session.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FullWorkflowTest(TestCase):
    """Integration test: full upload → preview → confirm flow."""

    def setUp(self):
        self.client = APIClient()

    @patch('quality_data.views.load_and_clean')
    def test_full_preview_confirm_flow(self, mock_load_and_clean):
        """Complete flow: upload → get preview → confirm → data applied."""
        mock_load_and_clean.return_value = _make_mock_dataframe([])

        # Step 1: Upload and get preview
        preview_url = reverse('quality_data:excel-preview', kwargs={'filename': 'test.xlsx'})
        with open('/dev/null', 'rb') as f:
            preview_response = self.client.post(preview_url, {'file': f}, format='multipart')

        self.assertEqual(preview_response.status_code, status.HTTP_200_OK)
        session_id = preview_response.data['session_id']

        # Step 2: Confirm
        confirm_url = reverse('quality_data:excel-confirm', kwargs={'session_id': session_id})
        confirm_response = self.client.post(confirm_url)

        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_response.data['status'], 'confirmed')

    @patch('quality_data.views.load_and_clean')
    def test_full_preview_reject_flow(self, mock_load_and_clean):
        """Complete flow: upload → get preview → reject → no data applied."""
        mock_load_and_clean.return_value = _make_mock_dataframe([])

        # Step 1: Upload and get preview
        preview_url = reverse('quality_data:excel-preview', kwargs={'filename': 'test.xlsx'})
        with open('/dev/null', 'rb') as f:
            preview_response = self.client.post(preview_url, {'file': f}, format='multipart')

        session_id = preview_response.data['session_id']

        # Step 2: Reject
        reject_url = reverse('quality_data:excel-reject', kwargs={'session_id': session_id})
        reject_response = self.client.delete(reject_url)

        self.assertEqual(reject_response.status_code, status.HTTP_200_OK)
        session = ExcelSyncSession.objects.get(pk=session_id)
        self.assertEqual(session.status, 'rejected')
