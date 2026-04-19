from django.urls import path
from . import views

app_name = 'excel_reports'

urlpatterns = [
    path('prueba/', views.prueba_carga, name='prueba_carga'),
    path('reporte/', views.generar_reporte, name='generar_reporte'),
]