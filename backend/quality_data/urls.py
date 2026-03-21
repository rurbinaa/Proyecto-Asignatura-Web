from django.urls import path, include, re_path
from .views import Process, SaveData


urlpatterns = [
    path(r'process/<str:filename>/', Process.as_view(), name='process'),
    path(r'savedata/<str:filename>/', SaveData.as_view(), name='savedata')
]