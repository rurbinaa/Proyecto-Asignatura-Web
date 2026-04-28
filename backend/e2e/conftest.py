"""
E2E test fixtures for Playwright + Django.

Requires the app to be running (docker compose up or dev server).
Set E2E_BASE_URL env var or defaults to http://localhost:8000.
"""
import os
import pytest


E2E_EMAIL = os.getenv("E2E_EMAIL", "gerente@uniwell.com")
E2E_PASSWORD = os.getenv("E2E_PASSWORD", "password123")


def pytest_collection_modifyitems(items):
    """Auto-mark all tests in e2e/ as e2e."""
    for item in items:
        item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def django_db_setup():
    """E2E tests use the running app's DB, not a test DB."""
    pass


@pytest.fixture
def page(context):
    """Fresh page per test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def logged_in_page(page, base_url):
    """Navigate to app and log in with test credentials."""
    page.goto(base_url)
    # Wait for login form
    page.wait_for_selector('input[type="email"]', timeout=10000)
    
    # Fill credentials (overridable via E2E_EMAIL / E2E_PASSWORD env vars)
    page.locator('input[type="email"]').fill(E2E_EMAIL)
    page.locator('input[type="password"]').fill(E2E_PASSWORD)
    
    # Click login button
    page.locator('button[type="submit"]').click()
    
    # Wait for dashboard to load
    page.wait_for_url("**/dashboard**", timeout=10000)
    
    return page
