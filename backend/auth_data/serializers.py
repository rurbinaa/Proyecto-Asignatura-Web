from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that:
    - Accepts email field instead of username
    - Includes the user's role in the token payload and response
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace username field with email field
        self.fields['email'] = serializers.CharField(write_only=True)
        del self.fields['username']
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.profile.role
        return token
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            # Let parent's error handling deal with missing fields
            attrs['username'] = attrs.get('email', '')
            if 'email' in attrs:
                del attrs['email']
            return super().validate(attrs)
        
        # Look up user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Let authentication fail with proper error message
            attrs['username'] = email
            return super().validate(attrs)
        
        # Replace email with username for parent authentication
        attrs['username'] = user.username
        del attrs['email']

        if user.profile.role == 'operator':
            raise PermissionDenied('Operator role is no longer supported.')
        
        data = super().validate(attrs)
        data['role'] = self.user.profile.role
        return data
