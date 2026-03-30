from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from quality_data.models import Color, DefectType
from .models import InspectionData, RevisionDefect, Mockup

class InspectionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='operario1', password='123')
        self.client.login(username='operario1', password='123')

        self.color = Color.objects.create(name="Rojo", is_active=True)
        self.tipo_defecto = DefectType.objects.create(name="Costura", is_active=True)
        
        self.inspeccion = InspectionData.objects.create(inspector=self.user, color=self.color)
        self.maqueta = Mockup.objects.create(name="Lote A", width=800, height=600)

    def test_crear_defecto_exitoso(self):
        url = reverse('media_data:defect-list')
        payload = {
            "inspection": self.inspeccion.id,
            "defectType": self.tipo_defecto.id,
            "defectSize": "S",
            "coordinates_x": [100.5],
            "coordinates_y": [200.0]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_deshacer_ultimo_defecto(self):
        RevisionDefect.objects.create(
            inspection=self.inspeccion, inspector=self.user,
            defectType=self.tipo_defecto, defectSize="M"
        )
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_obtener_info_maqueta(self):
        url = reverse('media_data:mockup-detail', kwargs={'pk': self.maqueta.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['width'], 800)

    def test_error_si_no_hay_registros_para_deshacer(self):
        url = reverse('media_data:defect-undo')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)