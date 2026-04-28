"""E2E: Auth flow against real backend."""
import pytest


def test_login_success(logged_in_page):
    """Login should show sidebar."""
    assert logged_in_page.locator('aside.sidebar').is_visible()


def test_login_failure(page, base_url):
    """Invalid credentials should show error."""
    page.goto(base_url)
    page.wait_for_selector('input[type="email"]', timeout=10000)
    page.locator('input[type="email"]').fill("wrong@user.com")
    page.locator('input[type="password"]').fill("wrong")
    page.locator('button.login-button').click()
    page.wait_for_timeout(2000)
    assert page.locator('aside.sidebar').count() == 0


def test_logout(logged_in_page):
    """Logout should return to login."""
    page = logged_in_page
    page.locator('button.sidebar-nav-item').filter(has_text="Log Out").click()
    page.wait_for_selector('input[type="email"]', timeout=5000)
    assert page.locator('input[type="email"]').is_visible()
