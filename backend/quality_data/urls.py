from django.urls import path, include, re_path
from .views import Process, SaveData, ExcelPreviewView, ExcelConfirmView, ExcelRejectView

app_name = 'quality_data'

urlpatterns = [
    # Legacy endpoints (kept for backward compatibility)
    path(r'process/<str:filename>/', Process.as_view(), name='process'),
    path(r'savedata/<str:filename>/', SaveData.as_view(), name='savedata'),

    # V2 endpoints — Preview → Confirm → Apply workflow
    path(r'excel/preview/<str:filename>/', ExcelPreviewView.as_view(), name='excel-preview'),
    path(r'excel/confirm/<int:session_id>/', ExcelConfirmView.as_view(), name='excel-confirm'),
    path(r'excel/reject/<int:session_id>/', ExcelRejectView.as_view(), name='excel-reject'),
]
