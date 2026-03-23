from django.db import models
from django.contrib.auth.models import User
from quality_data.models import DefectType

# Tabla InspectionData para almacenar los datos de cada inspección
class InspectionData(models.Model):
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=50, unique=True)
    

# Tabla RevisionDefect para almacenar los defectos capturados durante la inspección
class RevisionDefect(models.Model):
    inspection = models.ForeignKey(InspectionData, on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    defectType = models.ForeignKey(DefectType, on_delete=models.SET_NULL, null=True, blank=True)
    defectCount = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    coordinates_x = models.JSONField(default=list)
    coordinates_y = models.JSONField(default=list)    

# Tabla Mockup para almacenar la imagen de referencia y sus dimensiones
class Mockup(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mockups/')
    width = models.IntegerField(default=1024)
    height = models.IntegerField(default=768)



