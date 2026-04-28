"""
E2E: Excel import flow.

Tests the full upload → analyze → preview → confirm → success/cancel/error
state machine. Zero backend dependency — all API calls are mocked
via page.route().

State transitions: idle → analyzing → preview_ready → confirming → success + error.
We wait only for FINAL states (preview_ready, success, error) since React 18
automatic batching may skip rendering intermediate states.
"""
import pytest
from playwright.sync_api import expect
from e2e.mocks.excel import (
    mock_excel_preview,
    mock_excel_confirm,
    mock_excel_reject,
    mock_excel_analyze_error,
    mock_excel_confirm_error,
)


def _navigate_to_excel(page):
    """Navigate to the Import Batches view via sidebar."""
    page.locator("button.sidebar-nav-item").filter(has_text="Import Batches").click()
    page.wait_for_selector(".uploader-container", timeout=10000)


def _upload_file(page, test_excel_file):
    """Upload the test Excel file via the dropzone's hidden input."""
    file_input = page.locator(".dropzone input[type='file']")
    file_input.set_input_files(str(test_excel_file))
    # File preview should appear
    page.wait_for_selector(".file-preview", timeout=5000)


def test_full_happy_path(logged_in_page, test_excel_file):
    """Upload → analyze → preview → confirm → success.

    Covers all 5 states: idle → analyzing → preview_ready → confirming → success.
    We assert only idle, preview_ready, and success (final rendered states).
    """
    page = logged_in_page
    mock_excel_preview(page)
    mock_excel_confirm(page)

    _navigate_to_excel(page)

    # IDLE state: dropzone visible
    assert page.locator(".dropzone").is_visible()

    # Select file
    _upload_file(page, test_excel_file)

    # Click Analyze File → transitions to analyzing → preview_ready
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()

    # Wait for PREVIEW_READY state: backend stats appear
    page.wait_for_selector(".backend-stats-container", timeout=10000)
    assert page.locator(".backend-stats-container").is_visible()

    # Click Confirm & Import → transitions to confirming → success
    page.locator("button.ingesta-btn-primary").filter(has_text="Confirm & Import").click()

    # Wait for SUCCESS state
    page.wait_for_selector(".success-panel", timeout=10000)
    assert page.locator(".success-panel").is_visible()

    # "Upload Another File" button should exist
    upload_again = page.locator("button.ingesta-btn-outline").filter(
        has_text="Upload Another File"
    )
    expect(upload_again).to_be_visible()


def test_cancel_import(logged_in_page, test_excel_file):
    """Cancel import during preview should return to idle dropzone."""
    page = logged_in_page
    mock_excel_preview(page)
    mock_excel_reject(page)

    _navigate_to_excel(page)

    # Upload and analyze → preview_ready
    _upload_file(page, test_excel_file)
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()
    page.wait_for_selector(".backend-stats-container", timeout=10000)

    # Click Cancel Import
    page.locator("button.ingesta-btn-outline").filter(has_text="Cancel Import").click()

    # Should return to idle: dropzone visible, backend stats gone
    page.wait_for_selector(".dropzone", timeout=10000)
    assert page.locator(".dropzone").is_visible()
    assert page.locator(".backend-stats-container").count() == 0


def test_confirm_error(logged_in_page, test_excel_file):
    """Confirm failure should show error panel with Try Again."""
    page = logged_in_page
    mock_excel_preview(page)
    mock_excel_confirm_error(page)

    _navigate_to_excel(page)

    # Upload and analyze → preview_ready
    _upload_file(page, test_excel_file)
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()
    page.wait_for_selector(".backend-stats-container", timeout=10000)

    # Click Confirm & Import → will fail → error state
    page.locator("button.ingesta-btn-primary").filter(has_text="Confirm & Import").click()

    # Wait for ERROR state
    page.wait_for_selector(".error-panel", timeout=10000)
    assert page.locator(".error-panel").is_visible()

    # Try Again button should exist
    try_again = page.locator("button.ingesta-btn-outline").filter(has_text="Try Again")
    expect(try_again).to_be_visible()


def test_backend_stats_rendered(logged_in_page, test_excel_file):
    """Backend stats should show numerical values after preview."""
    page = logged_in_page
    mock_excel_preview(page)

    _navigate_to_excel(page)

    # Upload and analyze → preview_ready
    _upload_file(page, test_excel_file)
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()
    page.wait_for_selector(".backend-stats-container", timeout=10000)

    # Check that stats contain numerical values
    stats = page.locator(".backend-stats-container")
    assert stats.is_visible()

    # Each backend-stat-card should have a "Total:" with a number
    total_elements = page.locator(".backend-stat-total strong")
    assert total_elements.count() > 0

    # Check that at least one total value is a positive integer
    for i in range(total_elements.count()):
        text = total_elements.nth(i).text_content()
        if text and text.strip().isdigit():
            assert int(text.strip()) > 0
            break
    else:
        pytest.fail("No positive numeric total found in backend stats")


def test_file_removal(logged_in_page, test_excel_file):
    """Clearing the selected file should return to idle dropzone."""
    page = logged_in_page

    _navigate_to_excel(page)

    # Select file
    _upload_file(page, test_excel_file)

    # File preview should be visible
    assert page.locator(".file-preview").is_visible()

    # Click the clear button
    page.locator("button.clear-btn").click()

    # File preview should be gone, dropzone should be visible
    assert page.locator(".file-preview").count() == 0
    assert page.locator(".dropzone").is_visible()
