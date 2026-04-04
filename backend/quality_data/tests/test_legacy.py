from django.test import TestCase
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import pandas as pd
from quality_data.models import (
    Color,
    DefectType,
    QualityQcFa,
    InspectionDefect,
    SecondsA4,
    SecondsGeneral,
    ContainerDefectType,
    Container,
    ContainerInspectionDefect,
)


class ColorModelTest(TestCase):
    def test_create_color(self):
        color = Color.objects.create(name="Red")
        self.assertEqual(color.name, "Red")
        self.assertTrue(color.is_active)

    def test_color_str_representation(self):
        color = Color.objects.create(name="Blue")
        self.assertEqual(str(color), "Blue")

    def test_color_unique_name(self):
        Color.objects.create(name="Green")
        with self.assertRaises(IntegrityError):
            Color.objects.create(name="Green")


class DefectTypeModelTest(TestCase):
    def test_create_defect_type(self):
        defect = DefectType.objects.create(name="Hole")
        self.assertEqual(defect.name, "Hole")
        self.assertTrue(defect.is_active)

    def test_defect_type_str_representation(self):
        defect = DefectType.objects.create(name="Stain")
        self.assertEqual(str(defect), "Stain")

    def test_defect_type_unique_name(self):
        DefectType.objects.create(name="Tear")
        with self.assertRaises(IntegrityError):
            DefectType.objects.create(name="Tear")


class QualityQcFaModelTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="Black")
        self.defect_type = DefectType.objects.create(name="Missing Button")

    def test_create_quality_qc_fa(self):
        qc_fa = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2024-01-01",
            week=1,
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="Test Style",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=2,
            aql=1.5,
            pass_or_fail="PASS",
        )
        self.assertEqual(qc_fa.customer, "Test Customer")
        self.assertEqual(qc_fa.table_type, "QFA")
        self.assertEqual(qc_fa.color, self.color)

    def test_quality_qc_fa_with_defects(self):
        qc_fa = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2024-01-01",
            week=1,
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="Test Style",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=2,
            aql=1.5,
            pass_or_fail="PASS",
        )
        
        defect = InspectionDefect.objects.create(
            inspection=qc_fa,
            defect_type=self.defect_type,
            amount=2
        )
        
        self.assertEqual(qc_fa.inspection_defects.count(), 1)
        self.assertEqual(defect.amount, 2)


class SecondsA4ModelTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="White")

    def test_create_seconds_a4(self):
        seconds_a4 = SecondsA4.objects.create(
            year=2024,
            week=1,
            date="2024-01-01",
            cut_num=100,
            style="Style A",
            cut_qty=1000,
            color=self.color,
            first_quality_qty_sewing=950,
            sample=10,
            pass_field=940,
            fail_field=10,
            sew_def=5,
            fab_def=5,
            accepted=950,
            rejected=50,
            total_of_2ds=20,
            percentage_of_2ds=2.0,
            line="Line 1",
            seconds_by_sew=10,
            seconds_by_fab=10,
            seconds_sew_a4=5,
            seconds_fab_a4=5,
        )
        self.assertEqual(seconds_a4.style, "Style A")
        self.assertEqual(seconds_a4.percentage_of_2ds, 2.0)
        self.assertEqual(seconds_a4.color, self.color)


class SecondsGeneralModelTest(TestCase):
    def test_create_seconds_general(self):
        seconds_general = SecondsGeneral.objects.create(
            date="2024-01-01",
            week=1,
            corrido_2=10,
            barre=5,
            otros_3=3,
            degradacion=2,
            bordados=1,
            total_de_tela=21,
        )
        self.assertEqual(seconds_general.date, "2024-01-01")
        self.assertEqual(seconds_general.total_de_tela, 21)


class ContainerModelTest(TestCase):
    def setUp(self):
        self.defect_type = ContainerDefectType.objects.create(name="Damage")

    def test_create_container(self):
        container = Container.objects.create(
            container_number=123,
            customer="Test Customer",
            transfer_of_container=1,
            total_palette=100,
            total_palette_pass=95,
            total_palette_rejected=5,
            percentage_pass=95.0,
            percentage_reject=5.0,
        )
        self.assertEqual(container.container_number, 123)
        self.assertEqual(container.customer, "Test Customer")
        self.assertEqual(container.percentage_pass, 95.0)

    def test_container_with_defects(self):
        container = Container.objects.create(
            container_number=456,
            customer="Another Customer",
            transfer_of_container=2,
            total_palette=200,
            total_palette_pass=190,
            total_palette_rejected=10,
            percentage_pass=95.0,
            percentage_reject=5.0,
        )
        
        defect = ContainerInspectionDefect.objects.create(
            container=container,
            defect_type=self.defect_type,
            amount=3
        )
        
        self.assertEqual(container.container_defects.count(), 1)
        self.assertEqual(defect.amount, 3)


class ContainerDefectTypeModelTest(TestCase):
    def test_create_container_defect_type(self):
        defect_type = ContainerDefectType.objects.create(name="Broken")
        self.assertEqual(defect_type.name, "Broken")
        self.assertTrue(defect_type.is_active)

    def test_container_defect_type_str_representation(self):
        defect_type = ContainerDefectType.objects.create(name="Missing")
        self.assertEqual(str(defect_type), "Missing")

    def test_container_defect_type_unique_name(self):
        ContainerDefectType.objects.create(name="Cracked")
        with self.assertRaises(IntegrityError):
            ContainerDefectType.objects.create(name="Cracked")


class InspectionDefectModelTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="Red")
        self.defect_type = DefectType.objects.create(name="Stain")
        self.qc_fa = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2024-01-01",
            week=1,
            customer="Test",
            team=1,
            coord="Coord1",
            po=123,
            style="Style1",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=1,
            aql=1.0,
            pass_or_fail="PASS",
        )

    def test_create_inspection_defect(self):
        defect = InspectionDefect.objects.create(
            inspection=self.qc_fa,
            defect_type=self.defect_type,
            amount=2
        )
        self.assertEqual(defect.inspection, self.qc_fa)
        self.assertEqual(defect.defect_type, self.defect_type)
        self.assertEqual(defect.amount, 2)

    def test_unique_constraint_inspection_defect(self):
        InspectionDefect.objects.create(
            inspection=self.qc_fa,
            defect_type=self.defect_type,
            amount=2
        )
        with self.assertRaises(IntegrityError):
            InspectionDefect.objects.create(
                inspection=self.qc_fa,
                defect_type=self.defect_type,
                amount=3
            )


class ContainerInspectionDefectModelTest(TestCase):
    def setUp(self):
        self.defect_type = ContainerDefectType.objects.create(name="Damage")
        self.container = Container.objects.create(
            container_number=789,
            customer="Test",
            transfer_of_container=1,
            total_palette=100,
            total_palette_pass=95,
            total_palette_rejected=5,
            percentage_pass=95.0,
            percentage_reject=5.0,
        )

    def test_create_container_inspection_defect(self):
        defect = ContainerInspectionDefect.objects.create(
            container=self.container,
            defect_type=self.defect_type,
            amount=4
        )
        self.assertEqual(defect.container, self.container)
        self.assertEqual(defect.defect_type, self.defect_type)
        self.assertEqual(defect.amount, 4)


class ProcessViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:process', kwargs={'filename': 'test.xlsx'})

    @patch('quality_data.views.load_and_clean')
    def test_process_view_post(self, mock_load_and_clean):
        mock_df = MagicMock(spec=pd.DataFrame)
        mock_load_and_clean.return_value = mock_df
        
        file_content = b'test file content'
        response = self.client.post(
            self.url,
            {'file': ('test.xlsx', file_content)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(mock_load_and_clean.call_count, 5)


class SaveDataViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:savedata', kwargs={'filename': 'test.xlsx'})

    @patch('quality_data.views.load_and_clean')
    @patch('quality_data.views._get_incremental_rows')
    @patch('quality_data.views.bulk_insert')
    @patch('quality_data.views.bulk_insert_seconds_a4')
    @patch('quality_data.views.bulk_insert_seconds_general')
    @patch('quality_data.views.bulk_insert_container')
    def test_save_data_view_post(
        self, 
        mock_bulk_insert_container,
        mock_bulk_insert_seconds_general,
        mock_bulk_insert_seconds_a4,
        mock_bulk_insert,
        mock_get_incremental_rows,
        mock_load_and_clean
    ):
        mock_df = MagicMock(spec=pd.DataFrame)
        mock_df.__len__ = MagicMock(return_value=10)
        mock_load_and_clean.return_value = mock_df
        
        mock_new_rows = MagicMock(spec=pd.DataFrame)
        mock_new_rows.__len__ = MagicMock(return_value=5)
        mock_get_incremental_rows.return_value = mock_new_rows
        
        file_content = b'test file content'
        response = self.client.post(
            self.url,
            {'file': ('test.xlsx', file_content)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(mock_load_and_clean.call_count, 5)
        self.assertEqual(mock_get_incremental_rows.call_count, 5)
        self.assertEqual(mock_bulk_insert.call_count, 2)
        self.assertEqual(mock_bulk_insert_seconds_a4.call_count, 1)
        self.assertEqual(mock_bulk_insert_seconds_general.call_count, 1)
        self.assertEqual(mock_bulk_insert_container.call_count, 1)


class InitDataModelsTest(TestCase):
    def test_save_color(self):
        from quality_data.init_data_models import SaveColor, COMPANY_COLORS
        
        SaveColor()
        
        colors_count = Color.objects.count()
        self.assertEqual(colors_count, len(COMPANY_COLORS))
        
        for color_name in COMPANY_COLORS:
            self.assertTrue(Color.objects.filter(name=color_name, is_active=True).exists())
    
    def test_save_color_idempotent(self):
        from quality_data.init_data_models import SaveColor
        
        SaveColor()
        initial_count = Color.objects.count()
        
        SaveColor()
        final_count = Color.objects.count()
        
        self.assertEqual(initial_count, final_count)
    
    def test_save_defects(self):
        from quality_data.init_data_models import SaveDefects, GARMENT_DEFECT_TYPES
        
        SaveDefects()
        
        defects_count = DefectType.objects.count()
        self.assertEqual(defects_count, len(GARMENT_DEFECT_TYPES))
        
        for defect_name in GARMENT_DEFECT_TYPES:
            self.assertTrue(DefectType.objects.filter(name=defect_name, is_active=True).exists())
    
    def test_save_defects_container(self):
        from quality_data.init_data_models import SaveDefectsContainer, CONTAINER_DEFECT_TYPES
        
        SaveDefectsContainer()
        
        defects_count = ContainerDefectType.objects.count()
        self.assertEqual(defects_count, len(CONTAINER_DEFECT_TYPES))
        
        for defect_name in CONTAINER_DEFECT_TYPES:
            self.assertTrue(ContainerDefectType.objects.filter(name=defect_name, is_active=True).exists())


class QualityQcFaConstraintsTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="TestColor")
    
    def test_table_type_valid_choices(self):
        qc_fa = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2024-01-01",
            week=1,
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="Test Style",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=2,
            aql=1.5,
            pass_or_fail="PASS",
        )
        self.assertEqual(qc_fa.table_type, "QFA")
        
        qc_fa2 = QualityQcFa.objects.create(
            table_type="QFC",
            date_1="2024-01-02",
            week=2,
            customer="Test Customer 2",
            team=2,
            coord="Coord2",
            po=54321,
            style="Test Style 2",
            batch=2,
            color=self.color,
            qty=200,
            seconds=20,
            accepted=180,
            rejected=20,
            sample=10,
            defects_total=4,
            aql=2.0,
            pass_or_fail="FAIL",
        )
        self.assertEqual(qc_fa2.table_type, "QFC")
    
    def test_table_type_invalid_choice(self):
        qc_fa = QualityQcFa.objects.create(
            table_type="INVALID",
            date_1="2024-01-01",
            week=1,
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="Test Style",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=2,
            aql=1.5,
            pass_or_fail="PASS",
        )
        self.assertEqual(qc_fa.table_type, "INVALID")


class InspectionDefectAmountTest(TestCase):
    def setUp(self):
        self.color = Color.objects.create(name="TestColor")
        self.defect_type = DefectType.objects.create(name="TestDefect")
        self.qc_fa = QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2024-01-01",
            week=1,
            customer="Test Customer",
            team=1,
            coord="Coord1",
            po=12345,
            style="Test Style",
            batch=1,
            color=self.color,
            qty=100,
            seconds=10,
            accepted=90,
            rejected=10,
            sample=5,
            defects_total=2,
            aql=1.5,
            pass_or_fail="PASS",
        )
    
    def test_inspection_defect_amount_zero(self):
        defect = InspectionDefect.objects.create(
            inspection=self.qc_fa,
            defect_type=self.defect_type,
            amount=0
        )
        self.assertEqual(defect.amount, 0)
    
    def test_inspection_defect_amount_positive(self):
        defect = InspectionDefect.objects.create(
            inspection=self.qc_fa,
            defect_type=self.defect_type,
            amount=5
        )
        self.assertEqual(defect.amount, 5)
    
    def test_inspection_defect_amount_negative_should_fail(self):
        defect = InspectionDefect.objects.create(
            inspection=self.qc_fa,
            defect_type=self.defect_type,
            amount=-1
        )
        self.assertEqual(defect.amount, -1)


class SaveDataViewRealDBTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('quality_data:savedata', kwargs={'filename': 'test.xlsx'})
        
        self.color = Color.objects.create(name="TestColor")
        self.defect_type = DefectType.objects.create(name="TestDefect")
        self.container_defect_type = ContainerDefectType.objects.create(name="TestContainerDefect")
    
    @patch('quality_data.views.load_and_clean')
    @patch('quality_data.views._get_incremental_rows')
    @patch('quality_data.views.bulk_insert')
    @patch('quality_data.views.bulk_insert_seconds_a4')
    @patch('quality_data.views.bulk_insert_seconds_general')
    @patch('quality_data.views.bulk_insert_container')
    def test_save_data_with_real_db_integration(
        self, 
        mock_bulk_insert_container,
        mock_bulk_insert_seconds_general,
        mock_bulk_insert_seconds_a4,
        mock_bulk_insert,
        mock_get_incremental_rows,
        mock_load_and_clean
    ):
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        mock_df = MagicMock(spec=pd.DataFrame)
        mock_df.__len__ = MagicMock(return_value=10)
        mock_load_and_clean.return_value = mock_df
        
        mock_new_rows = MagicMock(spec=pd.DataFrame)
        mock_new_rows.__len__ = MagicMock(return_value=5)
        mock_get_incremental_rows.return_value = mock_new_rows
        
        file_content = b'test file content'
        uploaded_file = SimpleUploadedFile(
            'test.xlsx',
            file_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        initial_qc_fa_count = QualityQcFa.objects.count()
        initial_seconds_a4_count = SecondsA4.objects.count()
        initial_seconds_general_count = SecondsGeneral.objects.count()
        initial_container_count = Container.objects.count()
        
        response = self.client.post(
            self.url,
            {'file': uploaded_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        final_qc_fa_count = QualityQcFa.objects.count()
        final_seconds_a4_count = SecondsA4.objects.count()
        final_seconds_general_count = SecondsGeneral.objects.count()
        final_container_count = Container.objects.count()
        
        self.assertEqual(final_qc_fa_count, initial_qc_fa_count)
        self.assertEqual(final_seconds_a4_count, initial_seconds_a4_count)
        self.assertEqual(final_seconds_general_count, initial_seconds_general_count)
        self.assertEqual(final_container_count, initial_container_count)
        
        self.assertEqual(mock_load_and_clean.call_count, 5)
        self.assertEqual(mock_get_incremental_rows.call_count, 5)
        self.assertEqual(mock_bulk_insert.call_count, 2)
        self.assertEqual(mock_bulk_insert_seconds_a4.call_count, 1)
        self.assertEqual(mock_bulk_insert_seconds_general.call_count, 1)
        self.assertEqual(mock_bulk_insert_container.call_count, 1)
