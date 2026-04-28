"""
E2E: Navigation flow.

Tests sidebar view switching and active nav highlighting.
Zero backend dependency — all API calls are mocked via page.route().
Zero wait_for_timeout calls.
"""
import pytest
from playwright.sync_api import expect
from e2e.mocks.kpis import mock_kpi_data
from e2e.mocks.excel import mock_excel_preview


def test_sidebar_switches_views(logged_in_page):
    """Clicking sidebar nav items should switch the visible view.

    Note: ``title`` attribute on sidebar buttons is empty when the sidebar
    is expanded, so we match by span text content.
    """
    page = logged_in_page
    mock_kpi_data(page)
    mock_excel_preview(page)

    # After login, the manager default view is "excel" (Import Batches).
    # So the uploader-container should be visible initially.
    page.wait_for_selector(".uploader-container", timeout=5000)

    # Switch to Dashboard
    dashboard_btn = page.locator("button.sidebar-nav-item").filter(has_text="Dashboard")
    expect(dashboard_btn).to_be_visible(timeout=10000)
    dashboard_btn.click(force=True)
    page.wait_for_selector(".dashboard-view", timeout=10000)
    assert page.locator(".dashboard-view").is_visible()
    assert page.locator(".uploader-container").count() == 0

    # Switch back to Import Batches
    batches_btn = page.locator("button.sidebar-nav-item").filter(has_text="Import Batches")
    expect(batches_btn).to_be_visible(timeout=10000)
    batches_btn.click(force=True)
    page.wait_for_selector(".uploader-container", timeout=10000)
    assert page.locator(".uploader-container").is_visible()
    assert page.locator(".dashboard-view").count() == 0


def test_active_nav_highlight(logged_in_page):
    """The active sidebar nav item should have the .active class.

    Uses span text content since ``title`` attr is empty when sidebar
    is expanded. Uses ``expect().to_have_text()`` for auto-retry on
    React state updates — no ``wait_for_timeout`` needed.
    """
    page = logged_in_page

    # After login, default view is "Import Batches" (excel) for manager role
    active_btn = page.locator("button.sidebar-nav-item.active")
    expect(active_btn.locator("span")).to_have_text("Import Batches")

    # Click Dashboard
    dashboard_btn = page.locator("button.sidebar-nav-item").filter(has_text="Dashboard")
    expect(dashboard_btn).to_be_visible(timeout=10000)
    dashboard_btn.click(force=True)

    # expect() auto-retries until the condition is met
    active_btn = page.locator("button.sidebar-nav-item.active")
    expect(active_btn.locator("span")).to_have_text("Dashboard")

    # Click Import Batches again
    batches_btn = page.locator("button.sidebar-nav-item").filter(has_text="Import Batches")
    expect(batches_btn).to_be_visible(timeout=10000)
    batches_btn.click(force=True)

    active_btn = page.locator("button.sidebar-nav-item.active")
    expect(active_btn.locator("span")).to_have_text("Import Batches")
