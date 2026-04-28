"""
Mock infrastructure for E2E Playwright tests.

Each module provides factory functions that register ``page.route()``
interceptors for a specific API domain. The ``mock_all()`` shorthand
registers all happy-path routes at once.
"""

from .auth import mock_auth_success, mock_auth_failure
from .kpis import (
    mock_kpi_data,
    mock_kpi_empty,
    mock_volatile_kpis,
    mock_volatile_empty,
)
from .excel import (
    mock_excel_preview,
    mock_excel_confirm,
    mock_excel_reject,
    mock_excel_analyze_error,
    mock_excel_confirm_error,
)


def mock_all(page):
    """Register all happy-path API route interceptors.

    This is a convenience shorthand that sets up every domain with
    realistic success responses. Covers auth, KPIs, and Excel endpoints.
    """
    mock_auth_success(page)
    mock_kpi_data(page)
    mock_excel_preview(page)
    mock_excel_confirm(page)
    mock_excel_reject(page)


__all__ = [
    "mock_auth_success",
    "mock_auth_failure",
    "mock_kpi_data",
    "mock_kpi_empty",
    "mock_volatile_kpis",
    "mock_volatile_empty",
    "mock_excel_preview",
    "mock_excel_confirm",
    "mock_excel_reject",
    "mock_excel_analyze_error",
    "mock_excel_confirm_error",
    "mock_all",
]
