"""
E2E: Dashboard KPI rendering.

Tests KPI cards rendering, filter bar visibility, refresh button, and
volatile helper display. Zero backend dependency — all API calls
are mocked via page.route().
"""
import pytest
from e2e.mocks.kpis import mock_kpi_data, mock_volatile_kpis
from e2e.mocks.excel import mock_excel_preview


def _navigate_to_dashboard(page):
    """Click the Dashboard nav item in the sidebar.

    Uses expect() for auto-retry since React re-renders detach DOM elements
    during view transitions.
    """
    from playwright.sync_api import expect
    dashboard_btn = page.locator("button.sidebar-nav-item").filter(has_text="Dashboard")
    expect(dashboard_btn).to_be_visible(timeout=10000)
    dashboard_btn.click(force=True)
    page.wait_for_selector(".dashboard-view", timeout=10000)


def test_kpi_cards_render(logged_in_page):
    """Dashboard masonry should contain KPI cards after loading."""
    page = logged_in_page
    mock_kpi_data(page)

    _navigate_to_dashboard(page)

    masonry = page.locator(".dashboard-masonry")
    assert masonry.count() > 0
    # Wait for KPI data to load (masonry should have children)
    page.wait_for_selector(".dashboard-masonry > *", timeout=10000)


def test_filter_bar_visible(logged_in_page):
    """Dashboard filter bar should be visible with filter controls."""
    page = logged_in_page
    mock_kpi_data(page)

    _navigate_to_dashboard(page)

    filter_bar = page.locator(".filter-bar")
    assert filter_bar.is_visible()

    # Should have at least 6 filter inputs (team, style, color, customer,
    # batch — week and date range may also be present)
    filter_inputs = page.locator(".filter-input")
    assert filter_inputs.count() >= 6


def test_refresh_button(logged_in_page):
    """Refresh button should re-fetch KPI data without errors."""
    page = logged_in_page
    mock_kpi_data(page)

    _navigate_to_dashboard(page)

    masonry = page.locator(".dashboard-masonry")
    page.wait_for_selector(".dashboard-masonry > *", timeout=10000)

    refresh_btn = page.locator("button.refresh-btn")
    assert refresh_btn.is_visible()

    refresh_btn.click()

    # Masonry should still have children after refresh
    page.wait_for_selector(".dashboard-masonry > *", timeout=10000)
    assert masonry.locator("> *").count() > 0


def test_volatile_helper(logged_in_page, test_excel_file):
    """Volatile helper visibility depends on dashboard mode.

    - Live mode (sidebar Dashboard click): helper NOT visible.
    - Fast mode (via Excel uploader → View Dashboard): helper IS visible.
    """
    page = logged_in_page
    mock_excel_preview(page)
    mock_volatile_kpis(page)

    # ── Sub-test 1: Live mode → helper NOT visible ──
    _navigate_to_dashboard(page)
    assert page.locator(".volatile-helper").count() == 0

    # ── Sub-test 2: Fast mode → helper IS visible ──
    # Go to Import Batches
    from playwright.sync_api import expect
    batches_btn = page.locator("button.sidebar-nav-item").filter(has_text="Import Batches")
    expect(batches_btn).to_be_visible(timeout=10000)
    batches_btn.click(force=True)
    page.wait_for_selector(".uploader-container", timeout=10000)

    # Upload the generated Excel file via the dropzone hidden input
    file_input = page.locator(".dropzone input[type='file']")
    file_input.set_input_files(str(test_excel_file))
    page.wait_for_selector(".file-preview", timeout=5000)

    # Click "Analyze File"
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()

    # Wait for preview to be ready
    page.wait_for_selector(".backend-stats-container", timeout=10000)

    # Click "View Dashboard (Fast Mode)"
    page.locator("button.ingesta-btn-outline").filter(has_text="View Dashboard").click()
    page.wait_for_selector(".dashboard-view", timeout=10000)

    # Volatile helper should be visible in fast mode
    assert page.locator(".volatile-helper").is_visible()
