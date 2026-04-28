"""
E2E: Authentication flow.

Requires app running: docker compose up
"""
import pytest


def test_login_redirects_to_dashboard(logged_in_page, base_url):
    """After login, user should land on dashboard."""
    assert "dashboard" in logged_in_page.url.lower()


def test_login_rejects_invalid_credentials(page, base_url):
    """Invalid credentials should show error."""
    page.goto(base_url)
    page.wait_for_selector('input[type="text"], input[name="username"]', timeout=5000)

    username = page.locator('input[type="text"], input[name="username"]').first
    password = page.locator('input[type="password"]').first

    username.fill("wrong_user")
    password.fill("wrong_pass")
    page.locator('button[type="submit"]').click()

    # Should show error or stay on login
    page.wait_for_timeout(2000)
    assert "dashboard" not in page.url.lower()
