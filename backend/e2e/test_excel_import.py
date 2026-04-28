"""E2E: Excel import flow against real backend.

Requires: backend/e2e/fixtures/test_data.xlsx (place a real Excel file here)
"""
import pytest
from pathlib import Path


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "test_data.xlsx"


@pytest.mark.skipif(not FIXTURE.exists(), reason="No test_data.xlsx in e2e/fixtures/")
def test_excel_upload_and_preview(logged_in_page):
    """Upload Excel, see preview, cancel."""
    page = logged_in_page

    # Upload file
    file_input = page.locator(".dropzone input[type='file']")
    file_input.set_input_files(str(FIXTURE))
    page.wait_for_selector(".file-preview", timeout=5000)

    # Analyze
    page.locator("button.ingesta-btn-primary").filter(has_text="Analyze File").click()
    page.wait_for_selector(".backend-stats-container", timeout=30000)

    # Cancel
    page.locator("button:has-text('Cancel Import')").click()
    page.wait_for_selector(".dropzone", timeout=5000)
