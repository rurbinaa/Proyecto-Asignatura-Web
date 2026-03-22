from django.db import models
from django.contrib.auth.models import User
class InspectionData(models.Model):
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True) # Sello de tiempo automático

# Tabla Mockup
class Mockup(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='mockups/')
    width = models.IntegerField(default=1024)
    height = models.IntegerField(default=768)