from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, CurrentUserView, LogoutView


app_name = 'auth_data'


urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
]
