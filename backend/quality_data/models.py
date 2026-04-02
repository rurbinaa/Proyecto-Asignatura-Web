from django.db import models
from django.contrib.auth.models import User

QUALITY_QC_FA_TABLE_TYPE_CHOICES = [
    ("QFA", "QC FA Plant"),
    ("QFC", "QC FA Customer"),
]


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# tablas QC FA Plant y QC FA Customer

class DefectType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class QualityQcFa(models.Model):
    table_type = models.CharField(
        max_length=3,
        choices=QUALITY_QC_FA_TABLE_TYPE_CHOICES,
    )
    date_1 = models.CharField(max_length=20)
    week = models.IntegerField()
    customer = models.CharField(max_length=50)
    team = models.IntegerField()
    coord = models.CharField(max_length=50)
    date_2 = models.CharField(max_length=20, blank=True, default="")
    po = models.IntegerField()
    style = models.CharField(max_length=50)
    batch = models.IntegerField()
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name="quality_qc_fa_records")
    qty = models.IntegerField()
    seconds = models.IntegerField()
    accepted = models.IntegerField()
    rejected = models.IntegerField()
    sample = models.IntegerField()
    defects_total = models.IntegerField(default=0)
    aql = models.FloatField()
    pass_or_fail = models.CharField(max_length=10)
    defects = models.ManyToManyField(
        DefectType,
        through="InspectionDefect",
        related_name="quality_qc_fa_records",
    )

class InspectionDefect(models.Model):
    inspection = models.ForeignKey(QualityQcFa, on_delete=models.CASCADE, related_name="inspection_defects")
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, related_name="inspection_defects")
    amount = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["inspection", "defect_type"],
                name="unique_quality_qc_fa_defect",
            )
        ]



# tabla SecondsA4

class SecondsA4(models.Model):
    year = models.IntegerField()
    week = models.IntegerField()
    date = models.CharField(max_length=20)
    cut_num = models.IntegerField()
    style = models.CharField(max_length=50)
    cut_qty = models.IntegerField()
    color = models.ForeignKey(Color, on_delete=models.PROTECT, related_name="seconds_a4_records")
    first_quality_qty_sewing = models.IntegerField()
    sample = models.IntegerField()
    pass_field = models.IntegerField()
    fail_field = models.IntegerField()
    sew_def = models.IntegerField()
    fab_def = models.IntegerField()
    accepted = models.IntegerField()
    rejected = models.IntegerField()
    total_of_2ds = models.IntegerField()
    percentage_of_2ds = models.FloatField()
    line = models.CharField(max_length=20)
    seconds_by_sew = models.IntegerField()
    seconds_by_fab = models.IntegerField()
    seconds_sew_a4 = models.IntegerField()
    seconds_fab_a4 = models.IntegerField()


# Tabla Seconds General

class SecondsGeneral(models.Model):
    date = models.CharField(max_length=20)
    week = models.IntegerField()
    corrido_2 = models.IntegerField()
    barre = models.IntegerField()
    otros_3 = models.IntegerField()
    degradacion = models.IntegerField()
    bordados = models.IntegerField()
    total_de_tela = models.IntegerField()


# Tabla Container

class ContainerDefectType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Container(models.Model):
    container_number = models.IntegerField()
    customer = models.CharField(max_length=50)
    transfer_of_container = models.IntegerField(default=0)
    total_palette = models.IntegerField()
    total_palette_pass = models.IntegerField()
    total_palette_rejected = models.IntegerField()
    percentage_pass = models.FloatField()
    percentage_reject = models.FloatField()
    defects = models.ManyToManyField(
        ContainerDefectType,
        through="ContainerInspectionDefect",
        related_name="container_records",
    )


class ContainerInspectionDefect(models.Model):
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name="container_defects",)
    defect_type = models.ForeignKey(ContainerDefectType, on_delete=models.PROTECT, related_name="container_defects",)
    amount = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["container", "defect_type"],
                name="unique_container_defect",
            )
        ]


class ExcelSyncSession(models.Model):
    """
    Stores the state of an Excel import preview session.

    When a user uploads an Excel file, the system parses it and computes a diff
    against the database. The parsed data and diff summary are stored in this
    model so the user can review before confirming.

    Flow: upload → preview (creates session) → confirm/reject (deletes session)
    """
    STATUS_CHOICES = [
        ("pending", "Pending confirmation"),
        ("confirmed", "Confirmed and applied"),
        ("rejected", "Rejected by user"),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    # Parsed Excel data per sheet (JSONField stores list of dicts)
    qc_fa_plant_data = models.JSONField(default=list)
    qc_fa_customer_data = models.JSONField(default=list)
    seconds_a4_data = models.JSONField(default=list)
    seconds_general_data = models.JSONField(default=list)
    container_data = models.JSONField(default=list)

    # Diff summary per sheet (JSONField stores preview metadata)
    qc_fa_plant_preview = models.JSONField(default=dict)
    qc_fa_customer_preview = models.JSONField(default=dict)
    seconds_a4_preview = models.JSONField(default=dict)
    seconds_general_preview = models.JSONField(default=dict)
    container_preview = models.JSONField(default=dict)

    # Global warnings (e.g., data loss risks)
    warnings = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"SyncSession #{self.pk} [{self.status}] - {self.created_at}"

    @property
    def is_pending(self):
        return self.status == "pending"
