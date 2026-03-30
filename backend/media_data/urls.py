from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import RevisionDefectViewSet, MockupViewSet

app_name = 'media_data'

router = DefaultRouter()
router.register(r'defects', RevisionDefectViewSet, basename='defect')
router.register(r'mockups', MockupViewSet, basename='mockup')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    