from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_data.urls', namespace='auth_data')),
    path('quality/', include('quality_data.urls', namespace='quality_data')),
]
