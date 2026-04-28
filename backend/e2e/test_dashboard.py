"""
E2E: Dashboard KPI rendering.

Requires app running: docker compose up
"""
import pytest


def test_dashboard_renders_kpi_cards(logged_in_page):
    """Dashboard should show KPI cards after login."""
    page = logged_in_page

    # KPI cards should appear (they have kpi-card class or are inside masonry)
    page.wait_for_timeout(3000)
    cards = page.locator('.kpi-card, [class*="kpi"]')
    count = cards.count()
    assert count > 0, f"Expected KPI cards, found {count}"


def test_dashboard_shows_filter_bar(logged_in_page):
    """Filter bar should be visible on dashboard."""
    page = logged_in_page
    page.wait_for_timeout(2000)

    # Filter bar with date inputs or filter selects
    filter_bar = page.locator('[class*="filter"], input[type="date"]')
    assert filter_bar.count() > 0, "Filter bar not found"


def test_dashboard_has_masonry_layout(logged_in_page):
    """Dashboard should render in masonry layout."""
    page = logged_in_page
    page.wait_for_timeout(2000)

    masonry = page.locator('[class*="masonry"]')
    assert masonry.count() > 0, "Masonry layout not found"
