from xlsxwriter.workbook import Format, Workbook


class CorporateXlsxFormats:
    def __init__(self, workbook: Workbook) -> None:
        self.workbook = workbook
        self._build()

    def _add(self) -> Format:
        return self.workbook.add_format()

    def _build(self) -> None:
        # ── QC FA Plant (header row 3) ───────────────────────────────
        self.qfa_hdr = self._add()
        self.qfa_hdr.set_font_name("Calibri")
        self.qfa_hdr.set_font_size(9)
        self.qfa_hdr.set_bold()
        self.qfa_hdr.set_left(1)
        self.qfa_hdr.set_right(1)
        self.qfa_hdr.set_bottom(2)

        self.qfa_hdr_first = self._add()
        self.qfa_hdr_first.set_font_name("Calibri")
        self.qfa_hdr_first.set_font_size(9)
        self.qfa_hdr_first.set_bold()
        self.qfa_hdr_first.set_left(2)
        self.qfa_hdr_first.set_right(1)
        self.qfa_hdr_first.set_bottom(2)

        self.qfa_data = self._add()
        self.qfa_data.set_font_name("Calibri")
        self.qfa_data.set_font_size(10)
        self.qfa_data.set_border(1)

        # ── QC FA Customer (header row 1) ────────────────────────────
        self.qfc_hdr = self._add()
        self.qfc_hdr.set_font_name("Calibri")
        self.qfc_hdr.set_font_size(9)
        self.qfc_hdr.set_bold()
        self.qfc_hdr.set_font_color("#FFFFFF")
        self.qfc_hdr.set_bg_color("#4472C4")
        self.qfc_hdr.set_left(1)
        self.qfc_hdr.set_right(1)
        self.qfc_hdr.set_bottom(2)
        self.qfc_hdr.set_align("center")

        self.qfc_data = self._add()
        self.qfc_data.set_font_name("Calibri")
        self.qfc_data.set_font_size(11)
        self.qfc_data.set_border(1)

        # ── SecondsA4 (header row 2) ─────────────────────────────────
        self.sa4_hdr = self._add()
        self.sa4_hdr.set_font_name("Calibri")
        self.sa4_hdr.set_font_size(11)
        self.sa4_hdr.set_bold()
        self.sa4_hdr.set_bg_color("#D6DCE4")
        self.sa4_hdr.set_border(1)
        self.sa4_hdr.set_align("center")

        self.sa4_data = self._add()
        self.sa4_data.set_font_name("Calibri")
        self.sa4_data.set_font_size(10)
        self.sa4_data.set_border(1)

        # ── Seconds General (header row 2) ────────────────────────────
        self.sg_hdr_date = self._add()
        self.sg_hdr_date.set_font_name("Calibri")
        self.sg_hdr_date.set_font_size(14)
        self.sg_hdr_date.set_bold()

        self.sg_hdr = self._add()
        self.sg_hdr.set_font_name("Calibri")
        self.sg_hdr.set_font_size(11)
        self.sg_hdr.set_bold()
        self.sg_hdr.set_left(1)
        self.sg_hdr.set_right(1)
        self.sg_hdr.set_bottom(1)

        self.sg_data = self._add()
        self.sg_data.set_font_name("Calibri")
        self.sg_data.set_font_size(11)
        self.sg_data.set_border(1)

        # ── Container (header row 3) ──────────────────────────────────
        self.ctr_title = self._add()
        self.ctr_title.set_font_name("Aptos Narrow")
        self.ctr_title.set_font_size(16)
        self.ctr_title.set_bold()
        self.ctr_title.set_left(1)
        self.ctr_title.set_right(1)
        self.ctr_title.set_top(1)
        self.ctr_title.set_bottom(0)

        self.ctr_hdr = self._add()
        self.ctr_hdr.set_font_name("Calibri")
        self.ctr_hdr.set_font_size(14)
        self.ctr_hdr.set_bold()
        self.ctr_hdr.set_left(1)
        self.ctr_hdr.set_right(1)

        self.ctr_hdr_wide = self._add()
        self.ctr_hdr_wide.set_font_name("Calibri")
        self.ctr_hdr_wide.set_font_size(16)
        self.ctr_hdr_wide.set_bold()
        self.ctr_hdr_wide.set_left(1)
        self.ctr_hdr_wide.set_right(1)

        self.ctr_data = self._add()
        self.ctr_data.set_font_name("Calibri")
        self.ctr_data.set_font_size(11)
        self.ctr_data.set_border(1)

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
        return self._add()

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
        return self._add()


CORPORATE_SHEET_ORDER = [
    "QC FA Plant",
    "QC FA Customer",
    "SecondsA4",
    "Seconds General",
    "Container",
    "GeneralGraphics",
]

CORPORATE_DATA_SHEETS = {
    "QC FA Plant": {"table_name": "Table3", "hdr_row": 3},
    "QC FA Customer": {"table_name": "Table2", "hdr_row": 1},
    "SecondsA4": {"table_name": "Table15", "hdr_row": 2},
    "Seconds General": {"table_name": "Table1", "hdr_row": 2},
    "Container": {"table_name": "Table18", "hdr_row": 3},
}
