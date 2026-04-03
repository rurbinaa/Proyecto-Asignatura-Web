from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from quality_data.models import Color, DefectType
from .models import InspectionData, RevisionDefect, Mockup


class InspectionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='operator1', password='123')
        self.client.login(username='operator1', password='123')
        self.color = Color.objects.create(name="Red", is_active=True)
        self.defect_type = DefectType.objects.create(name="Stitching", is_active=True)

        self.inspection = InspectionData.objects.create(
            inspector=self.user,
            color=self.color,
            style="POLO-2026",
            size="XL",
        )
        self.mockup = Mockup.objects.create(name="Batch A", width=800, height=600)

    def test_create_defect_with_all_fields(self):
        url = reverse('media_data:defect-list')
        payload = {
            "inspection": self.inspection.id,
            "defect_type": self.defect_type.id,
            "defect_size": "XL",
            "notes": "Frayed edges near the collar",
            "defect_count": 3,
            "coordinates_x": [150.0],
            "coordinates_y": [300.0],
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        last_defect = RevisionDefect.objects.last()
        self.assertEqual(last_defect.inspector, self.user)
        self.assertEqual(last_defect.notes, "Frayed edges near the collar")
        self.assertEqual(last_defect.defect_count, 3)

    def test_close_inspection_with_defects_returns_reject(self):
        """Closing an inspection with defects sets status to REJECT."""
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Medium",
            defect_count=1,
        )
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['result'], 'REJECT')
        self.assertEqual(response.data['total_defects'], 1)
        self.inspection.refresh_from_db()
        self.assertTrue(self.inspection.is_closed)

    def test_close_inspection_without_defects_returns_pass(self):
        """Closing an inspection with no defects sets status to PASS."""
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

    def test_close_inspection_already_closed(self):
        """Closing an already-closed inspection returns 400."""
        self.inspection.is_closed = True
        self.inspection.save()
        url = reverse(
            'media_data:inspection-close-inspection',
            kwargs={'pk': self.inspection.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_undo_last_defect(self):
        RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Medium",
            defect_count=1,
        )
        url = f"{reverse('media_data:defect-undo')}?inspection={self.inspection.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_undo_verifies_deletion(self):
        """Undo actually removes the defect from the database."""
        defect = RevisionDefect.objects.create(
            inspection=self.inspection,
            inspector=self.user,
            defect_type=self.defect_type,
            defect_size="Medium",
            defect_count=1,
        )
        defect_id = defect.pk
        url = f"{reverse('media_data:defect-undo')}?inspection={self.inspection.id}"
        self.client.delete(url)
        self.assertFalse(RevisionDefect.objects.filter(pk=defect_id).exists())

    def test_undo_requires_inspection_param(self):
        """Undo returns 400 if inspection query param is missing."""
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_undo_no_defects_returns_404(self):
        """Undo returns 404 if no defects exist for the inspection."""
        url = f"{reverse('media_data:defect-undo')}?inspection={self.inspection.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_mockup_info(self):
        url = reverse('media_data:mockup-detail', kwargs={'pk': self.mockup.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['width'], 800)
