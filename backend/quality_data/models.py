from django.db import models


class AmountDefects(models.Model):

    table_type_choices ={
        "QFA": "AC FA Plant",
        "QFC": "QC FA Customer",
        "S4": "SecondsA4",
        "SG": "Seconds General",
        "C": "Container"
    }
    
    table_type = models.CharField(max_length=1, choices=table_type_choices)

    uneven = models.IntegerField()
    broken_stitch = models.IntegerField()
    open_seam = models.IntegerField()
    tear = models.IntegerField()
    hi_low = models.IntegerField()
    run_off_stitch = models.IntegerField()
    raw_edge = models.IntegerField()
    neddle_holes = models.IntegerField()
    loose_thread = models.IntegerField()
    uncut_thread = models.IntegerField()
    big_or_littler_neck = models.IntegerField()
    uneven_neck_or_sleeve = models.IntegerField()
    out_of_measurements = models.IntegerField()
    incorrect_stitch = models.IntegerField()
    variation_tension_sttich = models.IntegerField()
    excess_fabric = models.IntegerField()
    hitched = models.IntegerField()
    po_midex = models.IntegerField()
    transfer_peel_off_or_leave = models.IntegerField()
    wrong_transfer = models.IntegerField()
    missing_transfer = models.IntegerField()
    missing_label = models.IntegerField()
    shine = models.IntegerField()
    skip_stitch = models.IntegerField()
    pleat = models.IntegerField()
    dirt_marck = models.IntegerField()
    missing_operation = models.IntegerField()
    stain_oil_soil = models.IntegerField()
    contamination = models.IntegerField()
    construction_defect = models.IntegerField()
    mill_flaw = models.IntegerField()
    fabric_run = models.IntegerField()
    misplaced = models.IntegerField()
    pucketing = models.IntegerField()
    slanted = models.IntegerField()
    defect_sticker_inside = models.IntegerField()
    roping = models.IntegerField()
    label_slanted = models.IntegerField()
    shadding = models.IntegerField()
    missing_packing_trims = models.IntegerField()
    missing_print_or_embroidery = models.IntegerField()
    wrong_packing_trims = models.IntegerField()
    wrong_po = models.IntegerField()
    wrong_folding_method = models.IntegerField()
    wrong_size_attached = models.IntegerField()

    damaged_label = models.IntegerField()
    pocket_label = models.IntegerField()
    label_placement = models.IntegerField()
    missing_information_label = models.IntegerField()


class QualityQcFa(models.Model):
    date_1 = models.CharField(max_length=50)
    week = models.IntegerField()
    customer = models.CharField(max_length=100)
    team = models.IntegerField()
    coord = models.CharField(max_length=50)
    date_2 = models.CharField(max_length=50)
    po = models.IntegerField()
    style = models.CharField(max_length=100)
    batch = models.IntegerField()
    color = models.CharField(max_length=50)
    qty = models.CharField(max_length=50)
    seconds = models.IntegerField()
    accepted = models.IntegerField()
    rejected = models.IntegerField()
    sample = models.IntegerField()
    defeacts = models.IntegerField()
    aql = models.CharField(max_length=50)
    pass_or_fail = models.CharField(max_length=50)

    defeacts = models.ForeignKey(AmountDefects, on_delete=models.CASCADE)


