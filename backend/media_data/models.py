from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from quality_data.models import DefectType, Color

# Tabla Mockup para almacenar la imagen de referencia y sus dimensiones
class Mockup(models.Model):
    Side_Choices = [
        ('FRONT', 'Front Side'),
        ('BACK', 'Back Side'),
    ]
    name = models.CharField(max_length=100)
    side = models.CharField(max_length=10, choices=Side_Choices, default='FRONT')
    id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to='mockups/')
    width = models.IntegerField(default=1024)
    height = models.IntegerField(default=768)
    
    def __str__(self):
        return self.name

# Tabla InspectionData para almacenar los datos de cada inspección
class InspectionData(models.Model):
    Estatus_Choices = [
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
    status = models.CharField(max_length=10, choices=Estatus_Choices, default='OPEN')
    closed_at = models.DateTimeField(null=True, blank=True)
      
    def save(self, *args, **kwargs):
        if not self.pk:
            self.week = timezone.now().date().isocalendar()[1]
        super().save(*args, **kwargs)
    
    def __str__(self):
        condition = "closed" if self.is_closed else "open"
        return f"ID {self.id} | Date {self.date} | Week {self.week} | {self.color.name} ({condition})"

# Tabla RevisionDefect para almacenar los defectos capturados durante la inspección
class RevisionDefect(models.Model):  
    inspection = models.ForeignKey(InspectionData, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    defectType = models.ForeignKey(DefectType, on_delete=models.PROTECT, null=True, blank=True)
    defectSize = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    defectCount = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    coordinates_x = models.JSONField(default=list)
    coordinates_y = models.JSONField(default=list)    

    def __str__(self):
        return f"{self.defectType.name} - {self.defectSize} ({self.defectCount})"