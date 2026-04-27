from xlsxwriter.workbook import Format, Workbook


class CorporateXlsxFormats:
    def __init__(self, workbook: Workbook) -> None:
        self.workbook = workbook
        self._build()

    def _fmt(self, **kwargs) -> Format:
        return self.workbook.add_format(kwargs)

    def _build(self) -> None:
        # ── Borders ──────────────────────────────────────────────────
        thin_all = {"border": 1}
        thin_sides_bottom = {"left": 1, "right": 1, "bottom": 1}

        # ── QC FA Plant (header row 3) ───────────────────────────────
        self.qfa_hdr = self._fmt(
            font_name="Calibri", font_size=9, bold=True,
            left=1, right=1, bottom=2,
        )
        self.qfa_hdr_first = self._fmt(
            font_name="Calibri", font_size=9, bold=True,
            left=2, right=1, bottom=2,
        )
        self.qfa_data = self._fmt(
            font_name="Calibri", font_size=10, **thin_all,
        )

        # ── QC FA Customer (header row 1) ────────────────────────────
        self.qfc_hdr = self._fmt(
            font_name="Calibri", font_size=9, bold=True,
            font_color="#FFFFFF", bg_color="#FFFFFF",
            left=1, right=1, bottom=2,
        )
        self.qfc_hdr_date = self._fmt(
            font_name="Calibri", font_size=9, bold=True,
            font_color="#FFFFFF", bg_color="#FFFFFF",
            left=1, right=1, bottom=2,
            num_format="dd\\-mmm",
        )
        self.qfc_data = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
        )
        self.qfc_data_date = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
            num_format="dd\\-mmm",
        )
        self.qfc_data_pct = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
            num_format="0.0%",
        )

        # ── SecondsA4 (header row 2) ─────────────────────────────────
        self.sa4_hdr = self._fmt(
            font_name="Calibri", font_size=11, bold=True,
            font_color="#000000", bg_color="#E8E8E8",
        )
        self.sa4_data = self._fmt(
            font_name="Calibri", font_size=10, **thin_all,
        )
        self.sa4_data_date = self._fmt(
            font_name="Calibri", font_size=10, **thin_all,
            num_format="dd\\-mmm\\-yy",
        )
        self.sa4_data_pct = self._fmt(
            font_name="Calibri", font_size=10, **thin_all,
            num_format="0.00%",
        )

        # ── Seconds General (header row 2, 8 cols) ───────────────────
        self.sg_hdr_date = self._fmt(
            font_name="Calibri", font_size=14, bold=True,
        )
        self.sg_hdr = self._fmt(
            font_name="Calibri", font_size=11, bold=True,
            **thin_sides_bottom,
        )
        self.sg_data = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
        )

        # ── Container (header row 3) ──────────────────────────────────
        self.ctr_title = self._fmt(
            font_name="Aptos Narrow", font_size=16, bold=True,
            left=1, right=1, top=1, bottom=0,
        )
        self.ctr_subtitle = self._fmt(
            font_name="Calibri", font_size=16, bold=True,
        )
        self.ctr_hdr = self._fmt(
            font_name="Calibri", font_size=14, bold=True,
            left=1, right=1,
        )
        self.ctr_hdr_wide = self._fmt(
            font_name="Calibri", font_size=16, bold=True,
            left=1, right=1,
        )
        self.ctr_data = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
        )
        self.ctr_data_pct = self._fmt(
            font_name="Calibri", font_size=11, **thin_all,
            num_format="0.0%",
        )

    def hdr_for(self, sheet_name: str, col_idx: int) -> Format:
        if sheet_name == "QC FA Plant":
            return self.qfa_hdr_first if col_idx == 0 else self.qfa_hdr
        if sheet_name == "QC FA Customer":
            return self.qfc_hdr
        if sheet_name == "SecondsA4":
            return self.sa4_hdr
        if sheet_name == "Seconds General":
            return self.sg_hdr_date if col_idx == 0 else self.sg_hdr
        if sheet_name == "Container":
            return self.ctr_hdr if col_idx == 0 else self.ctr_hdr_wide
        return self._fmt()

    def data_for(self, sheet_name: str, col_idx: int) -> Format:
        if sheet_name == "QC FA Plant":
            return self.qfa_data
        if sheet_name == "QC FA Customer":
            return self.qfc_data
        if sheet_name == "SecondsA4":
            return self.sa4_data
        if sheet_name == "Seconds General":
            return self.sg_data
        if sheet_name == "Container":
            return self.ctr_data
        return self._fmt()


CORPORATE_SHEET_ORDER = [
    "Trims",
    "Packing Audit",
    "Sewing Endline 100% inspection",
    "Sewing In-Line",
    "QC FA Plant",
    "QC FA Customer",
    "SecondsA4",
    "Seconds General",
    "GraphxLine",
    "Container",
    "GeneralGraphics",
    "Thirds",
]

CORPORATE_DATA_SHEETS = {
    "QC FA Plant": {
        "table_name": "Table3",
        "hdr_row": 3,
    },
    "QC FA Customer": {
        "table_name": "Table2",
        "hdr_row": 1,
    },
    "SecondsA4": {
        "table_name": "Table15",
        "hdr_row": 2,
    },
    "Seconds General": {
        "table_name": "Table1",
        "hdr_row": 2,
    },
    "Container": {
        "table_name": "Table18",
        "hdr_row": 3,
    },
}
