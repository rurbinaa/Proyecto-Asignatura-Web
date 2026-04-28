"""
E2E test fixtures for Playwright + Django.

Requires the app to be running (docker compose up or dev server).
Set E2E_BASE_URL env var or defaults to http://localhost:8000.
"""
import pytest


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
    
    # Fill credentials (LoginView uses email + password)
    page.locator('input[type="email"]').fill("admin@uniwell.com")
    page.locator('input[type="password"]').fill("admin")
    
    # Click login button
    page.locator('button[type="submit"]').click()
    
    # Wait for dashboard to load
    page.wait_for_url("**/dashboard**", timeout=10000)
    
    return page
