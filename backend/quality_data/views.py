from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.response import Response
from excel_importer.handler_service import load_and_clean, bulk_insert
# Create your views here.

sheet_names = [
    ("QC FA Plant", 2, 67),
    ("QC FA Customer", 0, 64),
    ("SecondsA4", 1, 22),
    ("Seconds General", 1, 22),
    ("Container", 2, 24),
]

qc_fa_plant_remap = {
    'Date 1': 'date_1',
    'Week': 'week',
    'Customer': 'customer',
    'Team': 'team',
    'Coord': 'coord',
    'Date 2': 'date_2',
    'Po': 'po',
    'Style': 'style',
    'Batch': 'batch',
    'Color': 'color',
    'Qty': 'qty',
    'Seconds': 'seconds',
    'Accepted': 'accepted',
    'Rejected': 'rejected',
    'Sample': 'sample',
    'Defects': 'defeacts',
    'AQL %': 'aql',
    'Pass/Fail': 'pass_or_fail',

    'uneven': 'uneven',
    'broken_stitch': 'broken_stitch',
    'open_seam': 'open_seam',
    'tear': 'tear',
    'hi_low': 'hi_low',
    'run_off_stitch': 'run_off_stitch',
    'raw_edge': 'raw_edge',
    'neddle_holes': 'neddle_holes',
    'loose_thread': 'loose_thread',
    'uncut_thread': 'uncut_thread',
    'big_or_littler_neck': 'big_or_littler_neck',
    'uneven_neck_or_sleeve': 'uneven_neck_or_sleeve',
    'out_of_measurements': 'out_of_measurements',
    'incorrect_stitch': 'incorrect_stitch',
    'variation_tension_sttich': 'variation_tension_sttich',
    'excess_fabric': 'excess_fabric',
    'hitched': 'hitched',
    'po_midex': 'po_midex',
    'transfer_peel_off_or_leave': 'transfer_peel_off_or_leave',
    'wrong_transfer': 'wrong_transfer',
    'missing_transfer': 'missing_transfer',
    'missing_label': 'missing_label',
    'shine': 'shine',
    'skip_stitch': 'skip_stitch',
    'pleat': 'pleat',
    'dirt_marck': 'dirt_marck',
    'missing_operation': 'missing_operation',
    'stain_oil_soil': 'stain_oil_soil',
    'contamination': 'contamination',
    'construction_defect': 'construction_defect',
    'mill_flaw': 'mill_flaw',
    'fabric_run': 'fabric_run',
    'misplaced': 'misplaced',
    'pucketing': 'pucketing',
    'slanted': 'slanted',
    'defect_sticker_inside': 'defect_sticker_inside',
    'roping': 'roping',
    'label_slanted': 'label_slanted',
    'shadding': 'shadding',
    'missing_packing_trims': 'missing_packing_trims',
    'missing_print_or_embroidery': 'missing_print_or_embroidery',
    'wrong_packing_trims': 'wrong_packing_trims',
    'wrong_po': 'wrong_po',
    'wrong_folding_method': 'wrong_folding_method',
    'wrong_size_attached': 'wrong_size_attached',
    'damaged_label': 'damaged_label',
    'pocket_label': 'pocket_label',
    'label_placement': 'label_placement',
    'missing_information_label': 'missing_information_label',
}

qc_fa_plant_numeric_columns = [
"week", "team", "po", "batch",  "seconds", "accepted", "rejected", "sample", "aql", "qty"
]


qc_fa_plant_not_numeric_columns = [
    'date_1', 'customer', 'coord', 'date_2', 'style', 'color', 'pass_or_fail'
]

qc_fa_plant_amount_defeacts_fields = [
'uneven', 'broken_stitch', 'open_seam', 'tear', 'hi_low', 'run_off_stitch', 'raw_edge', 'neddle_holes',
'loose_thread', 'uncut_thread', 'big_or_littler_neck', 'uneven_neck_or_sleeve', 'out_of_measurements',
'incorrect_stitch', 'variation_tension_sttich', 'excess_fabric', 'hitched', 'po_midex',
'transfer_peel_off_or_leave', 'wrong_transfer', 'missing_transfer', 'missing_label', 'shine', 'skip_stitch',
'pleat', 'dirt_marck', 'missing_operation', 'stain_oil_soil', 'contamination', 'construction_defect',
'mill_flaw', 'fabric_run', 'misplaced', 'pucketing', 'slanted', 'defect_sticker_inside', 'roping',
'label_slanted', 'shadding', 'missing_packing_trims', 'missing_print_or_embroidery', 'wrong_packing_trims',
'wrong_po', 'wrong_folding_method', 'wrong_size_attached',
'damaged_label', 'pocket_label', 'label_placement', 'missing_information_label'
]

class Process(APIView):
    parser_classes = [FileUploadParser]

    def post (self, request, filename, format = None):
        file_obj = request.data['file']



        
        # QC FA Plant

        qc_fa_plant_df = load_and_clean(file_obj, qc_fa_plant_remap, qc_fa_plant_numeric_columns, qc_fa_plant_amount_defeacts_fields, *sheet_names[1])

        # QC FA Customer

        # SecondsA4

        # Seconds General

        # Container


        return Response(status = 204)
    

class SaveData(APIView):
    parser_classes = [FileUploadParser]

    def post (self, request, filename, format = None):
        file_obj = request.data['file']

        qc_fa_plant_df = load_and_clean(file_obj, qc_fa_plant_remap, qc_fa_plant_numeric_columns,qc_fa_plant_amount_defeacts_fields, *sheet_names[1])

        bulk_insert(qc_fa_plant_df, qc_fa_plant_numeric_columns, qc_fa_plant_not_numeric_columns, qc_fa_plant_amount_defeacts_fields)

        return Response(status = 204)