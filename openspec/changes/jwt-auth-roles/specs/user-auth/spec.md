# User Authentication Specification

## Purpose

Define JWT-based authentication with role-based access control (RBAC) for the Uniwell system. The system MUST distinguish between "manager" and "operator" roles to enable appropriate module access.

## Functional Requirements

### Requirement: JWT Token Generation

The system MUST generate a valid JWT access token and refresh token upon successful user authentication.

#### Scenario: Successful login returns JWT tokens

- GIVEN a user exists with email "manager1@uniwell.com" and password "password123"
- WHEN the user sends POST /api/auth/login/ with valid credentials
- THEN the response MUST contain an access token
- AND the response MUST contain a refresh token
- AND the response MUST include the user's role in the token claims
- AND the response status MUST be 200 OK

#### Scenario: Login with invalid credentials returns 401

- GIVEN a user exists with email "manager1@uniwell.com" and password "password123"
- WHEN the user sends POST /api/auth/login/ with email "manager1@uniwell.com" and password "wrongpassword"
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST contain an error message indicating invalid credentials

#### Scenario: Login with non-existent user returns 401

- GIVEN no user exists with email "nonexistent@uniwell.com"
- WHEN the client sends POST /api/auth/login/ with email "nonexistent@uniwell.com" and any password
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST NOT reveal whether the email exists

---

### Requirement: Token-Based Access Control

The system MUST reject API requests without a valid JWT token.

#### Scenario: Request without token returns 401

- GIVEN a protected API endpoint /api/some-resource/
- WHEN a client sends a request without an Authorization header
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST include a WWW-Authenticate header with "Bearer" scheme

#### Scenario: Request with invalid token returns 401

- GIVEN a protected API endpoint /api/some-resource/
- WHEN a client sends a request with Authorization header "Bearer invalid_token"
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST indicate the token is invalid or expired

#### Scenario: Request with expired token returns 401

- GIVEN a valid access token that has expired
- WHEN a client uses this token to access a protected endpoint
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST indicate the token has expired

#### Scenario: Request with valid token succeeds

- GIVEN a valid access token for user "manager1@uniwell.com"
- WHEN a client sends a request with Authorization header "Bearer {valid_token}"
- THEN the response status MUST be 200 OK
- AND the server MUST identify the requesting user from the token

---

### Requirement: Role Identification in Tokens

The system MUST include the user's role in the JWT token claims.

#### Scenario: Manager token contains manager role

- GIVEN a user with email "manager1@uniwell.com" has role "manager"
- WHEN the user logs in successfully
- THEN the access token payload MUST contain a "role" claim with value "manager"

#### Scenario: Operator token contains operator role

- GIVEN a user with email "operator1@uniwell.com" has role "operator"
- WHEN the user logs in successfully
- THEN the access token payload MUST contain a "role" claim with value "operator"

#### Scenario: Token role is immutable

- GIVEN a user has obtained an access token with role "operator"
- WHEN the user's role is changed to "manager" in the database
- THEN the existing token MUST continue to report role "operator" until expiration
- AND a new login MUST be required to obtain a token with the updated role

---

### Requirement: Current User Endpoint

The system MUST provide an endpoint to retrieve the current authenticated user's information including their role.

#### Scenario: Get current user with valid token

- GIVEN a user with email "manager1@uniwell.com" and role "manager" has a valid access token
- WHEN the user sends GET /api/auth/me/ with the Authorization header
- THEN the response status MUST be 200 OK
- AND the response body MUST contain email "manager1@uniwell.com"
- AND the response body MUST contain role "manager"
- AND the response body MAY contain additional user profile fields

#### Scenario: Get current user without token returns 401

- GIVEN no Authorization header is provided
- WHEN a client sends GET /api/auth/me/
- THEN the response status MUST be 401 Unauthorized

---

### Requirement: Logout Endpoint

The system MUST provide a logout endpoint to invalidate user sessions.

#### Scenario: Logout with valid token succeeds

- GIVEN a user has a valid access token
- WHEN the user sends POST /api/auth/logout/ with the Authorization header
- THEN the response status MUST be 200 OK
- AND the response MUST indicate successful logout
- AND the access token SHOULD be added to a blacklist if token blacklisting is enabled

#### Scenario: Logout without token returns 401

- GIVEN no Authorization header is provided
- WHEN a client sends POST /api/auth/logout/
- THEN the response status MUST be 401 Unauthorized

#### Scenario: Blacklisted token is rejected

- GIVEN token blacklisting is enabled
- AND a user has logged out, adding their token to the blacklist
- WHEN the user attempts to use the blacklisted token
- THEN the response status MUST be 401 Unauthorized
- AND the response MUST indicate the token has been invalidated

---

## Non-Functional Requirements

### Requirement: Token Security

The system MUST implement secure JWT token handling.

#### Scenario: Tokens use secure signing algorithm

- GIVEN the JWT configuration
- THEN the signing algorithm MUST be HS256 or stronger
- AND the secret key MUST be at least 256 bits

#### Scenario: Access tokens have limited lifetime

- GIVEN the JWT configuration
- THEN access tokens MUST expire within 15 minutes or less by default
- AND the expiration time SHOULD be configurable via environment variables

#### Scenario: Refresh tokens have extended lifetime

- GIVEN the JWT configuration
- THEN refresh tokens MUST have a longer lifetime than access tokens
- AND refresh tokens SHOULD expire after 7 days of inactivity
- AND refresh token lifetime SHOULD be configurable via environment variables

#### Scenario: Secret key from environment

- GIVEN the application is running in production
- THEN the JWT signing secret MUST be loaded from environment variables
- AND the secret MUST NOT be hardcoded in source code

---

### Requirement: Authentication Performance

The system SHOULD complete authentication operations within acceptable time limits.

#### Scenario: Login response time

- GIVEN typical server load
- WHEN a user sends a login request
- THEN the response time SHOULD be less than 500ms
- AND the response time MUST be less than 2000ms

#### Scenario: Token validation performance

- GIVEN a protected endpoint is accessed
- WHEN the server validates the JWT token
- THEN the validation overhead SHOULD be less than 50ms per request

---

## Error Handling Requirements

### Requirement: Authentication Error Responses

The system MUST provide clear, consistent error responses for authentication failures.

#### Scenario: Missing credentials returns 400

- GIVEN a login request
- WHEN the request body is missing email or password fields
- THEN the response status MUST be 400 Bad Request
- AND the response MUST indicate which fields are missing

#### Scenario: Malformed authorization header returns 401

- GIVEN a request with an Authorization header
- WHEN the header format is not "Bearer {token}"
- THEN the response status MUST be 401 Unauthorized
- AND the response SHOULD indicate the expected format

---

## Edge Cases

### Requirement: Edge Case Handling

The system MUST handle edge cases gracefully.

#### Scenario: Login with empty password

- GIVEN a login request
- WHEN the password field is empty string ""
- THEN the response status MUST be 400 Bad Request
- AND the response MUST indicate the password field validation error
- NOTE: Empty string fails DRF field validation before authentication, so it is a 400 (validation error) rather than a 401 (authentication error)

#### Scenario: Login with very long password

- GIVEN a login request
- WHEN the password exceeds 128 characters
- THEN the response status MUST be 401 Unauthorized
- AND the server MUST NOT crash or hang

#### Scenario: Concurrent login requests

- GIVEN a valid user
- WHEN multiple login requests are sent simultaneously
- THEN each successful request MUST receive a unique token pair
- AND the server MUST handle all requests without errors

#### Scenario: Token with tampered payload

- GIVEN a valid access token
- WHEN the token payload is modified and re-sent
- THEN the signature verification MUST fail
- AND the response status MUST be 401 Unauthorized
