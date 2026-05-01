from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    
    Authenticate user and return JWT tokens with role.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class CurrentUserView(APIView):
    """
    GET /api/auth/me/
    
    Get current authenticated user's information.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        profile = user.profile
        if profile.role == 'operator':
            raise PermissionDenied('Operator role is no longer supported.')
        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': profile.role,
            'is_manager': profile.is_manager,
            'is_operator': profile.is_operator,
        })


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Logout user (currently a no-op since JWT is stateless).
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )
