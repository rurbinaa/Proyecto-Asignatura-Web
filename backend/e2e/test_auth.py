"""
E2E: Authentication flow.

Tests login success, login failure, and logout.
Zero backend dependency — all API calls are mocked via page.route().
"""
import pytest
from playwright.sync_api import expect
from e2e.mocks.auth import mock_auth_success, mock_auth_failure
from e2e.conftest import E2E_EMAIL, E2E_PASSWORD


def test_login_success(logged_in_page):
    """After successful login, the sidebar should be visible.

    The ``logged_in_page`` fixture handles form filling and API mocking.
    We just assert the authenticated state.
    """
    assert logged_in_page.locator("aside.sidebar").is_visible()


def test_login_failure(page, base_url):
    """Invalid credentials should show an error message."""
    mock_auth_failure(page)

    page.goto(base_url)
    page.wait_for_selector('input[type="email"]', timeout=10000)

    page.locator('input[type="email"]').fill("wrong@user.com")
    page.locator('input[type="password"]').fill("wrong_pass")
    page.locator('button.login-button').click()

    # expect() auto-retries until the condition is met (handles React async state)
    expect(page.locator(".error-text")).to_be_visible()


def test_logout(logged_in_page):
    """Logout should clear the session and show the login card."""
    page = logged_in_page

    # Click logout button in sidebar
    page.locator(".sidebar-logout").click()

    # Should return to login view
    page.wait_for_selector(".login-card", timeout=10000)
    assert page.locator("aside.sidebar").count() == 0
