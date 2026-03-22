from django.urls import path, include, re_path
from .views import Process, SaveData, CreateDefectView, UndoCaptureView


urlpatterns = [
    path(r'process/<str:filename>/', Process.as_view(), name='process'),
    path(r'savedata/<str:filename>/', SaveData.as_view(), name='savedata'),
    path('captura-defecto/', CreateDefectView.as_view(), name='captura-defecto'),
    path('captura/undo/', UndoCaptureView.as_view(), name='undo-capture'),
]