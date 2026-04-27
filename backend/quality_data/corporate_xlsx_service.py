from dataclasses import dataclass
from io import BytesIO
import datetime as dt

import xlsxwriter

from excel_importer.date_utils import (
    apply_charfield_iso_date_range,
    apply_datefield_date_range,
)
from excel_importer.sheet_configs import (
    CORPORATE_XLSX_EXPORT_CONFIG,
    SECONDS_GENERAL_DEFECT_COLUMNS,
    SECONDS_GENERAL_SEWING_DEFECTS,
    SECONDS_GENERAL_FABRIC_DEFECTS,
)
from quality_data.corporate_xlsx_styles import (
    CORPORATE_SHEET_ORDER,
    CORPORATE_DATA_SHEETS,
    CorporateXlsxFormats,
)
from quality_data.models import Container, QualityQcFa, SecondsA4, SecondsGeneral


class EmptyCorporateXlsxDataError(Exception):
    pass


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

    def generate(self, date_from, date_to):
        datasets = self.get_datasets(date_from, date_to)

        if not any(
            queryset.exists()
            for config in CORPORATE_XLSX_EXPORT_CONFIG
            if (queryset := datasets.get(config["dataset"]))
        ):
            raise EmptyCorporateXlsxDataError("No data for selected range.")

        buffer = BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        fmt = CorporateXlsxFormats(workbook)

        self._create_sheets(workbook, datasets, fmt)

        workbook.close()
        file_bytes = buffer.getvalue()

        return CorporateXlsxArtifact(
            file_bytes=file_bytes,
            filename=f"corporate-qa-report-{date_from.isoformat()}_to_{date_to.isoformat()}.xlsx",
        )

    def _create_sheets(self, workbook, datasets, fmt):
        sheet_indexes = {}
        for sheet_name in CORPORATE_SHEET_ORDER:
            ws = workbook.add_worksheet(sheet_name)
            sheet_indexes[sheet_name] = ws

            data_config = CORPORATE_DATA_SHEETS.get(sheet_name)
            if not data_config:
                continue

            dataset_config = next(
                (c for c in CORPORATE_XLSX_EXPORT_CONFIG if c["sheet_name"] == sheet_name),
                None,
            )
            if not dataset_config:
                continue

            queryset = datasets.get(dataset_config["dataset"])
            if queryset is None:
                continue

            rows = self._queryset_to_rows(queryset, dataset_config)
            columns = dataset_config["columns"]

            self._write_table(
                ws, sheet_name, data_config, columns, rows, fmt,
            )

    def _write_table(self, ws, sheet_name, data_config, columns, rows, fmt):
        hdr_row = data_config["hdr_row"]
        hdr_idx = hdr_row - 1
        data_start = hdr_row

        from excel_importer.sheet_configs import (
            QC_FA_PLANT_REMAP,
            QC_FA_CUSTOMER_REMAP,
            SECONDS_A4_REMAP,
            CONTAINER_REMAP,
        )

        if sheet_name == "QC FA Plant":
            reverse_map = {v: k for k, v in QC_FA_PLANT_REMAP.items()}
        elif sheet_name == "QC FA Customer":
            reverse_map = {v: k for k, v in QC_FA_CUSTOMER_REMAP.items()}
        elif sheet_name == "SecondsA4":
            reverse_map = {v: k for k, v in SECONDS_A4_REMAP.items()}
        elif sheet_name == "Seconds General":
            reverse_map = {
                'date': 'Date',
                'week': 'Week',
                'corrido_2': 'Corrido2',
                'barre': 'Barre',
                'otros_3': 'Otros3',
                'degradacion': 'Degradacion',
                'bordados': 'Bordados',
                'total_de_tela': 'Total de Tela',
            }
        elif sheet_name == "Container":
            reverse_map = {v: k for k, v in CONTAINER_REMAP.items()}
        else:
            reverse_map = {}

        header_names = [reverse_map.get(col, col) for col in columns]
        num_rows = len(rows)
        last_col_letter = xlsxwriter.utility.xl_col_to_name(len(columns) - 1)

        if num_rows > 0:
            last_data_row_1idx = hdr_row + num_rows
            table_ref = f"A{hdr_row}:{last_col_letter}{last_data_row_1idx}"
        else:
            # xlsxwriter requires at least one data row in the table range
            ws.write(hdr_row, 0, "")
            table_ref = f"A{hdr_row}:{last_col_letter}{hdr_row + 1}"

        ws.add_table(table_ref, {
            "name": data_config["table_name"],
            "columns": [{"header": h} for h in header_names],
            "autofilter": True if num_rows > 0 else False,
            "style": "Table Style Medium 2",
        })

        for row_offset, row_values in enumerate(rows):
            target_row = hdr_row + row_offset
            for col_idx, value in enumerate(row_values):
                data_fmt = fmt.data_for(sheet_name, col_idx)
                ws.write(target_row, col_idx, value, data_fmt)

        if hdr_row > 1:
            ws.freeze_panes(hdr_row, 0)

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

    @staticmethod
    def _queryset_to_rows(queryset, dataset_config):
        columns = dataset_config["columns"]
        row_builder = dataset_config.get("row_builder")

        if row_builder == "qc_fa":
            return CorporateXlsxReportService._build_qc_fa_rows(
                queryset=queryset,
                columns=columns,
                defect_columns=dataset_config.get("defect_columns", []),
            )
        if row_builder == "seconds_general":
            return CorporateXlsxReportService._build_seconds_general_rows(
                queryset=queryset,
                columns=columns,
            )
        if row_builder == "container":
            return CorporateXlsxReportService._build_container_rows(
                queryset=queryset,
                columns=columns,
                defect_columns=dataset_config.get("defect_columns", []),
            )

        values = queryset.order_by("pk").values_list(*columns)
        return [
            [CorporateXlsxReportService._normalize_cell_value(value) for value in row]
            for row in values
        ]

    @staticmethod
    def _build_qc_fa_rows(*, queryset, columns, defect_columns):
        rows = []
        defect_columns = set(defect_columns)
        inspections = queryset.select_related("color").prefetch_related(
            "inspection_defects__defect_type"
        ).order_by("pk")

        for inspection in inspections:
            defect_amounts = {
                defect.defect_type.name: defect.amount
                for defect in inspection.inspection_defects.all()
            }

            row = []
            for column in columns:
                if column == "color":
                    value = inspection.color.name if inspection.color_id else None
                elif column in defect_columns:
                    value = defect_amounts.get(column, 0)
                else:
                    value = getattr(inspection, column, None)

                row.append(CorporateXlsxReportService._normalize_cell_value(value))

            rows.append(row)

        return rows

    @staticmethod
    def _build_seconds_general_rows(*, queryset, columns):
        metadata_fields = {"date", "week", "line", "customer", "style", "artcode",
                           "color", "po", "size", "produced", "fixed", "definitive"}
        defect_set = set(SECONDS_GENERAL_DEFECT_COLUMNS)

        rows = []
        inspections = queryset.prefetch_related(
            "seconds_general_defects__defect_type"
        ).order_by("pk")

        for inspection in inspections:
            defect_amounts = {
                d.defect_type.name: d.amount
                for d in inspection.seconds_general_defects.all()
            }

            row = []
            for column in columns:
                if column in metadata_fields:
                    value = getattr(inspection, column, None)
                elif column in defect_set:
                    value = defect_amounts.get(column, 0)
                elif column == "total_de_costura":
                    value = sum(
                        defect_amounts.get(d, 0) for d in SECONDS_GENERAL_SEWING_DEFECTS
                    )
                elif column == "total_de_tela":
                    value = sum(
                        defect_amounts.get(d, 0) for d in SECONDS_GENERAL_FABRIC_DEFECTS
                    )
                else:
                    value = None

                row.append(CorporateXlsxReportService._normalize_cell_value(value))

            rows.append(row)

        return rows

    @staticmethod
    def _build_container_rows(*, queryset, columns, defect_columns):
        rows = []
        defect_columns = set(defect_columns)
        containers = queryset.prefetch_related("container_defects__defect_type").order_by("pk")

        for container in containers:
            defect_amounts = {
                defect.defect_type.name: defect.amount
                for defect in container.container_defects.all()
            }
            fallback_total_defects = sum(
                amount for name, amount in defect_amounts.items() if name != "total_defects"
            )

            row = []
            for column in columns:
                if column in defect_columns:
                    value = defect_amounts.get(column)
                    if column == "total_defects" and value is None:
                        value = fallback_total_defects
                    if value is None:
                        value = 0
                else:
                    value = getattr(container, column, None)

                row.append(CorporateXlsxReportService._normalize_cell_value(value))

            rows.append(row)

        return rows

    @staticmethod
    def _normalize_cell_value(value):
        if isinstance(value, (dt.date, dt.datetime)):
            return value.isoformat()
        return value
