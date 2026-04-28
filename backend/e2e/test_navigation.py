"""E2E: Navigation between views."""
import pytest
from playwright.sync_api import expect


def test_sidebar_switches_views(logged_in_page):
    """Clicking Dashboard then Import Batches should switch views."""
    page = logged_in_page

    # Default is Import Batches
    assert page.locator(".uploader-container").is_visible()

    # Switch to Dashboard
    page.locator("button.sidebar-nav-item").filter(has_text="Dashboard").click(force=True)
    page.wait_for_selector(".dashboard-view", timeout=10000)
    assert page.locator(".dashboard-view").is_visible()

    # Switch back
    page.locator("button.sidebar-nav-item").filter(has_text="Import Batches").click(force=True)
    page.wait_for_selector(".uploader-container", timeout=10000)
    assert page.locator(".uploader-container").is_visible()
