from django.db import models

# Create your models here.

# Generic table for QC FA Plant and QC FA Customer

class QualityQcFa (models.model):

    date_1 = models.DateField
    week = models.IntegerField
    customer = models.CharField
    team = models.IntegerField
    coord = models.CharField
    date_2 = models.DateField
    po = models.IntegerField
    Style = models.CharField
    batch = models.IntegerField
    color = models.CharField
    qty = models.CharField
    seconds = models.IntegerField
    accepted = models.IntegerField
    rejected = models.IntegerField
    sample = models.IntegerField
    defeacts = models.IntegerField
    aql = models.IntegerField
    pass_or_fail = models.CharField


class amount_defects (models.Model):
    
    uneven = models.IntegerField
    broken_stitch = models.IntegerField
    open_seam = models.IntegerField
    tear = models.IntegerField
    hi_low = models.IntegerField
    run_off_stitch = models.IntegerField
    raw_edge = models.IntegerField
    neddle_holes = models.IntegerField
    loose_thread = models.IntegerField
    uncut_thread = models.IntegerField
    big_or_littler_neck = models.IntegerField
    uneven_neck_or_sleeve = models.IntegerField
    out_of_measurements = models.IntegerField
    incorrect_stitch = models.IntegerField
    variation_tension_sttich = models.IntegerField
    excess_fabric = models.IntegerField
    hitched = models.IntegerField
    po_midex = models.IntegerField
    transfer_peel_off_or_leave = models.IntegerField
    wrong_transfer = models.IntegerField
    missing_transfer = models.IntegerField
    missing_label = models.IntegerField
    shine = models.IntegerField
    skip_stitch = models.IntegerField
    pleat = models.IntegerField
    dirt_marck = models.IntegerField
    missing_operation = models.IntegerField
    stain_oil_soil = models.IntegerField
    contamination = models.IntegerField
    construction_defect = models.IntegerField
    mill_flaw = models.IntegerField
    fabric_run = models.IntegerField
    misplaced = models.IntegerField
    pucketing = models.IntegerField
    slanted = models.IntegerField
    defect_sticker_inside = models.IntegerField
    roping = models.IntegerField
    label_slanted = models.IntegerField
    shadding = models.IntegerField
    missing_packing_trims = models.IntegerField
    missing_print_or_embroidery = models.IntegerField
    wrong_packing_trims = models.IntegerField
    wrong_po = models.IntegerField
    wrong_folding_method = models.IntegerField
    wrong_size_attached = models.IntegerField