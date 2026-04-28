"""
E2E test fixtures for Playwright — zero backend dependency.

All API calls are intercepted via page.route() mock handlers.
No Django, no running backend required.
"""
import os
import pytest

from e2e.mocks.auth import mock_auth_success
from e2e.mocks.kpis import mock_kpi_data
from e2e.fixtures.generate_excel import generate_test_excel


E2E_EMAIL = os.getenv("E2E_EMAIL", "gerente@uniwell.com")
E2E_PASSWORD = os.getenv("E2E_PASSWORD", "password123")


def pytest_collection_modifyitems(items):
    """Auto-mark all tests in e2e/ as e2e."""
    for item in items:
        item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def django_db_setup():
    """Prevent pytest-django from creating a test database.

    E2E tests mock all API calls — no database is needed.
    """
    pass


@pytest.fixture
def page(context):
    """Fresh page per test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def logged_in_page(page, base_url):
    """Navigate to app, mock all auth APIs, and log in with test credentials.

    Uses page.route() for ALL auth API calls so no backend is needed.
    After login, waits for ``aside.sidebar`` as post-login detection
    (the app is an SPA with no URL routing).
    """
    # Mock all auth endpoints before navigating
    mock_auth_success(page)

    page.goto(base_url)
    page.wait_for_selector('input[type="email"]', timeout=10000)

    page.locator('input[type="email"]').fill(E2E_EMAIL)
    page.locator('input[type="password"]').fill(E2E_PASSWORD)
    page.locator('button.login-button').click()

    # Wait for authenticated state — sidebar appears after successful login
    page.wait_for_selector('aside.sidebar', timeout=10000)

    return page


@pytest.fixture
def test_excel_file(tmp_path):
    """Generate a test .xlsx file using openpyxl.

    Returns a Path to the generated file with 5 sheets of deterministic data.
    """
    return generate_test_excel(tmp_path)
