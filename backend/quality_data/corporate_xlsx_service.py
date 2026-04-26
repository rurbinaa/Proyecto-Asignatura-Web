from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from excel_importer.date_utils import (
    apply_charfield_iso_date_range,
    apply_datefield_date_range,
)
from excel_importer.sheet_configs import (
    CORPORATE_XLSX_CANONICAL_TEMPLATE_RELATIVE_PATH,
    CORPORATE_XLSX_EXPORT_CONFIG,
    CORPORATE_XLSX_PLACEHOLDER_TEMPLATE_RELATIVE_PATH,
)
from quality_data.models import Container, QualityQcFa, SecondsA4, SecondsGeneral


class EmptyCorporateXlsxDataError(Exception):
    """Raised when no reportable rows exist for the requested range."""


@dataclass
class CorporateXlsxArtifact:
    file_bytes: bytes
    filename: str


class CorporateXlsxReportService:
    MODEL_REGISTRY = {
        "QualityQcFa": QualityQcFa,
        "SecondsA4": SecondsA4,
        "SecondsGeneral": SecondsGeneral,
        "Container": Container,
    }

    def __init__(self, template_path=None):
        self.project_root = Path(__file__).resolve().parents[2]
        self.template_path = self._resolve_template_path(template_path)

    def generate(self, date_from, date_to):
        datasets = self.get_datasets(date_from, date_to)
        if not any(dataset.exists() for dataset in datasets.values()):
            raise EmptyCorporateXlsxDataError("No data for selected range.")

        workbook = load_workbook(self.template_path)
        output = BytesIO()
        workbook.save(output)
        workbook.close()

        return CorporateXlsxArtifact(
            file_bytes=output.getvalue(),
            filename=f"corporate-qa-report-{date_from.isoformat()}_to_{date_to.isoformat()}.xlsx",
        )

    def get_datasets(self, date_from, date_to):
        datasets = {}

        for dataset_config in CORPORATE_XLSX_EXPORT_CONFIG:
            model_class = self.MODEL_REGISTRY[dataset_config["model"]]
            queryset = model_class.objects.filter(**dataset_config["queryset_filters"])

            if dataset_config["date_field_type"] == "date":
                queryset = apply_datefield_date_range(
                    queryset,
                    dataset_config["date_field"],
                    date_from,
                    date_to,
                )
            else:
                queryset = apply_charfield_iso_date_range(
                    queryset,
                    dataset_config["date_field"],
                    date_from,
                    date_to,
                )

            datasets[dataset_config["dataset"]] = queryset

        return datasets

    def _resolve_template_path(self, template_path):
        if template_path:
            resolved_path = Path(template_path).resolve()
        else:
            resolved_path = self.project_root.joinpath(
                *CORPORATE_XLSX_CANONICAL_TEMPLATE_RELATIVE_PATH
            )

        placeholder_path = self.project_root.joinpath(
            *CORPORATE_XLSX_PLACEHOLDER_TEMPLATE_RELATIVE_PATH
        ).resolve()

        if resolved_path == placeholder_path:
            raise ValueError("Placeholder template is forbidden for corporate XLSX reports.")

        return resolved_path
