# Proposal: JWT Authentication with Roles

## Intent

Implement JWT-based authentication with role-based access control (RBAC) to ensure Uniwell's sensitive information is accessible only to authorized personnel. The system needs to distinguish between "manager" and "operator" roles to enable/block modules accordingly.

## Scope

### In Scope
- JWT token generation and validation using `djangorestframework-simplejwt`
- UserProfile model with role field (OneToOne with Django User)
- Custom login endpoint (`POST /api/auth/login/`) returning JWT tokens with role
- Current user endpoint (`GET /api/auth/me/`) returning user info with role
- Logout endpoint (`POST /api/auth/logout/`)
- Management command to seed 6 hardcoded users with roles
- Tests for all acceptance criteria (token generation, 401 without token, role identification)
- DRF configuration for JWT authentication classes

### Out of Scope
- Password reset functionality
- Email verification
- OAuth/social authentication
- Fine-grained permissions beyond manager/operator roles
- Frontend login UI implementation

## Capabilities

### New Capabilities
- `user-auth`: User authentication via JWT tokens with role-based access control
- `user-management`: User profile management with role assignment

### Modified Capabilities
None

## Approach

1. **Add `rest_framework_simplejwt`** to `INSTALLED_APPS` in settings.py
2. **Create UserProfile model** in a new `auth_data` app with OneToOne relationship to User and `role` field (choices: manager, operator)
3. **Custom TokenObtainPairSerializer** to include user role in access token claims
4. **Create views**:
   - Custom TokenObtainPairView for `/api/auth/login/`
   - CurrentUserView for `/api/auth/me/` (returns user + role)
   - LogoutView for `/api/auth/logout/` (client-side token removal, server-side blacklist if enabled)
5. **Management command** `seed_auth_users` to create 6 hardcoded users with roles
6. **Configure REST_FRAMEWORK** settings with JWT authentication classes as default
7. **Write comprehensive tests** covering all acceptance criteria

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/backend/settings.py` | Modified | Add simplejwt to INSTALLED_APPS, configure REST_FRAMEWORK with JWT auth |
| `backend/auth_data/models.py` | New | UserProfile model with role field |
| `backend/auth_data/serializers.py` | New | Custom TokenObtainPairSerializer with role |
| `backend/auth_data/views.py` | New | Login, /me/, logout views |
| `backend/auth_data/urls.py` | New | Auth route configuration |
| `backend/backend/urls.py` | Modified | Include auth_data URLs under `/api/auth/` |
| `backend/auth_data/management/commands/seed_auth_users.py` | New | Seed hardcoded users |
| `backend/auth_data/tests/` | New | Tests for auth endpoints and role-based access |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| JWT secret key not properly configured in production | Medium | Use environment variable `JWT_SECRET_KEY`, document in .env.example |
| Token expiration too short/long for UX | Low | Use default simplejwt settings (5min access, 7day refresh), adjustable via settings |
| Role hardcoded in token, changes require re-login | Low | Acceptable tradeoff; role changes are rare, user can re-login |
| Existing tests break with new auth requirements | Medium | Add authentication fixtures to existing tests, keep tests isolated |

## Rollback Plan

1. Remove `auth_data` app from `INSTALLED_APPS`
2. Delete `auth_data/` directory
3. Remove `/api/auth/` routes from `backend/urls.py`
4. Revert `REST_FRAMEWORK` settings to use SessionAuthentication only
5. Drop `auth_data_userprofile` table if migrations were applied: `python manage.py migrate auth_data zero`
6. Remove `djangorestframework-simplejwt` from requirements.txt (optional, already installed)

## Dependencies

- `djangorestframework-simplejwt` (already in requirements.txt)
- Django User model (built-in)

## Success Criteria

- [ ] `POST /api/auth/login/` returns valid JWT token for valid credentials
- [ ] `POST /api/auth/login/` returns 401 for invalid credentials
- [ ] API routes return 401 Unauthorized when no token is provided
- [ ] `GET /api/auth/me/` returns current user with `role` field ("manager" or "operator")
- [ ] `POST /api/auth/logout/` successfully logs out user
- [ ] All 6 hardcoded users exist with correct roles (4 managers, 2 operators)
- [ ] Tests pass with >90% coverage on auth module
