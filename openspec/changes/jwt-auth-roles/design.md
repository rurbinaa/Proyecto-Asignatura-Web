# Design: JWT Authentication with Roles

## Technical Approach

Implement JWT-based authentication using `djangorestframework-simplejwt` with a custom UserProfile extension pattern. The auth layer integrates with existing DRF configuration as a parallel authentication mechanism, allowing gradual migration from Session to JWT auth.

Key technical choices:
- **UserProfile model**: OneToOne extension pattern preserves Django User integrity while adding role field
- **Custom token serializer**: Embeds role claim in JWT payload at token generation time
- **Stateless auth**: JWT validation happens via DRF authentication classes, no session DB hits
- **Token blacklisting**: Optional via simplejwt's blacklist app for logout invalidation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Django Backend Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │   Frontend   │───→│   Nginx/     │───→│      DRF API Layer           │  │
│  │  (React)     │    │   Gunicorn   │    │  ┌────────────────────────┐  │  │
│  └──────────────┘    └──────────────┘    │  │  JWTAuthentication     │  │  │
│                                          │  │  (from simplejwt)      │  │  │
│                                          │  └────────────────────────┘  │  │
│                                          └──────────────────────────────┘  │
│                                                     │                        │
│                                                     ↓                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        auth_data App (NEW)                          │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │   │
│  │  │  UserProfile    │  │ CustomToken      │  │   Auth Views     │   │   │
│  │  │  (models.py)    │  │ Serializer       │  │   (views.py)     │   │   │
│  │  │  - user (O2O)   │  │ (serializers.py) │  │   - LoginView    │   │   │
│  │  │  - role         │  │ - adds role to   │  │   - MeView       │   │   │
│  │  │                 │  │   token claims   │  │   - LogoutView   │   │   │
│  │  └────────┬────────┘  └──────────────────┘  └──────────────────┘   │   │
│  │           │                                                         │   │
│  │           └──────────────────→ ┌──────────────┐                     │   │
│  │                                │   Django     │                     │   │
│  │                                │   User Model │                     │   │
│  │                                │   (built-in) │                     │   │
│  │                                └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Existing Apps (UNCHANGED)                       │   │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │   │
│  │  │ quality_data │    │  media_data  │    │   excel_importer     │   │   │
│  │  │   (KPIs)     │    │  (uploads)   │    │   (data sync)        │   │   │
│  │  └──────────────┘    └──────────────┘    └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           auth_data Components                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐         ┌──────────────────────────────────────┐
│      UserProfile Model      │         │      CustomTokenObtainPair           │
├─────────────────────────────┤         │           Serializer                 │
│                             │         ├──────────────────────────────────────┤
│  id: BigAutoField (PK)      │         │                                      │
│  user: OneToOne → User      │◄────────│  validate(attrs)                     │
│  role: CharField(choices)   │         │    ↓                                 │
│    - "manager"              │         │  data = super().validate(attrs)      │
│    - "operator"             │         │    ↓                                 │
│                             │         │  user = self.user                    │
│  class Meta:                │         │  profile = user.profile              │
│    db_table =               │         │    ↓                                 │
│    "auth_data_userprofile"  │         │  data['role'] = profile.role         │
│                             │         │    ↓                                 │
│  def __str__():             │         │  return data                         │
│    return f"{user.email}    │         │                                      │
│             - {role}"       │         │  (role embedded in JWT claims)       │
└─────────────────────────────┘         └──────────────────────────────────────┘
             │                                         │
             │ 1:1                                     │ validates
             │                                         │
             ▼                                         ▼
┌─────────────────────────────┐         ┌──────────────────────────────────────┐
│     Django User Model       │         │       Authentication Views           │
├─────────────────────────────┤         ├──────────────────────────────────────┤
│                             │         │                                      │
│  id                         │         │  LoginView(TokenObtainPairView)      │
│  username                   │         │  ─────────────────────────────────   │
│  email (used as username)   │         │  serializer_class = CustomToken      │
│  password                   │         │                                     │
│  first_name                 │         │  POST /api/auth/login/              │
│  last_name                  │         │    → {access, refresh, role}        │
│  is_active                  │         │                                      │
│  ...                        │         │  CurrentUserView(APIView)           │
│                             │         │  ─────────────────────────────      │
│  @property                  │         │  permission_classes = [IsAuth]      │
│  def profile(self):         │         │                                     │
│    return UserProfile       │         │  GET /api/auth/me/                  │
│      .objects               │         │    → {email, role, ...}             │
│      .get(user=self)        │         │                                      │
│                             │         │  LogoutView(APIView)                │
│                             │         │  ────────────────────               │
│                             │         │  POST /api/auth/logout/             │
│                             │         │    → blacklist token (if enabled)   │
│                             │         │    → 200 OK                         │
└─────────────────────────────┘         └──────────────────────────────────────┘
```

## Sequence Diagram: Login Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Client  │     │  DRF URL    │     │  CustomTokenView     │     │  CustomSerializer│     │  Database    │
│ (React) │     │  Router     │     │  (LoginView)         │     │                  │     │  (PostgreSQL)│
└────┬────┘     └──────┬──────┘     └──────────┬───────────┘     └────────┬─────────┘     └──────┬───────┘
     │                 │                       │                          │                    │
     │ POST /api/auth/login/                   │                          │                    │
     │ {email, password}                       │                          │                    │
     │────────────────>│                       │                          │                    │
     │                 │                       │                          │                    │
     │                 │───────route to view──>│                          │                    │
     │                 │                       │                          │                    │
     │                 │                       │───────call serializer───>│                    │
     │                 │                       │    validate()            │                    │
     │                 │                       │                          │                    │
     │                 │                       │                          │──SELECT user──────>│
     │                 │                       │                          │  WHERE email=...   │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │                       │                          │──SELECT profile───>│
     │                 │                       │                          │  WHERE user_id=... │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │                       │                          │───check password───│
     │                 │                       │                          │    (bcrypt)        │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │                       │<────return validated─────│                    │
     │                 │                       │     {access, refresh}    │                    │
     │                 │                       │                          │                    │
     │                 │                       │───────generate JWT───────│                    │
     │                 │                       │  payload contains:       │                    │
     │                 │                       │  {user_id, email, role}  │                    │
     │                 │                       │                          │                    │
     │                 │<────return response────│                          │                    │
     │                 │                       │                          │                    │
     │ 200 OK          │                       │                          │                    │
     │ {               │                       │                          │                    │
     │   access: "eyJ...",                    │                          │                    │
     │   refresh: "eyJ...",                   │                          │                    │
     │   role: "manager"                      │                          │                    │
     │ }               │                       │                          │                    │
     │<────────────────│                       │                          │                    │
     │                 │                       │                          │                    │

     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     ERROR PATH (Invalid Credentials)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

     │                 │                       │                          │                    │
     │ POST /api/auth/login/                   │                          │                    │
     │ {wrong_email, wrong_password}           │                          │                    │
     │────────────────>│                       │                          │                    │
     │                 │                       │                          │                    │
     │                 │                       │                          │──SELECT user──────>│
     │                 │                       │                          │  WHERE email=...   │
     │                 │                       │                          │<────NOT FOUND──────│
     │                 │                       │                          │                    │
     │                 │                       │<────raise Validation───│                    │
     │                 │                       │       Error              │                    │
     │                 │                       │                          │                    │
     │                 │<─────401 Unauthorized──│                          │                    │
     │                 │                       │                          │                    │
     │ 401 Unauthorized│                       │                          │                    │
     │ {detail: "No   │                       │                          │                    │
     │  active account │                       │                          │                    │
     │  found..."}     │                       │                          │                    │
     │<────────────────│                       │                          │                    │
     │                 │                       │                          │                    │
```

## Sequence Diagram: Authenticated Request Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Client  │     │  DRF URL    │     │  DRF Permission      │     │  JWT Auth Class  │     │  Database    │
│ (React) │     │  Router     │     │  Engine              │     │  (simplejwt)     │     │  (PostgreSQL)│
└────┬────┘     └──────┬──────┘     └──────────┬───────────┘     └────────┬─────────┘     └──────┬───────┘
     │                 │                       │                          │                    │
     │ GET /api/quality/kpis/                  │                          │                    │
     │ Authorization: Bearer eyJ...            │                          │                    │
     │────────────────>│                       │                          │                    │
     │                 │                       │                          │                    │
     │                 │───────dispatch───────>│                          │                    │
     │                 │                       │                          │                    │
     │                 │                       │────check permissions────>│                    │
     │                 │                       │                          │                    │
     │                 │                       │                          │──decode JWT───────→│
     │                 │                       │                          │  (validate sig,    │
     │                 │                       │                          │   check exp)       │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │                       │                          │──SELECT blacklist─>│
     │                 │                       │                          │  (if enabled)      │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │                       │<────return user object────│                    │
     │                 │                       │  {id, email, role} from   │                    │
     │                 │                       │  JWT claims               │                    │
     │                 │                       │                          │                    │
     │                 │                       │───────is_authenticated?──│                    │
     │                 │                       │                          │                    │
     │                 │                       │   YES → continue          │                    │
     │                 │                       │   NO  → 401 response      │                    │
     │                 │                       │                          │                    │
     │                 │                       │──────call view method─────│                    │
     │                 │                       │                          │                    │
     │                 │                       │                          │──SELECT kpis──────>│
     │                 │                       │                          │  WHERE ...         │
     │                 │                       │                          │<───────────────────│
     │                 │                       │                          │                    │
     │                 │<─────return response────│                          │                    │
     │                 │                       │                          │                    │
     │ 200 OK          │                       │                          │                    │
     │ {kpis: [...]}   │                       │                          │                    │
     │<────────────────│                       │                          │                    │
     │                 │                       │                          │                    │

     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     ERROR PATH (No Token / Invalid Token)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

     │                 │                       │                          │                    │
     │ GET /api/quality/kpis/                  │                          │                    │
     │ (No Authorization header)               │                          │                    │
     │────────────────>│                       │                          │                    │
     │                 │                       │                          │                    │
     │                 │                       │────check permissions────>│                    │
     │                 │                       │                          │                    │
     │                 │                       │<────no auth credentials───│                    │
     │                 │                       │                          │                    │
     │                 │                       │   → 401 Unauthorized      │                    │
     │                 │                       │   WWW-Authenticate:       │                    │
     │                 │                       │   Bearer                  │                    │
     │                 │                       │                          │                    │
     │                 │<─────401 Unauthorized──│                          │                    │
     │                 │                       │                          │                    │
     │ 401 Unauthorized│                       │                          │                    │
     │ {detail: "Auth-│                       │                          │                    │
     │  entication     │                       │                          │                    │
     │  credentials   │                       │                          │                    │
     │  not provided"} │                       │                          │                    │
     │<────────────────│                       │                          │                    │
     │                 │                       │                          │                    │
```

## Data Model

### UserProfile Model

```python
# backend/auth_data/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends Django User model with role information.
    OneToOne relationship ensures one profile per user.
    """
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('operator', 'Operator'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Associated Django user'
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text='User role determining access level'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_data_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.role}"
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_operator(self):
        return self.role == 'operator'


# Signal to auto-create profile when User is created (optional)
# Disabled for this implementation - profiles created by seed command only
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
```

### Database Schema

```sql
-- auth_data_userprofile table (auto-generated by Django migration)
CREATE TABLE auth_data_userprofile (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'operator')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index on user_id for fast lookups (auto-created by Django for OneToOne)
CREATE INDEX auth_data_userprofile_user_id_key ON auth_data_userprofile(user_id);

-- Index on role for filtering (optional, add if needed for admin queries)
-- CREATE INDEX auth_data_userprofile_role_idx ON auth_data_userprofile(role);
```

## API Contract

### 1. POST /api/auth/login/

**Request:**
```json
{
  "email": "manager1@uniwell.com",
  "password": "password123"
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE2MjE0NDAwLCJpYXQiOjE3MTYyMTQxMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxLCJlbWFpbCI6Im1hbmFnZXIxQHVuaXdlbGwuY29tIiwicm9sZSI6Im1hbmFnZXIifQ.signature",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcxNjgxODkwMCwiaWF0IjoxNzE2MjE0MTAwLCJqdGkiOiI5ODc2NTQzMjEwIiwidXNlcl9pZCI6MX0.signature",
  "role": "manager"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "No active account found with the given credentials"
}
```

**Validation Error (400 Bad Request):**
```json
{
  "email": ["This field is required."],
  "password": ["This field is required."]
}
```

---

### 2. GET /api/auth/me/

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "email": "manager1@uniwell.com",
  "first_name": "",
  "last_name": "",
  "role": "manager",
  "is_manager": true,
  "is_operator": false
}
```

**Error Response (401 Unauthorized - No Token):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Error Response (401 Unauthorized - Invalid/Expired Token):**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

---

### 3. POST /api/auth/logout/

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body (optional, if blacklist enabled):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "detail": "Successfully logged out."
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### JWT Token Payload Structure

**Access Token Decoded Payload:**
```json
{
  "token_type": "access",
  "exp": 1716214400,
  "iat": 1716214100,
  "jti": "unique-token-id",
  "user_id": 1,
  "email": "manager1@uniwell.com",
  "role": "manager"
}
```

**Refresh Token Decoded Payload:**
```json
{
  "token_type": "refresh",
  "exp": 1716818900,
  "iat": 1716214100,
  "jti": "unique-token-id",
  "user_id": 1
}
```

## Security Decisions

### JWT Settings

```python
# backend/backend/settings.py additions

from datetime import timedelta

# SimpleJWT configuration
SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(
        os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '15')
    )),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(
        os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7')
    )),
    
    # Rotation and blacklist settings
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    
    # Algorithm and signing
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    
    # Audience and issuer (optional, for multi-tenant scenarios)
    'AUDIENCE': None,
    'ISSUER': None,
    
    # Auth header settings
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token class settings
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    
    # Sliding token settings (not used with standard tokens)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Optional, for logout blacklisting
]

# Update REST_FRAMEWORK settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for admin/browseable API
    ],
}
```

### Security Checklist

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Signing Algorithm** | HS256 | HMAC-SHA256 provides adequate security, widely supported, performant |
| **Token Lifetime** | 15 min access, 7 day refresh | Balance between security (short access) and UX (longer refresh) |
| **Secret Key Source** | Environment variable `JWT_SECRET_KEY` | Falls back to Django SECRET_KEY for dev, production MUST set separate JWT secret |
| **Token Rotation** | Disabled | Simpler implementation, refresh tokens valid for full 7 days |
| **Blacklist** | Optional (configured off by default) | Can enable for stricter logout, adds DB query overhead |
| **Role in Token** | Embedded at generation time | Stateless role validation, tradeoff: role changes require re-login |
| **CORS** | Already configured | Existing CORS settings in place for localhost development |

### Environment Variables

```bash
# .env.example additions

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars-long!!
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

## Migration Strategy

### Phase 1: Safe Schema Addition (Zero Downtime)

The UserProfile model uses a **OneToOne relationship** which creates a new table without modifying the existing `auth_user` table:

```python
# Generated migration: 0001_initial.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('manager', 'Manager'), ('operator', 'Operator')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
            options={
                'db_table': 'auth_data_userprofile',
            },
        ),
    ]
```

**Why this is safe:**
- New table creation doesn't lock existing tables
- Existing User data remains untouched
- No foreign key constraints on auth_user that would block
- Can rollback by simply dropping the new table

### Phase 2: User Seeding (Idempotent)

The seed command is designed to be **idempotent and non-destructive**:

```python
# backend/auth_data/management/commands/seed_auth_users.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from auth_data.models import UserProfile


class Command(BaseCommand):
    help = 'Seed 6 hardcoded users with roles (idempotent)'
    
    USERS = [
        # (email, role)
        ('manager1@uniwell.com', 'manager'),
        ('manager2@uniwell.com', 'manager'),
        ('manager3@uniwell.com', 'manager'),
        ('manager4@uniwell.com', 'manager'),
        ('operator1@uniwell.com', 'operator'),
        ('operator2@uniwell.com', 'operator'),
    ]
    
    DEFAULT_PASSWORD = 'password123'
    
    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0
        
        for email, role in self.USERS:
            user, user_created = User.objects.get_or_create(
                username=email,  # Using email as username
                defaults={
                    'email': email,
                    'first_name': '',
                    'last_name': '',
                }
            )
            
            if user_created:
                user.set_password(self.DEFAULT_PASSWORD)
                user.save()
                UserProfile.objects.create(user=user, role=role)
                created_count += 1
                self.stdout.write(f"Created: {email} ({role})")
            else:
                skipped_count += 1
                self.stdout.write(f"Skipped (exists): {email}")
        
        self.stdout.write(self.style.SUCCESS(
            f'\nComplete: {created_count} created, {skipped_count} skipped'
        ))
```

### Phase 3: Rollback Plan

If issues occur, rollback is straightforward:

```bash
# 1. Revert REST_FRAMEWORK settings (remove JWTAuthentication)
# 2. Remove 'rest_framework_simplejwt' from INSTALLED_APPS
# 3. Remove auth URLs from main urls.py

# 4. Drop the UserProfile table (if migrations applied)
python manage.py migrate auth_data zero

# 5. Optional: Delete created users (if needed)
# python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(email__endswith='@uniwell.com').delete()"
```

### Phase 4: Existing Endpoint Migration

Existing endpoints (quality_data, media_data) will start requiring JWT auth automatically once `JWTAuthentication` is added to `DEFAULT_AUTHENTICATION_CLASSES`. This is the expected behavior per the spec.

For testing existing endpoints during transition:
```python
# Temporarily disable auth for specific endpoints if needed
class SomeExistingView(APIView):
    authentication_classes = []  # Override global setting
    permission_classes = [AllowAny]  # Open access
    ...
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/auth_data/__init__.py` | Create | App initialization |
| `backend/auth_data/apps.py` | Create | App configuration class |
| `backend/auth_data/models.py` | Create | UserProfile model with role field |
| `backend/auth_data/serializers.py` | Create | CustomTokenObtainPairSerializer |
| `backend/auth_data/views.py` | Create | LoginView, CurrentUserView, LogoutView |
| `backend/auth_data/urls.py` | Create | Auth URL routes (/api/auth/) |
| `backend/auth_data/admin.py` | Create | Admin registration for UserProfile |
| `backend/auth_data/tests/__init__.py` | Create | Tests package init |
| `backend/auth_data/tests/test_auth.py` | Create | Authentication tests |
| `backend/auth_data/tests/test_views.py` | Create | View/endpoint tests |
| `backend/auth_data/management/__init__.py` | Create | Management commands package |
| `backend/auth_data/management/commands/__init__.py` | Create | Commands package |
| `backend/auth_data/management/commands/seed_auth_users.py` | Create | User seeding command |
| `backend/auth_data/migrations/0001_initial.py` | Create | Initial UserProfile migration |
| `backend/backend/settings.py` | Modify | Add simplejwt, configure REST_FRAMEWORK auth |
| `backend/backend/urls.py` | Modify | Include auth_data URLs under /api/auth/ |

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit** | UserProfile model validation | Test role choices, string representation, properties |
| **Unit** | CustomTokenObtainPairSerializer | Test token generation includes role claim |
| **Integration** | Login endpoint | Test 200 with valid creds, 401 with invalid, 400 with missing fields |
| **Integration** | /me/ endpoint | Test 200 with valid token, 401 without, correct role in response |
| **Integration** | Logout endpoint | Test 200 with valid token, blacklist behavior if enabled |
| **Integration** | Protected endpoints | Test 401 without token, 200 with valid token |
| **Integration** | Seed command | Test idempotency, correct user/role creation |
| **Integration** | Token validation | Test expired token rejection, invalid signature rejection |

### Test Fixtures

```python
# backend/conftest.py additions

import pytest
from django.contrib.auth.models import User
from auth_data.models import UserProfile


@pytest.fixture
def manager_user(db):
    """Create a manager user with profile."""
    user = User.objects.create_user(
        username='manager@test.com',
        email='manager@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(user=user, role='manager')
    return user


@pytest.fixture
def operator_user(db):
    """Create an operator user with profile."""
    user = User.objects.create_user(
        username='operator@test.com',
        email='operator@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(user=user, role='operator')
    return user


@pytest.fixture
def manager_token(client, manager_user):
    """Get JWT access token for manager user."""
    response = client.post('/api/auth/login/', {
        'email': 'manager@test.com',
        'password': 'testpass123'
    })
    return response.data['access']
```

## Open Questions

- [ ] Should token blacklisting be enabled by default? Adds DB overhead but enables true logout
- [ ] Should we add a token refresh endpoint explicitly, or rely on simplejwt's default `/api/auth/token/refresh/`?
- [ ] Should UserProfile auto-create via signal, or always require explicit creation (current approach)?
