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
            size="XL"
        )
        self.mockup = Mockup.objects.create(name="Batch A", width=800, height=600)

    def test_create_defect_with_all_fields(self):
        url = reverse('media_data:defect-list')
        payload = {
            "inspection": self.inspection.id,
            "inspector": self.user.id,
            "defectType": self.defect_type.id,
            "defectSize": "XL",
            "notes": "Frayed edges near the collar",
            "defectCount": 3,
            "coordinates_x": [150.0],
            "coordinates_y": [300.0]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        last_defect = RevisionDefect.objects.last()
        self.assertEqual(last_defect.inspector, self.user)
        self.assertEqual(last_defect.notes, "Frayed edges near the collar")
        self.assertEqual(last_defect.defectCount, 3)

    def test_close_inspection_successfully(self):
        url = reverse('media_data:inspection-close-inspection', kwargs={'pk': self.inspection.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.inspection.refresh_from_db()
        self.assertTrue(self.inspection.is_closed)
        self.assertIsNotNone(self.inspection.closed_at)

    def test_undo_last_defect(self):
        RevisionDefect.objects.create(
            inspection=self.inspection, 
            inspector=self.user,
            defectType=self.defect_type, 
            defectSize="Medium",
            defectCount=1
        )
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_mockup_info(self):
        url = reverse('media_data:mockup-detail', kwargs={'pk': self.mockup.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['width'], 800)

    def test_error_if_no_records_to_undo(self):
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)