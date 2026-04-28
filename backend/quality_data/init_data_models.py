from .models import Color, DefectType, ContainerDefectType

COMPANY_COLORS = [
    "athletic_orange",
    "black",
    "brown",
    "cardinal",
    "coral",
    "electric_blue",
    "forest",
    "fushia",
    "gold",
    "graphite",
    "kelly",
    "light_blue",
    "light_lime",
    "lime",
    "maroon",
    "melon",
    "military_green",
    "navy",
    "olive",
    "pastel_blue",
    "pastel_mint",
    "pink",
    "purple",
    "royal",
    "safety_green",
    "safety_orange",
    "safety_yellow",
    "salmon",
    "sand",
    "scarlet",
    "silver",
    "sky_blue",
    "teal",
    "texas",
    "vegas_gold",
    "white",
]

GARMENT_DEFECT_TYPES = [
    "uneven",
    "broken_stitch",
    "open_seam",
    "tear",
    "hi_low",
    "run_off_stitch",
    "raw_edge",
    "neddle_holes",
    "loose_thread",
    "uncut_thread",
    "big_or_littler_neck",
    "uneven_neck_or_sleeve",
    "out_of_measurements",
    "incorrect_stitch",
    "variation_tension_sttich",
    "excess_fabric",
    "hitched",
    "po_midex",
    "transfer_peel_off_or_leave",
    "wrong_transfer",
    "wrong_label",
    "missing_transfer",
    "missing_label",
    "shine",
    "skip_stitch",
    "pleat",
    "dirt_marck",
    "missing_operation",
    "stain_oil_soil",
    "contamination",
    "construction_defect",
    "mill_flaw",
    "fabric_run",
    "misplaced",
    "pucketing",
    "slanted",
    "defect_sticker_inside",
    "roping",
    "label_slanted",
    "shadding",
    "missing_packing_trims",
    "missing_print_or_embroidery",
    "wrong_packing_trims",
    "wrong_po",
    "wrong_folding_method",
    "wrong_size_attached",
    "damaged_label",
    "pocket_label",
    "label_placement",
    "missing_information_label",
]

CONTAINER_DEFECT_TYPES = [
    "dirt_label",
    "dirt_container",
    "dirt_cartoons",
    "container_holes",
    "writte_mark_on_label",
    "written_mark_on_cartoon",
    "container_poor_close",
    "boxes_poor_close",
    "printing_issues_label",
    "misaligned_label",
    "crushed_corners",
    "cartoons_holes",
    "warped_boxes",
    "defects_label",
    "total_defects",
]


def SaveColor():
    for i in COMPANY_COLORS:
        if not Color.objects.filter(name = i).exists():
            Color.objects.create(name = i, is_active=True)

    
def SaveDefects():
    for i in GARMENT_DEFECT_TYPES:
        if not DefectType.objects.filter(name = i).exists():
            DefectType.objects.create(name = i, is_active=True)
      

def SaveDefectsContainer():
    for i in CONTAINER_DEFECT_TYPES:
        if not ContainerDefectType.objects.filter(name = i).exists():
            ContainerDefectType.objects.create(name = i, is_active=True)