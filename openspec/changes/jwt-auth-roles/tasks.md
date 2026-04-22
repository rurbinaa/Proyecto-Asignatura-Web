# Implementation Tasks: JWT Authentication with Roles

**Change:** jwt-auth-roles  
**Phase:** Implementation  
**References:**  
- Specs: `openspec/changes/jwt-auth-roles/specs/user-auth/spec.md`, `openspec/changes/jwt-auth-roles/specs/user-management/spec.md`  
- Design: `openspec/changes/jwt-auth-roles/design.md`

---

## Phase 1 - Infrastructure

### 1.1 Add rest_framework_simplejwt to INSTALLED_APPS

**File:** `backend/backend/settings.py`  
**Spec Reference:** user-management/spec.md - User Profile Model  
**Design Reference:** design.md - Security Decisions (JWT Settings)

**Task:**
- Add `'rest_framework_simplejwt'` to `INSTALLED_APPS` list
- Position: After existing DRF apps, before local apps

**Acceptance Criteria:**
- [x] `rest_framework_simplejwt` present in `INSTALLED_APPS`
- [x] No syntax errors in settings.py
- [x] Django starts without errors

---

### 1.2 Configure REST_FRAMEWORK with JWT authentication classes

**File:** `backend/backend/settings.py`  
**Spec Reference:** user-auth/spec.md - Token-Based Access Control  
**Design Reference:** design.md - Security Decisions (JWT Settings)

**Task:**
- Add `'rest_framework_simplejwt.authentication.JWTAuthentication'` to `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`
- Keep `'rest_framework.authentication.SessionAuthentication'` for admin/browsable API

**Acceptance Criteria:**
- [x] `JWTAuthentication` in `DEFAULT_AUTHENTICATION_CLASSES`
- [x] `SessionAuthentication` preserved
- [x] Order: JWT first, then Session

---

### 1.3 Add SIMPLE_JWT settings

**File:** `backend/backend/settings.py`  
**Spec Reference:** user-auth/spec.md - Token Security  
**Design Reference:** design.md - Security Decisions (JWT Settings)

**Task:**
- Add `SIMPLE_JWT` dictionary configuration with:
  - `ACCESS_TOKEN_LIFETIME`: timedelta(minutes=15) or from env `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`
  - `REFRESH_TOKEN_LIFETIME`: timedelta(days=7) or from env `JWT_REFRESH_TOKEN_LIFETIME_DAYS`
  - `ALGORITHM`: 'HS256'
  - `SIGNING_KEY`: from env `JWT_SECRET_KEY` or fallback to `SECRET_KEY`
  - `AUTH_HEADER_TYPES`: ('Bearer',)
  - `ROTATE_REFRESH_TOKENS`: False
  - `BLACKLIST_AFTER_ROTATION`: False

**Acceptance Criteria:**
- [x] All required SIMPLE_JWT settings present
- [x] Environment variable support for lifetimes and secret
- [x] Imports include `timedelta` and `os`

---

### 1.4 Create UserProfile model

**File:** `backend/auth_data/models.py`  
**Spec Reference:** user-management/spec.md - User Profile Model, Role Enumeration  
**Design Reference:** design.md - Data Model (UserProfile Model)

**Task:**
- Create `auth_data` app directory structure
- Create `UserProfile` model with:
  - `user`: OneToOneField to `auth.User`, `on_delete=models.CASCADE`, `related_name='profile'`
  - `role`: CharField with `max_length=20`, `choices=ROLE_CHOICES`
  - `ROLE_CHOICES`: `[('manager', 'Manager'), ('operator', 'Operator')]`
  - `created_at`: DateTimeField(auto_now_add=True)
  - `updated_at`: DateTimeField(auto_now=True)
  - `Meta`: `db_table='auth_data_userprofile'`
  - `__str__`: return f"{self.user.email} - {self.role}"
  - Properties: `is_manager`, `is_operator`

**Acceptance Criteria:**
- [x] Model matches design specification
- [x] OneToOne relationship enforced
- [x] Role choices constrained to 'manager' and 'operator'
- [x] String representation includes email and role

---

### 1.5 Create and run migration for UserProfile

**Files:** `backend/auth_data/migrations/0001_initial.py` (auto-generated)  
**Spec Reference:** user-management/spec.md - Database Schema  
**Design Reference:** design.md - Migration Strategy (Phase 1)

**Task:**
- Run `python manage.py makemigrations auth_data`
- Verify migration creates `auth_data_userprofile` table
- Run `python manage.py migrate`
- Verify no migration errors

**Acceptance Criteria:**
- [x] Migration file created with correct operations
- [x] Migration applies successfully
- [x] Table `auth_data_userprofile` exists in database
- [x] OneToOne constraint on `user_id` enforced

---

## Phase 2 - Implementation

### 2.1 Create CustomTokenObtainPairSerializer

**File:** `backend/auth_data/serializers.py`  
**Spec Reference:** user-auth/spec.md - Role Identification in Tokens  
**Design Reference:** design.md - Component Diagram (CustomTokenObtainPairSerializer)

**Task:**
- Create serializer extending `TokenObtainPairSerializer`
- Override `validate()` method to:
  - Call `super().validate(attrs)` to get default tokens
  - Get user profile: `profile = self.user.profile`
  - Add role to response: `data['role'] = profile.role`
  - Return modified data

**Acceptance Criteria:**
- [x] Serializer inherits from `TokenObtainPairSerializer`
- [x] `validate()` includes role in response
- [x] Role accessible via `user.profile.role`
- [x] Response format: `{access, refresh, role}`

---

### 2.2 Create AuthViewSet

**File:** `backend/auth_data/views.py`  
**Spec Reference:** user-auth/spec.md - Current User Endpoint, Logout Endpoint  
**Design Reference:** design.md - Component Diagram (Authentication Views)

**Task:**
- Create `AuthViewSet` (ViewSets.ModelViewSet or APIView-based) with:
  - **login** action (POST): Use `CustomTokenObtainPairSerializer`, return tokens + role
  - **me** action (GET): Return current user data `{id, email, first_name, last_name, role, is_manager, is_operator}`, require authentication
  - **logout** action (POST): Invalidate token (add to blacklist if enabled), return success message

**Acceptance Criteria:**
- [x] Login endpoint accepts email/password, returns 200 with tokens
- [x] Login with invalid credentials returns 401
- [x] /me/ returns user data with role for authenticated requests
- [x] /me/ returns 401 without token
- [x] Logout returns 200 for authenticated requests
- [x] Logout returns 401 without token

---

### 2.3 Configure router and URLs for auth endpoints

**File:** `backend/auth_data/urls.py`  
**Spec Reference:** user-auth/spec.md - All endpoint scenarios  
**Design Reference:** design.md - API Contract

**Task:**
- Create `auth_data/urls.py` with:
  - Router configuration for `AuthViewSet`
  - Routes:
    - `POST /login/` → login action
    - `GET /me/` → me action
    - `POST /logout/` → logout action
  - Optional: `POST /token/refresh/` for token refresh

**Acceptance Criteria:**
- [x] URLs properly configured with router
- [x] All three endpoints accessible
- [x] URL patterns match design spec

---

### 2.4 Include auth URLs in backend/urls.py

**File:** `backend/backend/urls.py`  
**Spec Reference:** user-auth/spec.md - All endpoint scenarios  
**Design Reference:** design.md - API Contract

**Task:**
- Import `auth_data.urls`
- Add path: `path('api/auth/', include('auth_data.urls'))`
- Ensure proper ordering (before catch-all patterns)

**Acceptance Criteria:**
- [x] Auth URLs included under `/api/auth/`
- [x] No URL conflicts
- [x] All endpoints accessible at correct paths

---

## Phase 3 - Seed Data

### 3.1 Create management/commands directory structure

**Files:**
- `backend/auth_data/management/__init__.py`
- `backend/auth_data/management/commands/__init__.py`

**Spec Reference:** user-management/spec.md - Hardcoded Users  
**Design Reference:** design.md - Migration Strategy (Phase 2)

**Task:**
- Create `management/` directory in `auth_data/`
- Create `commands/` subdirectory
- Add `__init__.py` files to make them Python packages

**Acceptance Criteria:**
- [x] Directory structure: `auth_data/management/commands/`
- [x] All `__init__.py` files present
- [x] Django recognizes management commands

---

### 3.2 Create seed_users.py command

**File:** `backend/auth_data/management/commands/seed_auth_users.py`  
**Spec Reference:** user-management/spec.md - Hardcoded Users, Idempotent seed operation  
**Design Reference:** design.md - Migration Strategy (Phase 2 - User Seeding)

**Task:**
- Create command extending `BaseCommand`
- Define `USERS` list with 6 hardcoded users:
  - manager1@uniwell.com (manager)
  - manager2@uniwell.com (manager)
  - manager3@uniwell.com (manager)
  - manager4@uniwell.com (manager)
  - operator1@uniwell.com (operator)
  - operator2@uniwell.com (operator)
- Default password: `password123`
- Use `get_or_create()` for idempotency
- Create UserProfile for each user
- Output: created/skipped counts

**Acceptance Criteria:**
- [x] Command runs with `python manage.py seed_auth_users`
- [x] Creates exactly 6 users on first run
- [x] Skips existing users on subsequent runs (idempotent)
- [x] Each user has associated UserProfile with correct role
- [x] All users have password `password123`
- [x] Console output shows created/skipped counts

---

### 3.3 Run seed_users command

**Command:** `python manage.py seed_auth_users`  
**Spec Reference:** user-management/spec.md - Seed command creates all 6 users  
**Design Reference:** design.md - Migration Strategy (Phase 2)

**Task:**
- Execute seed command
- Verify 6 users created
- Verify all profiles have correct roles

**Acceptance Criteria:**
- [x] Command completes successfully
- [x] 6 users exist in database
- [x] 4 managers, 2 operators
- [x] All users can authenticate with `password123`

---

## Phase 4 - Testing

### 4.1 Write test for successful login

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Successful login returns JWT tokens  
**Design Reference:** design.md - Testing Strategy (Integration - Login endpoint)

**Task:**
- Create test `test_login_success_returns_tokens_and_role`
- Use seeded user `manager1@uniwell.com` / `password123`
- POST to `/api/auth/login/`
- Assert:
  - Status code 200
  - Response contains `access` token
  - Response contains `refresh` token
  - Response contains `role` = 'manager'

**Acceptance Criteria:**
- [x] Test passes with valid credentials
- [x] All assertions verify correct response structure
- [x] Test isolated (uses test database)

---

### 4.2 Write test for invalid credentials

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Login with invalid credentials returns 401  
**Design Reference:** design.md - Testing Strategy (Integration - Login endpoint)

**Task:**
- Create test `test_login_invalid_credentials_returns_401`
- POST to `/api/auth/login/` with valid email but wrong password
- Assert:
  - Status code 401
  - Response contains error message

**Acceptance Criteria:**
- [x] Test passes with invalid password
- [x] 401 status returned
- [x] Error message present

---

### 4.3 Write test for /me/ with valid token

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Get current user with valid token  
**Design Reference:** design.md - Testing Strategy (Integration - /me/ endpoint)

**Task:**
- Create test `test_me_with_valid_token_returns_user_data`
- Login to get token
- GET `/api/auth/me/` with Authorization header
- Assert:
  - Status code 200
  - Response contains email
  - Response contains role
  - Role matches expected value

**Acceptance Criteria:**
- [x] Test passes with valid token
- [x] User data returned correctly
- [x] Role included in response

---

### 4.4 Write test for /me/ without token

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Get current user without token returns 401  
**Design Reference:** design.md - Testing Strategy (Integration - /me/ endpoint)

**Task:**
- Create test `test_me_without_token_returns_401`
- GET `/api/auth/me/` without Authorization header
- Assert:
  - Status code 401

**Acceptance Criteria:**
- [x] Test passes
- [x] 401 status returned for unauthenticated request

---

### 4.5 Write test for protected route without token

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Request without token returns 401  
**Design Reference:** design.md - Testing Strategy (Integration - Protected endpoints)

**Task:**
- Create test `test_protected_route_without_token_returns_401`
- Use existing protected endpoint (e.g., `/api/quality/kpis/` or create test view)
- GET without Authorization header
- Assert:
  - Status code 401

**Acceptance Criteria:**
- [x] Test passes
- [x] 401 status returned
- [x] JWT authentication enforced on protected routes

---

### 4.6 Write test for protected route with token

**File:** `backend/auth_data/tests/test_auth.py`  
**Spec Reference:** user-auth/spec.md - Request with valid token succeeds  
**Design Reference:** design.md - Testing Strategy (Integration - Protected endpoints)

**Task:**
- Create test `test_protected_route_with_token_succeeds`
- Login to get token
- GET protected endpoint with Authorization header
- Assert:
  - Status code 200

**Acceptance Criteria:**
- [x] Test passes
- [x] 200 status returned with valid token
- [x] Protected route accessible with JWT

---

### 4.7 Run all tests and verify pass

**Command:** `pytest backend/auth_data/tests/` or `python manage.py test auth_data`  
**Spec Reference:** All spec scenarios  
**Design Reference:** design.md - Testing Strategy

**Task:**
- Run full test suite for auth_data app
- Verify all tests pass
- Fix any failing tests
- Ensure code coverage is adequate

**Acceptance Criteria:**
- [x] All 7 tests from Phase 4 pass
- [x] No test failures
- [x] Tests run in isolation
- [x] No side effects on database

---

## Task Dependencies

```
Phase 1 (Infrastructure):
  1.1 → 1.2 → 1.3 (settings.py changes - can be done together)
  1.4 → 1.5 (model must exist before migration)

Phase 2 (Implementation):
  2.1 → 2.2 (serializer needed for view)
  2.2 → 2.3 → 2.4 (views → urls → include)

Phase 3 (Seed Data):
  3.1 → 3.2 → 3.3 (directory → command → execute)
  Depends on: Phase 1 (UserProfile model must exist)

Phase 4 (Testing):
  4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6 → 4.7
  Depends on: Phase 2 (endpoints must exist)
```

---

## Definition of Done

- [x] All 17 tasks completed
- [x] All tests passing (Phase 4)
- [x] Code follows design.md patterns
- [x] Specs in `openspec/changes/jwt-auth-roles/specs/` satisfied
- [x] No linting errors
- [x] Migrations applied successfully
- [x] Seed command runs without errors
- [ ] Manual testing confirms:
  - Login returns tokens + role
  - /me/ returns user data
  - Protected routes require JWT
  - Invalid credentials rejected
