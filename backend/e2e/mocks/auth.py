"""
Mock auth API route handlers for E2E tests.

Provides factories that register page.route() interceptors for all auth endpoints:
POST /api/auth/login/, GET /api/auth/me/, POST /api/auth/logout/.
"""

import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:5173",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
}

E2E_ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ1NzAwMDAwLCJpYXQiOjE3NDU2OTY0MDAsImp0aSI6Im1vY2stand0LWlkIiwidXNlcl9pZCI6MX0."
    "mock-signature"
)
E2E_REFRESH_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc0NTc4NjQwMCwiaWF0IjoxNzQ1Njk2NDAwLCJqdGkiOiJtb2NrLXJlZnJlc2gtaWQiLCJ1c2VyX2lkIjoxfQ."
    "mock-signature"
)

LOGIN_SUCCESS_RESPONSE = {
    "access": E2E_ACCESS_TOKEN,
    "refresh": E2E_REFRESH_TOKEN,
    "role": "manager",
}

LOGIN_FAILURE_RESPONSE = {"detail": "Invalid credentials"}

ME_RESPONSE = {
    "id": 1,
    "email": "gerente@uniwell.com",
    "first_name": "Gerente",
    "last_name": "Uniwell",
    "role": "manager",
    "is_manager": True,
    "is_operator": False,
}

LOGOUT_RESPONSE = {"detail": "Successfully logged out."}


def _handle_options(route):
    """Handle CORS preflight."""
    route.fulfill(status=200, headers=CORS_HEADERS)


def _login_success_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    body = json.dumps(LOGIN_SUCCESS_RESPONSE)
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def _login_failure_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    body = json.dumps(LOGIN_FAILURE_RESPONSE)
    route.fulfill(
        status=401,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def _me_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    body = json.dumps(ME_RESPONSE)
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def _logout_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    body = json.dumps(LOGOUT_RESPONSE)
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def mock_auth_success(page):
    """Register all happy-path auth route interceptors.

    Intercepts:
    - POST /api/auth/login/ → 200 + tokens + role
    - GET  /api/auth/me/    → 200 + manager profile
    - POST /api/auth/logout/ → 200 + success detail
    """
    page.route("**/api/auth/login/", _login_success_handler)
    page.route("**/api/auth/me/", _me_handler)
    page.route("**/api/auth/logout/", _logout_handler)


def mock_auth_failure(page):
    """Register auth route interceptors for failed login.

    Intercepts:
    - POST /api/auth/login/ → 401 + error detail
    """
    page.route("**/api/auth/login/", _login_failure_handler)
