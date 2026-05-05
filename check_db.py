import os
import django
import sys

sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from quality_data.models import QualityQcFa
nans = QualityQcFa.objects.filter(line_code="nan").count()
nulls = QualityQcFa.objects.filter(line_code__isnull=True).count()
emptys = QualityQcFa.objects.filter(line_code="").count()
print(f"NaNs: {nans}, Nulls: {nulls}, Emptys: {emptys}")
