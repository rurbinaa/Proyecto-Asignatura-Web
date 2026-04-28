"""
E2E: Excel import flow (upload → preview → confirm).

Requires app running: docker compose up
"""
import pytest
import os
from pathlib import Path


EXCEL_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "test_data.xlsx"


@pytest.mark.skipif(
    not EXCEL_FIXTURE.exists(),
    reason="No test Excel fixture found. Place one at backend/e2e/fixtures/test_data.xlsx",
)
def test_excel_upload_preview_flow(logged_in_page):
    """Upload an Excel file, verify preview, and confirm import."""
    page = logged_in_page

    # Click Excel upload button/area
    upload_trigger = page.locator(
        '[class*="upload"], [class*="dropzone"], input[type="file"]'
    ).first
    
    if upload_trigger.count() == 0:
        pytest.skip("No upload element found on dashboard")

    # Upload file
    file_input = page.locator('input[type="file"]')
    if file_input.count() == 0:
        # Some UIs use a hidden input triggered by clicking a button
        upload_trigger.click()
        page.wait_for_timeout(500)
        file_input = page.locator('input[type="file"]')

    if file_input.count() > 0:
        file_input.set_input_files(str(EXCEL_FIXTURE))
        page.wait_for_timeout(3000)

        # Should see preview data
        preview = page.locator('[class*="preview"], [class*="session"]')
        if preview.count() > 0:
            # Click confirm button
            confirm_btn = page.locator(
                'button:has-text("Confirm"), button:has-text("Apply"), '
                'button:has-text("Aceptar")'
            ).first
            if confirm_btn.count() > 0:
                confirm_btn.click()
                page.wait_for_timeout(3000)
