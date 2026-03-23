from django.urls import path, include, re_path
from .views import CreateDefectView, UndoCaptureView

urlpatterns = [
    path('captura-defecto/', CreateDefectView.as_view({'post': 'capture_defect'}), name='capture-defect'),
    path('captura/undo/', UndoCaptureView.as_view({'delete': 'undo'}), name='undo-capture')
]