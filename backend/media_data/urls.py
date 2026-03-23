from django.urls import path, include, re_path
from .views import CreateDefectView, UndoCaptureView

urlpatterns = [
    path('captura-defecto/', CreateDefectView.as_view(), name='captura-defecto'),
    path('captura/undo/', UndoCaptureView.as_view(), name='undo-capture')
]