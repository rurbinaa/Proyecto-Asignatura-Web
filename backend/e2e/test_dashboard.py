"""E2E: Dashboard KPI rendering against real backend."""
import pytest
from playwright.sync_api import expect


def _go_to_dashboard(page):
    """Click Dashboard in sidebar."""
    btn = page.locator("button.sidebar-nav-item").filter(has_text="Dashboard")
    expect(btn).to_be_visible(timeout=5000)
    btn.click(force=True)
    page.wait_for_selector(".dashboard-view", timeout=10000)


def test_dashboard_renders(logged_in_page):
    """Dashboard should render with masonry layout."""
    page = logged_in_page
    _go_to_dashboard(page)
    assert page.locator(".dashboard-masonry").is_visible()
    assert page.locator(".dashboard-title").is_visible()


def test_filter_bar_visible(logged_in_page):
    """Filter bar should be visible."""
    page = logged_in_page
    _go_to_dashboard(page)
    assert page.locator(".filter-bar").is_visible()
