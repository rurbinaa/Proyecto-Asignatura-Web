"""
E2E test fixtures for Playwright — REAL backend, no mocks.

Requires: docker compose up (backend at localhost:8000, frontend at localhost:5173)
"""
import os
import pytest


E2E_EMAIL = os.getenv("E2E_EMAIL", "gerente@uniwell.com")
E2E_PASSWORD = os.getenv("E2E_PASSWORD", "password123")


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def django_db_setup():
    """Prevent pytest-django from creating a test database."""
    pass


@pytest.fixture
def page(context):
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def logged_in_page(page, base_url):
    """Log in with real credentials against the running backend."""
    page.goto(base_url)
    page.wait_for_selector('input[type="email"]', timeout=10000)

    page.locator('input[type="email"]').fill(E2E_EMAIL)
    page.locator('input[type="password"]').fill(E2E_PASSWORD)
    page.locator('button.login-button').click()

    # Wait for sidebar (auth success indicator)
    page.wait_for_selector('aside.sidebar', timeout=10000)

    return page
