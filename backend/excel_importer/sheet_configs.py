SHEET_NAMES = [
    ("QC FA Plant", 2, 67),
    ("QC FA Customer", 0, 64),
    ("SecondsA4", 1, 22),
    ("Seconds General", 1, 38),
    ("Container", 2, 24),
]

QC_FA_PLANT_REMAP = {
    'Date': 'date_1',
    'Week': 'week',
    'Customer': 'customer',
    'Team': 'team',
    'COORD.': 'coord',
    'Date2': 'date_2',
    'Po': 'po',
    'Style': 'style',
    'Batch': 'batch',
    'Color': 'color',
    'Qty': 'qty',
    'Column2': 'column2',
    'Seconds': 'seconds',
    'Accepted': 'accepted',
    'Rejected': 'rejected',
    'Sample': 'sample',
    'Defects': 'defects_total',
    'AQL %': 'aql',
    'Pass/Fail': 'pass_or_fail',
    'Uneven': 'uneven',
    'Broken Stitch': 'broken_stitch',
    'Open seam': 'open_seam',
    'Tear': 'tear',
    'Hi Low': 'hi_low',
    'Run Off Stitch': 'run_off_stitch',
    'Raw Edge': 'raw_edge',
    'Needle Holes': 'neddle_holes',
    'Loose Thread': 'loose_thread',
    'Uncut Thread': 'uncut_thread',
    'Big/Litter Neck': 'big_or_littler_neck',
    'Uneven Neck / Sleeve': 'uneven_neck_or_sleeve',
    'Out of Measurements': 'out_of_measurements',
    'incorrect Stitch': 'incorrect_stitch',
    'Variation Tension Stitch': 'variation_tension_sttich',
    'Excess Fabric': 'excess_fabric',
    'Hitched': 'hitched',
    'PO Mixed': 'po_midex',
    'Transfer Peel off, Leve': 'transfer_peel_off_or_leave',
    'Wrong Transfer': 'wrong_transfer',
    'Wrong  Label': 'wrong_label',
    ' Missing Transfer': 'missing_transfer',
    ' Missing Label': 'missing_label',
    'Shine': 'shine',
    'Skip Stitch': 'skip_stitch',
    'Pleat': 'pleat',
    'Dirt Marck': 'dirt_marck',
    'Missing operation': 'missing_operation',
    'Stain/OIL/SOIL': 'stain_oil_soil',
    'Contamination': 'contamination',
    'Construction Defect': 'construction_defect',
    'Mill Flaw': 'mill_flaw',
    'Fabric Run': 'fabric_run',
    'Misplaced': 'misplaced',
    'Puckering': 'pucketing',
    'Slanted': 'slanted',
    'Defects Sticker inside': 'defect_sticker_inside',
    'Roping': 'roping',
    'Label Slanted': 'label_slanted',
    'Shadding': 'shadding',
    'Missing Packing Trims': 'missing_packing_trims',
    'Missing Print/Embroidery': 'missing_print_or_embroidery',
    'Wrong Packing Trims': 'wrong_packing_trims',
    'Wrong PO': 'wrong_po',
    'Wrong Folding Method': 'wrong_folding_method',
    'Wrong Size Attached': 'wrong_size_attached',
}

QC_FA_PLANT_NUMERIC_COLUMNS = [
    "week", "team", "po", "batch", "seconds", "accepted", "rejected", "sample", "aql", "qty", "defects_total"
]

QC_FA_PLANT_NOT_NUMERIC_COLUMNS = [
    'date_1', 'customer', 'coord', 'date_2', 'style', 'color', 'pass_or_fail'
]

QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS = [
    'uneven', 'broken_stitch', 'open_seam', 'tear', 'hi_low', 'run_off_stitch', 'raw_edge', 'neddle_holes',
    'loose_thread', 'uncut_thread', 'big_or_littler_neck', 'uneven_neck_or_sleeve', 'out_of_measurements',
    'incorrect_stitch', 'variation_tension_sttich', 'excess_fabric', 'hitched', 'po_midex',
    'transfer_peel_off_or_leave', 'wrong_transfer', 'wrong_label', 'missing_transfer', 'missing_label', 'shine', 'skip_stitch',
    'pleat', 'dirt_marck', 'missing_operation', 'stain_oil_soil', 'contamination', 'construction_defect',
    'mill_flaw', 'fabric_run', 'misplaced', 'pucketing', 'slanted', 'defect_sticker_inside', 'roping',
    'label_slanted', 'shadding', 'missing_packing_trims', 'missing_print_or_embroidery', 'wrong_packing_trims',
    'wrong_po', 'wrong_folding_method', 'wrong_size_attached', 'damaged_label', 'pocket_label', 'label_placement',
    'missing_information_label'
]

QC_FA_CUSTOMER_REMAP = {
    'Week': 'week',
    'Customer': 'customer',
    'Line': 'team',
    'Date': 'date_1',
    'PO#': 'po',
    'Style': 'style',
    'ArtCode': 'coord',
    'Batch': 'batch',
    'Color': 'color',
    'Quantity': 'qty',
    'Seconds': 'seconds',
    'Accepted': 'accepted',
    'Rejected': 'rejected',
    'Sample': 'sample',
    'Defects': 'defects_total',
    'AQL %': 'aql',
    'Pass/Fail': 'pass_or_fail',
    'Uneven': 'uneven',
    'Broken Stitch': 'broken_stitch',
    'Open seam': 'open_seam',
    'Hi Low': 'hi_low',
    'Run Off Stitch': 'run_off_stitch',
    'Raw Edge': 'raw_edge',
    'Needle Holes': 'neddle_holes',
    'Tear': 'tear',
    'Loose Thread': 'loose_thread',
    'Uncut Thread': 'uncut_thread',
    'Big/Litter Neck': 'big_or_littler_neck',
    'Uneven Sleeve': 'uneven_neck_or_sleeve',
    'Out of Measurements': 'out_of_measurements',
    'Variation Tension Stitch': 'variation_tension_sttich',
    'Excess Fabric': 'excess_fabric',
    'Hitched': 'hitched',
    'PO Mixed': 'po_midex',
    'Transfer Peel off, Leve': 'transfer_peel_off_or_leave',
    'Wrong  Transfer': 'wrong_transfer',
    ' Missing Transfer': 'missing_transfer',
    'Missing information Label': 'missing_information_label',
    'Wrong  Label': 'wrong_label',
    'Damaged Label': 'damaged_label',
    ' Missing Label': 'missing_label',
    'Shine': 'shine',
    'Skip Stitch': 'skip_stitch',
    'Pleat': 'pleat',
    'Dirt Marck': 'dirt_marck',
    'Missing operation': 'missing_operation',
    'Stain/Oil/Soil': 'stain_oil_soil',
    'Contamination': 'contamination',
    'Construction Defect': 'construction_defect',
    'Mill Flaw': 'mill_flaw',
    'Fabric Run': 'fabric_run',
    'Puckering': 'pucketing',
    'Slanted': 'slanted',
    'Pocket': 'pocket_label',
    'Defects Sticker inside': 'defect_sticker_inside',
    'Label Slanted': 'label_slanted',
    'Shadding': 'shadding',
    'Missing Packing Trims': 'missing_packing_trims',
    'Missing Print/Embroidery': 'missing_print_or_embroidery',
    'Wrong Packing Trims': 'wrong_packing_trims',
    'Wrong PO': 'wrong_po',
    'Wrong Folding Method': 'wrong_folding_method',
    'Wrong Size Attached': 'wrong_size_attached',
    'Label Placement': 'label_placement',
}

QC_FA_CUSTOMER_NUMERIC_COLUMNS = [
    "week", "po", "batch", "seconds", "accepted", "rejected", "sample", "aql", "qty", "defects_total"
]

QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS = [
    'date_1', 'customer', 'coord', 'date_2', 'style', 'color', 'pass_or_fail', 'team', 'line_code'
]

QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS = [
    'uneven', 'broken_stitch', 'open_seam', 'tear', 'hi_low', 'run_off_stitch', 'raw_edge', 'neddle_holes',
    'loose_thread', 'uncut_thread', 'big_or_littler_neck', 'uneven_neck_or_sleeve', 'out_of_measurements',
    'incorrect_stitch', 'variation_tension_sttich', 'excess_fabric', 'hitched', 'po_midex',
    'transfer_peel_off_or_leave', 'wrong_transfer', 'wrong_label', 'missing_transfer', 'missing_label', 'shine', 'skip_stitch',
    'pleat', 'dirt_marck', 'missing_operation', 'stain_oil_soil', 'contamination', 'construction_defect',
    'mill_flaw', 'fabric_run', 'misplaced', 'pucketing', 'slanted', 'defect_sticker_inside', 'roping',
    'label_slanted', 'shadding', 'missing_packing_trims', 'missing_print_or_embroidery', 'wrong_packing_trims',
    'wrong_po', 'wrong_folding_method', 'wrong_size_attached', 'damaged_label', 'pocket_label', 'label_placement',
    'missing_information_label'
]


SECONDS_A4_REMAP = {
    'year': 'year',
    'week': 'week',
    'DATE': 'date',
    'CUT#': 'cut_num',
    'STYLE': 'style',
    'CUT QTY': 'cut_qty',
    'COLOR': 'color',
    'FIRST QUALITY QTY SEWING': 'first_quality_qty_sewing',
    'Sample': 'sample',
    'PASS': 'pass_field',
    'FAIL': 'fail_field',
    'SEW DEF.': 'sew_def',
    'FAB. DEF.': 'fab_def',
    '% ACEPTED': 'accepted',
    '% REJECTED': 'rejected',
    'TOTAL OF 2DS': 'total_of_2ds',
    '% OF 2DS': 'percentage_of_2ds',
    'LINE#': 'line',
    '2DA BY SEW': 'seconds_by_sew',
    '2DA BY\xa0 FAB': 'seconds_by_fab',
    '%Seconds Sew A4': 'seconds_sew_a4',
    '%Seconds Fab A4': 'seconds_fab_a4',
}

SECONDS_A4_NUMERIC_COLUMNS = [
    'year', 'week', 'cut_num', 'cut_qty', 'first_quality_qty_sewing', 'sample',
    'pass_field', 'fail_field', 'sew_def', 'fab_def', 'accepted', 'rejected',
    'total_of_2ds', 'percentage_of_2ds', 'seconds_by_sew', 'seconds_by_fab',
    'seconds_sew_a4', 'seconds_fab_a4'
]

SECONDS_A4_NOT_NUMERIC_COLUMNS = [
    'date', 'style', 'color', 'line'
]


SECONDS_GENERAL_REMAP = {
    'Date': 'date',
    'Week': 'week',
    'Line': 'team',
    'Customer': 'customer',
    'Style': 'style',
    'ArtCode': 'artcode',
    'Color': 'color',
    'PO ': 'po',
    'Size': 'size',
    'Produced': 'produced',
    'Fixed': 'fixed',
    'Definitive': 'definitive',
    'Picado de Aguja': 'picado_aguja',
    'Manchas/Sucio': 'manchas_sucio',
    'Grasa': 'grasa',
    'Tono Tela': 'tono_tela',
    'Fuera Medidas': 'fuera_medidas',
    'Enganche': 'enganche',
    'Costura Torcida/Insegura': 'costura_torcida_insegura',
    'Hoyos Costura': 'hoyos_costura',
    'Heat Transfer Defectuoso/Inclinado/Fuera de Posicion': 'heat_transfer',
    'Mal Corte': 'mal_corte',
    'Trapo': 'trapo',
    'Corrido': 'corrido',
    'Otros': 'otros',
    'Total De Costura': 'total_de_costura',
    'Desgarre/Def Tela': 'desgarre_def_tela',
    'Contamination': 'contamination',
    'Linea de Tela': 'linea_de_tela',
    'Mill  Flaw': 'mill_flaw',
    'Hoyos': 'hoyos',
    'Manchas Tela': 'manchas_tela',
    'Corrido2': 'corrido_2',
    'Barre': 'barre',
    'Otros3': 'otros_3',
    'Degradacion': 'degradacion',
    'Bordados': 'bordados',
    'Total de Tela': 'total_de_tela',
}

SECONDS_GENERAL_NUMERIC_COLUMNS = [
    'week', 'produced', 'fixed', 'definitive',
]

SECONDS_GENERAL_NOT_NUMERIC_COLUMNS = [
    'date', 'team', 'line_code', 'customer', 'style', 'artcode', 'color', 'po', 'size',
]

SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS = [
    'picado_aguja', 'manchas_sucio', 'grasa', 'tono_tela', 'fuera_medidas',
    'enganche', 'costura_torcida_insegura', 'hoyos_costura', 'heat_transfer',
    'mal_corte', 'trapo', 'corrido', 'otros',
    'desgarre_def_tela', 'contamination', 'linea_de_tela', 'mill_flaw',
    'hoyos', 'manchas_tela',
    'corrido_2', 'barre', 'otros_3', 'degradacion', 'bordados',
]


CONTAINER_REMAP = {
    'Date': 'date',
    '# Container': 'container_number',
    'Customer': 'customer',
    '# Transfert of Container': 'transfer_of_container',
    'Total Palette': 'total_palette',
    'Total Palette Pass': 'total_palette_pass',
    'Total Palette reject': 'total_palette_rejected',
    '% Pass': 'percentage_pass',
    '% Reject': 'percentage_reject',
    'Dirt label/ \n Salte nan Etikèt': 'dirt_label',
    'dirt container/ \n Konntenè sal': 'dirt_container',
    'Dirt Cartons/ Katon Sal': 'dirt_cartoons',
    'Container Holes\nTwou nan Konntenè': 'container_holes',
    'Written mark on Label\nEkriti sou Etikèt': 'writte_mark_on_label',
    'Written mark on Carton\nEkriti sou Bwat yo': 'written_mark_on_cartoon',
    'container poor close \nKontenè mal fèmen': 'container_poor_close',
    'boxes pooor close\nBwat ki mal fèmen': 'boxes_poor_close',
    'Printing Issues label/ \nProblem Enpresyon Etikèt': 'printing_issues_label',
    'Misaligned label/ \nEtikèt kwochi': 'misaligned_label',
    'Crushed corners Boxes / Bwat kraze': 'crushed_corners',
    'Cartons Holes \nTwou nan Bwat2': 'cartoons_holes',
    'Warped Boxes/  Bwat Defòme': 'warped_boxes',
    'Defects label carton /Defo Etikèt katon': 'defects_label',
    'Total defects': 'total_defects',
}

CONTAINER_NUMERIC_COLUMNS = [
    'container_number', 'transfer_of_container', 'total_palette', 'total_palette_pass',
    'total_palette_rejected', 'percentage_pass', 'percentage_reject'
]

CONTAINER_NOT_NUMERIC_COLUMNS = [
    'customer', 'date'
]

CONTAINER_AMOUNT_DEFEACTS_FIELDS = [
    'dirt_label', 'dirt_container', 'dirt_cartoons', 'container_holes',
    'writte_mark_on_label', 'written_mark_on_cartoon', 'container_poor_close',
    'boxes_poor_close', 'printing_issues_label', 'misaligned_label',
    'crushed_corners', 'cartoons_holes', 'warped_boxes', 'defects_label',
    'total_defects'
]

# Pivot table ranges for KPI dynamic parsing
PIVOT_RANGES = {
    'seconds_rework': {'sheet': 'SecondsA4', 'header_row': 8, 'usecols': 'X:Z', 'nrows': 48},
    'fabric_defects_corrido2': {'sheet': 'Seconds General', 'header_row': 3, 'usecols': 'AM:AN', 'nrows': 42},
    'fabric_defects_corrido': {'sheet': 'Seconds General', 'header_row': 49, 'usecols': 'AM:AN', 'nrows': 35},
}


QC_FA_PLANT_EXPORT_COLUMNS = list(QC_FA_PLANT_REMAP.values())
QC_FA_CUSTOMER_EXPORT_COLUMNS = list(QC_FA_CUSTOMER_REMAP.values())

SECONDS_GENERAL_EXPORT_COLUMNS = [
    'date', 'week', 'team', 'line_code', 'customer', 'style', 'artcode', 'color', 'po', 'size',
    'produced', 'fixed', 'definitive',
    'picado_aguja', 'manchas_sucio', 'grasa', 'tono_tela', 'fuera_medidas',
    'enganche', 'costura_torcida_insegura', 'hoyos_costura', 'heat_transfer',
    'mal_corte', 'trapo', 'corrido', 'otros', 'total_de_costura',
    'desgarre_def_tela', 'contamination', 'linea_de_tela', 'mill_flaw',
    'hoyos', 'manchas_tela',
    'corrido_2', 'barre', 'otros_3', 'degradacion', 'bordados', 'total_de_tela',
]

SECONDS_GENERAL_DEFECT_COLUMNS = [
    'picado_aguja', 'manchas_sucio', 'grasa', 'tono_tela', 'fuera_medidas',
    'enganche', 'costura_torcida_insegura', 'hoyos_costura', 'heat_transfer',
    'mal_corte', 'trapo', 'corrido', 'otros',
    'desgarre_def_tela', 'contamination', 'linea_de_tela', 'mill_flaw',
    'hoyos', 'manchas_tela',
    'corrido_2', 'barre', 'otros_3', 'degradacion', 'bordados',
]

SECONDS_GENERAL_SEWING_DEFECTS = [
    'picado_aguja', 'manchas_sucio', 'grasa', 'tono_tela', 'fuera_medidas',
    'enganche', 'costura_torcida_insegura', 'hoyos_costura', 'heat_transfer',
    'mal_corte', 'trapo', 'corrido', 'otros',
]

SECONDS_GENERAL_FABRIC_DEFECTS = [
    'desgarre_def_tela', 'contamination', 'linea_de_tela', 'mill_flaw',
    'hoyos', 'manchas_tela',
    'corrido_2', 'barre', 'otros_3', 'degradacion', 'bordados',
]

CONTAINER_EXPORT_COLUMNS = list(CONTAINER_REMAP.values())

CORPORATE_XLSX_EXPORT_CONFIG = [
    {
        "dataset": "qfa",
        "sheet_name": "QC FA Plant",
        "table_name": "Table3",
        "model": "QualityQcFa",
        "date_field": "date_1",
        "date_field_type": "char",
        "queryset_filters": {"table_type": "QFA"},
        "columns": QC_FA_PLANT_EXPORT_COLUMNS,
        "defect_columns": QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
        "row_builder": "qc_fa",
    },
    {
        "dataset": "qfc",
        "sheet_name": "QC FA Customer",
        "table_name": "Table2",
        "model": "QualityQcFa",
        "date_field": "date_1",
        "date_field_type": "char",
        "queryset_filters": {"table_type": "QFC"},
        "columns": QC_FA_CUSTOMER_EXPORT_COLUMNS,
        "defect_columns": QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
        "row_builder": "qc_fa",
    },
    {
        "dataset": "seconds_a4",
        "sheet_name": "SecondsA4",
        "table_name": "Table15",
        "model": "SecondsA4",
        "date_field": "date",
        "date_field_type": "char",
        "queryset_filters": {},
        "columns": [
            "year",
            "week",
            "date",
            "cut_num",
            "style",
            "cut_qty",
            "first_quality_qty_sewing",
            "sample",
            "pass_field",
            "fail_field",
            "sew_def",
            "fab_def",
            "accepted",
            "rejected",
            "total_of_2ds",
            "percentage_of_2ds",
            "line",
            "seconds_by_sew",
            "seconds_by_fab",
            "seconds_sew_a4",
            "seconds_fab_a4",
        ],
    },
    {
        "dataset": "seconds_general",
        "sheet_name": "Seconds General",
        "table_name": "Table1",
        "model": "SecondsGeneral",
        "date_field": "date",
        "date_field_type": "char",
        "queryset_filters": {},
        "columns": SECONDS_GENERAL_EXPORT_COLUMNS,
        "row_builder": "seconds_general",
    },
    {
        "dataset": "container",
        "sheet_name": "Container",
        "table_name": "Table18",
        "model": "Container",
        "date_field": "date",
        "date_field_type": "date",
        "queryset_filters": {},
        "columns": CONTAINER_EXPORT_COLUMNS,
        "defect_columns": CONTAINER_AMOUNT_DEFEACTS_FIELDS,
        "row_builder": "container",
    },
]
