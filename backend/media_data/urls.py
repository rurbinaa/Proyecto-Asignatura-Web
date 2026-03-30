from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import RevisionDefectViewSet, MockupViewSet

app_name = 'media_data'

router = DefaultRouter()
router.register(r'defects', RevisionDefectViewSet, basename='defect')
router.register(r'mockups', MockupViewSet, basename='mockup')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]