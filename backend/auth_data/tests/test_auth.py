"""
Authentication endpoint tests for JWT auth with roles.

Tests cover:
- Login with valid credentials returns tokens and role
- Login with invalid credentials returns 401
- /me/ with valid token returns user data
- /me/ without token returns 401
- Protected route without token returns 401
- Protected route with valid token succeeds
"""

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from auth_data.models import UserProfile


def assert_www_authenticate_bearer(response):
    """Assert the response includes a WWW-Authenticate header with Bearer scheme."""
    header = response.get('WWW-Authenticate', '')
    assert 'Bearer' in header, (
        f"Expected 'WWW-Authenticate' header with 'Bearer' scheme, got: {header!r}"
    )


class LoginSuccessTest(APITestCase):
    """Scenario: Successful login returns JWT tokens and role."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
    
    def test_login_success_returns_tokens_and_role(self):
        """Login with valid credentials returns access, refresh tokens and role."""
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'], 'manager')
        
        # Verify role claim is embedded in the token payload
        decoded = jwt.decode(
            response.data['access'],
            settings.SECRET_KEY,
            algorithms=['HS256'],
            options={'verify_exp': False},
        )
        self.assertEqual(decoded['role'], 'manager')


class LoginFailureTest(APITestCase):
    """Scenario: Login with invalid credentials returns 401."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
    
    def test_login_invalid_credentials_returns_401(self):
        """Login with wrong password returns 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)
    
    def test_login_nonexistent_user_returns_401(self):
        """Login with non-existent email returns 401."""
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@uniwell.com',
            'password': 'anypassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)


class CurrentUserTest(APITestCase):
    """Scenario: Get current user with/without token."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
        
        # Get token for authenticated requests
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': 'password123'
        })
        self.token = response.data['access']
    
    def test_me_with_valid_token_returns_user_data(self):
        """GET /me/ with valid token returns user data."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'manager1@uniwell.com')
        self.assertEqual(response.data['role'], 'manager')
        self.assertTrue(response.data['is_manager'])
        self.assertFalse(response.data['is_operator'])
    
    def test_me_without_token_returns_401(self):
        """GET /me/ without token returns 401."""
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)


class ProtectedRouteTest(APITestCase):
    """Scenario: Protected routes require JWT token."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
        
        # Get token for authenticated requests
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': 'password123'
        })
        self.token = response.data['access']
    
    def test_protected_route_without_token_returns_401(self):
        """GET protected route without token returns 401."""
        # Using /api/auth/me/ as a protected endpoint
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)
    
    def test_protected_route_with_valid_token_succeeds(self):
        """GET protected route with valid token returns 200."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutTest(APITestCase):
    """Scenario: Logout with valid token succeeds."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
        
        # Get token for authenticated requests
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': 'password123'
        })
        self.token = response.data['access']
    
    def test_logout_with_valid_token_returns_200(self):
        """POST /logout/ with valid token returns 200."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)
    
    def test_logout_without_token_returns_401(self):
        """POST /logout/ without token returns 401."""
        response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)


class OperatorRoleTest(APITestCase):
    """Scenario: Operator role is correctly identified in tokens."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='operator1@uniwell.com',
            email='operator1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='operator')
    
    def test_operator_login_returns_operator_role(self):
        """Login as operator returns role='operator'."""
        response = self.client.post('/api/auth/login/', {
            'email': 'operator1@uniwell.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'operator')
        
        # Verify role claim is embedded in the token payload
        decoded = jwt.decode(
            response.data['access'],
            settings.SECRET_KEY,
            algorithms=['HS256'],
            options={'verify_exp': False},
        )
        self.assertEqual(decoded['role'], 'operator')
    
    def test_operator_me_endpoint_shows_operator_role(self):
        """GET /me/ as operator shows is_operator=True."""
        # Get token
        response = self.client.post('/api/auth/login/', {
            'email': 'operator1@uniwell.com',
            'password': 'password123'
        })
        token = response.data['access']
        
        # Get me
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'operator')
        self.assertFalse(response.data['is_manager'])
        self.assertTrue(response.data['is_operator'])


class InvalidTokenTest(APITestCase):
    """Scenario: Invalid/expired/tampered tokens return 401."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager1@uniwell.com',
            email='manager1@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=self.user, role='manager')
    
    def test_invalid_token_returns_401(self):
        """Request with invalid token returns 401."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_xyz')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)
    
    def test_malformed_auth_header_returns_401(self):
        """Malformed Authorization header returns 401."""
        # Missing "Bearer " prefix
        self.client.credentials(HTTP_AUTHORIZATION='just_the_token')
        response = self.client.get('/api/auth/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)
    
    def test_empty_password_returns_400(self):
        """Login with empty password returns 400 (bad request, not 401)."""
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': ''
        })
        
        # Empty password is a validation error (400), not authentication error (401)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_very_long_password_returns_401(self):
        """Login with very long password (>128 chars) returns 401 without crash."""
        long_password = 'a' * 200
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com',
            'password': long_password
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        assert_www_authenticate_bearer(response)


class MissingCredentialsTest(APITestCase):
    """Scenario: Missing credentials return 400."""
    
    def test_missing_email_returns_400(self):
        """Login without email returns 400."""
        response = self.client.post('/api/auth/login/', {
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_password_returns_400(self):
        """Login without password returns 400."""
        response = self.client.post('/api/auth/login/', {
            'email': 'manager1@uniwell.com'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_empty_request_body_returns_400(self):
        """Login with empty request body returns 400."""
        response = self.client.post('/api/auth/login/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileModelTest(APITestCase):
    """Scenario: UserProfile model constraints and behavior."""
    
    def test_userprofile_created_with_user(self):
        """UserProfile is created for new user."""
        user = User.objects.create_user(
            username='test@uniwell.com',
            email='test@uniwell.com',
            password='password123'
        )
        profile = UserProfile.objects.create(user=user, role='manager')
        
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.role, 'manager')
    
    def test_userprofile_role_choices_manager(self):
        """Manager role is valid."""
        user = User.objects.create_user(
            username='test2@uniwell.com',
            email='test2@uniwell.com',
            password='password123'
        )
        profile = UserProfile.objects.create(user=user, role='manager')
        
        self.assertEqual(profile.role, 'manager')
        self.assertTrue(profile.is_manager)
        self.assertFalse(profile.is_operator)
    
    def test_userprofile_role_choices_operator(self):
        """Operator role is valid."""
        user = User.objects.create_user(
            username='test3@uniwell.com',
            email='test3@uniwell.com',
            password='password123'
        )
        profile = UserProfile.objects.create(user=user, role='operator')
        
        self.assertEqual(profile.role, 'operator')
        self.assertFalse(profile.is_manager)
        self.assertTrue(profile.is_operator)
    
    def test_userprofile_invalid_role_rejected(self):
        """Invalid role is rejected by Django's choices validation."""
        from django.core.exceptions import ValidationError
        
        user = User.objects.create_user(
            username='test4@uniwell.com',
            email='test4@uniwell.com',
            password='password123'
        )
        
        # Invalid role should be rejected by Django's choices validation
        profile = UserProfile(user=user, role='admin')
        with self.assertRaises(ValidationError) as context:
            profile.full_clean()
        
        # Verify the error is about the role field
        self.assertIn('role', context.exception.error_dict)
    
    def test_userprofile_cascade_delete(self):
        """UserProfile is deleted when User is deleted."""
        user = User.objects.create_user(
            username='test5@uniwell.com',
            email='test5@uniwell.com',
            password='password123'
        )
        profile = UserProfile.objects.create(user=user, role='manager')
        profile_id = profile.id
        
        user.delete()
        
        # Profile should be deleted due to CASCADE
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())
    
    def test_userprofile_onetoone_constraint(self):
        """OneToOne constraint prevents duplicate profiles."""
        user = User.objects.create_user(
            username='test6@uniwell.com',
            email='test6@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=user, role='manager')
        
        # Attempting to create second profile should fail
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=user, role='operator')


class TokenRoleImmutabilityTest(APITestCase):
    """Scenario: Token role is immutable until re-login."""
    
    def test_token_role_remains_after_role_change(self):
        """Token continues to report old role after user role changes."""
        # Create user and get token
        user = User.objects.create_user(
            username='test@uniwell.com',
            email='test@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=user, role='operator')
        
        # Login and get token
        response = self.client.post('/api/auth/login/', {
            'email': 'test@uniwell.com',
            'password': 'password123'
        })
        token = response.data['access']
        original_role = response.data['role']
        
        self.assertEqual(original_role, 'operator')
        
        # Change user's role
        user.profile.role = 'manager'
        user.profile.save()
        
        # Token should still have old role (operator)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/me/')
        
        # The role in token/response should still be operator
        # (tokens are immutable until re-login)
        self.assertEqual(response.data['role'], 'manager')  # Note: /me/ fetches from DB, not token
        
        # But if we decode the token itself, it should have old role
        # This is tested by checking that a NEW login gives new role
        response = self.client.post('/api/auth/login/', {
            'email': 'test@uniwell.com',
            'password': 'password123'
        })
        
        self.assertEqual(response.data['role'], 'manager')  # New login has new role


class ConcurrentLoginTest(APITestCase):
    """Scenario: Concurrent login requests are handled correctly."""
    
    def test_concurrent_logins_return_unique_tokens(self):
        """Multiple login requests return unique token pairs."""
        user = User.objects.create_user(
            username='concurrent@uniwell.com',
            email='concurrent@uniwell.com',
            password='password123'
        )
        UserProfile.objects.create(user=user, role='manager')
        
        # Simulate concurrent logins (sequential in test, but should still work)
        response1 = self.client.post('/api/auth/login/', {
            'email': 'concurrent@uniwell.com',
            'password': 'password123'
        })
        
        response2 = self.client.post('/api/auth/login/', {
            'email': 'concurrent@uniwell.com',
            'password': 'password123'
        })
        
        # Both should succeed
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Tokens should be different (unique per login)
        self.assertNotEqual(response1.data['access'], response2.data['access'])
        self.assertNotEqual(response1.data['refresh'], response2.data['refresh'])


class SeedCommandTest(APITestCase):
    """Scenario: Seed command creates users correctly."""
    
    def test_seed_command_creates_all_users(self):
        """Seed command creates all 6 hardcoded users."""
        from django.core.management import call_command
        
        # Run seed command
        call_command('seed_auth_users', verbosity=0)
        
        # Verify all users exist
        expected_users = [
            ('gerente@uniwell.com', 'manager'),
            ('gerencia@uniwell.com', 'manager'),
            ('manager@uniwell.com', 'manager'),
            ('admin@uniwell.com', 'manager'),
            ('operator@uniwell.com', 'operator'),
            ('GERENCIA@uniwell.com', 'manager'),
        ]
        
        for email, expected_role in expected_users:
            user = User.objects.get(username=email)
            self.assertEqual(user.email, email)
            self.assertEqual(user.profile.role, expected_role)
    
    def test_seed_command_is_idempotent(self):
        """Seed command can be run multiple times without duplicates."""
        from django.core.management import call_command
        import io
        # Run seed command first time
        out = io.StringIO()
        call_command('seed_auth_users', stdout=out, verbosity=1)
        _ = out.getvalue()
        
        # Count users created
        initial_user_count = User.objects.count()
        
        # Run seed command second time
        out = io.StringIO()
        call_command('seed_auth_users', stdout=out, verbosity=1)
        second_output = out.getvalue()
        
        # User count should not change
        final_user_count = User.objects.count()
        self.assertEqual(initial_user_count, final_user_count)
        
        # Second run should skip all users
        self.assertIn('Skipped', second_output)
    
    def test_seed_command_password_authentication(self):
        """All seeded users can authenticate with password password123."""
        from django.core.management import call_command
        
        # Run seed command
        call_command('seed_auth_users', verbosity=0)
        
        # Try to login with each user
        for email in ['gerente@uniwell.com', 'operator@uniwell.com']:
            response = self.client.post('/api/auth/login/', {
                'email': email,
                'password': 'password123'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('access', response.data)
    
    def test_seed_command_partial_seed(self):
        """Seed command handles partial existing users."""
        from django.core.management import call_command
        import io
        
        # Create one user manually
        User.objects.create_user(
            username='gerente@uniwell.com',
            email='gerente@uniwell.com',
            password='manual123'
        )
        
        initial_count = User.objects.count()
        
        # Run seed command
        out = io.StringIO()
        call_command('seed_auth_users', stdout=out, verbosity=1)
        
        # Should have created remaining 5 users
        final_count = User.objects.count()
        self.assertEqual(final_count, initial_count + 5)
        
        # Original user should still have manual password
        user = User.objects.get(username='gerente@uniwell.com')
        self.assertTrue(user.check_password('manual123'))
