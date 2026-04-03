from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from quality_data.models import DefectType, Color


class Mockup(models.Model):
    """Garment mockup image with dimensions for the touch capture interface."""

    SIDE_CHOICES = [
        ('FRONT', 'Front Side'),
        ('BACK', 'Back Side'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES, default='FRONT')
    image = models.ImageField(upload_to='mockups/')
    width = models.IntegerField(default=1024)
    height = models.IntegerField(default=768)

    class Meta:
        ordering = ['name', 'side']

    def __str__(self):
        return f"{self.name} ({self.side})"


class InspectionData(models.Model):
    """Inspection session created by an operator for a specific garment lot."""

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('PASS', 'Pass'),
        ('REJECT', 'Reject'),
    ]

    inspector = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField(auto_now_add=True)
    created_at = models.TimeField(auto_now_add=True)
    week = models.PositiveIntegerField(editable=False)
    style = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    is_closed = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.week = timezone.now().date().isocalendar()[1]
        super().save(*args, **kwargs)

    def __str__(self):
        condition = "closed" if self.is_closed else "open"
        return f"ID {self.id} | Date {self.date} | Week {self.week} | {self.color.name} ({condition})"


class RevisionDefect(models.Model):
    """Individual defect captured during an inspection with coordinates on the mockup."""

    inspection = models.ForeignKey(InspectionData, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    defect_type = models.ForeignKey(DefectType, on_delete=models.PROTECT, null=True, blank=True)
    defect_size = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    defect_count = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    coordinates_x = models.JSONField(default=list)
    coordinates_y = models.JSONField(default=list)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        defect_name = self.defect_type.name if self.defect_type else "Unknown"
        return f"{defect_name} - {self.defect_size} ({self.defect_count})"
