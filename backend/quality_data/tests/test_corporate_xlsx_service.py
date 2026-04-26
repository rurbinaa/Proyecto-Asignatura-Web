from pathlib import Path

from django.test import SimpleTestCase


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
