from django.db import models
from django.contrib.auth.models import User
from quality_data.models import DefectType, Color

# Tabla InspectionData para almacenar los datos de cada inspección
class InspectionData(models.Model):
    inspector = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True)
    
    def __str__(self):
        return f"Inspección {self.id} - {self.color.name} ({self.created_at})"

# Tabla RevisionDefect para almacenar los defectos capturados durante la inspección
class RevisionDefect(models.Model):
    class DefectSize(models.TextChoices):
        SMALL = 'S', 'Small',
        MEDIUM = 'M', 'Medium',
        LARGE = 'L', 'Large'
    
    inspection = models.ForeignKey(InspectionData, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    defectType = models.ForeignKey(DefectType, on_delete=models.PROTECT, null=True, blank=True)
    defectSize = models.CharField(max_length=1, choices=DefectSize)
    notes = models.TextField(blank=True, null=True)
    defectCount = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    coordinates_x = models.JSONField(default=list)
    coordinates_y = models.JSONField(default=list)    

    def __str__(self):
        return f"{self.defectType.name} - {self.defectSize} ({self.defectCount})"

# Tabla Mockup para almacenar la imagen de referencia y sus dimensiones
class Mockup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mockups/')
    width = models.IntegerField(default=1024)
    height = models.IntegerField(default=768)



