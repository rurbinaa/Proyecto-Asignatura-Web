import datetime as dt
from io import BytesIO
from pathlib import Path
import tempfile

from django.test import SimpleTestCase, TestCase
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.table import Table

from quality_data.models import Color, QualityQcFa


class CorporateXlsxTemplateSelectionTest(SimpleTestCase):
    def test_uses_docs_canonical_template_path(self):
        from quality_data.corporate_xlsx_service import CorporateXlsxReportService

        service = CorporateXlsxReportService()

        expected = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "QA Data report 2025.xlsx"
        )
        self.assertEqual(service.template_path, expected)

    def test_rejects_placeholder_template_path(self):
        from quality_data.corporate_xlsx_service import CorporateXlsxReportService

        placeholder = (
            Path(__file__).resolve().parents[3]
            / "backend"
            / "excel_reports"
            / "excel_templates"
            / "plantilla_corporativa.xlsx"
        )

        with self.assertRaises(ValueError):
            CorporateXlsxReportService(template_path=placeholder)


class CorporateXlsxWorkbookFidelityTest(TestCase):
    def setUp(self):
        from quality_data.corporate_xlsx_service import CorporateXlsxReportService

        self.temp_dir = tempfile.TemporaryDirectory()
        self.template_path = Path(self.temp_dir.name) / "corporate-template.xlsx"
        self.target_tables = {
            "QC FA Plant": "Table3",
            "QC FA Customer": "Table2",
            "SecondsA4": "Table15",
            "Seconds General": "Table1",
            "Container": "Table18",
        }
        self._build_template_workbook(self.template_path)
        self.service = CorporateXlsxReportService(template_path=self.template_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_template_workbook(self, output_path):
        workbook = Workbook()
        workbook.remove(workbook.active)

        headers_by_sheet = {
            "QC FA Plant": ["Date", "Week", "Customer"],
            "QC FA Customer": ["Date", "Week", "Customer"],
            "SecondsA4": ["Date", "Week", "Value"],
            "Seconds General": ["Date", "Week", "Value"],
            "Container": ["Date", "Container", "Customer"],
        }

        for sheet_name, table_name in self.target_tables.items():
            worksheet = workbook.create_sheet(sheet_name)
            headers = headers_by_sheet[sheet_name]

            for col_index, header in enumerate(headers, start=1):
                worksheet.cell(row=1, column=col_index, value=header)

            worksheet.cell(row=2, column=1, value="TEMPLATE-DATA")
            worksheet.cell(row=2, column=2, value=0)
            worksheet.cell(row=2, column=3, value="TEMPLATE-DATA")

            worksheet.add_table(Table(displayName=table_name, ref="A1:C2"))

        workbook.save(output_path)
        workbook.close()

    def _create_qfa_record(self, *, date_1, customer):
        color = Color.objects.create(name=f"Navy-{date_1}-{customer}")
        return QualityQcFa.objects.create(
            table_type="QFA",
            date_1=date_1,
            week=3,
            customer=customer,
            team=1,
            coord="COORD-01",
            date_2=date_1,
            po=1001,
            style="ST-001",
            batch=11,
            color=color,
            qty=120,
            seconds=2,
            accepted=118,
            rejected=2,
            sample=20,
            defects_total=2,
            aql=1.67,
            pass_or_fail="Pass",
        )

    def test_generated_workbook_preserves_sheet_order_and_table_identifiers(self):
        self._create_qfa_record(date_1="2025-01-15", customer="InRange Co")

        artifact = self.service.generate(dt.date(2025, 1, 1), dt.date(2025, 1, 31))
        generated = load_workbook(BytesIO(artifact.file_bytes))

        self.assertEqual(generated.sheetnames, list(self.target_tables.keys()))
        for sheet_name, table_name in self.target_tables.items():
            self.assertIn(table_name, generated[sheet_name].tables.keys())

        generated.close()

    def test_generated_workbook_contains_only_filtered_qfa_rows_and_resized_table_ref(self):
        self._create_qfa_record(date_1="2025-01-15", customer="InRange Co")
        self._create_qfa_record(date_1="2025-03-05", customer="OutOfRange Co")

        artifact = self.service.generate(dt.date(2025, 1, 1), dt.date(2025, 1, 31))
        workbook = load_workbook(BytesIO(artifact.file_bytes))

        sheet = workbook["QC FA Plant"]
        table = sheet.tables["Table3"]

        self.assertEqual(table.ref, "A1:C2")
        self.assertEqual(sheet["A2"].value, "2025-01-15")
        self.assertEqual(sheet["C2"].value, "InRange Co")
        self.assertNotEqual(sheet["C2"].value, "OutOfRange Co")

        workbook.close()
