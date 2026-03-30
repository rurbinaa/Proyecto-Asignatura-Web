from django.contrib import admin
from .models import InspectionData, RevisionDefect, Mockup

admin.site.register(InspectionData)
admin.site.register(RevisionDefect)
admin.site.register(Mockup)