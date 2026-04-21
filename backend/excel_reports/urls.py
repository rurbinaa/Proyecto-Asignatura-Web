from django.urls import path
from . import views

app_name = 'excel_reports'

urlpatterns = [ 
    path('testing/', views.load_test, name='load_test'),
   path('report/', views.generate_excel, name='generate_excel'),
]