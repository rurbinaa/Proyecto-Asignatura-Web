"""
Mock KPI API route handlers for E2E tests.

Provides factories that register page.route() interceptors for all KPI endpoints:
GET /quality/kpis/* (filter-options, aql, rendimiento, etc.)
POST /quality/kpis/volatile/
"""

import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:5173",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
}

# ── Filter options ──────────────────────────────────────────────────────────

FILTER_OPTIONS_RESPONSE = {
    "week": [1, 2, 3, 4],
    "team": [1, 2, 3],
    "style": ["N3165", "N4165", "N5165"],
    "color": ["Red", "Blue", "Black", "White"],
    "customer": ["CUST_A", "CUST_B", "CUST_C"],
    "batch": [1, 2, 3],
}

# ── Generic KPI data ────────────────────────────────────────────────────────

KPI_DATA_RESPONSE = {
    "data": [
        {"style": "N3165", "aql": 2.5},
        {"style": "N4165", "aql": 1.8},
        {"style": "N5165", "aql": 3.2},
    ]
}

# ── Volatile KPIs (flat object with 14 KPI entries) ─────────────────────────

VOLATILE_KPIS_RESPONSE = {
    "aql_by_style": {"data": [{"style": "N3165", "aql": 2.5}]},
    "aql_weekly": {"data": [{"week": 1, "aql": 2.5}, {"week": 2, "aql": 1.8}]},
    "audited_pieces": {"data": [{"week": 1, "pieces": 400}, {"week": 2, "pieces": 350}]},
    "ac_re_rate_by_line": {"data": [{"line": "Team A", "pass": 90, "reject": 10}]},
    "seconds_rework": {"data": [{"week": 1, "seconds": 1200}]},
    "performance_by_customer": {"data": [{"customer": "CUST_A", "rate": 95.0}]},
    "performance_by_line": {"data": [{"line": "Team A", "rate": 92.0}]},
    "top_defects": {"data": [{"defect": "Sewing", "count": 15}]},
    "fabric_defects": {"data": [{"defect": "Hole", "count": 5}]},
    "defects_by_style_type": {"data": [{"style": "N3165", "type": "Sewing", "count": 8}]},
    "pass_reject_distribution": {"data": [{"status": "PASS", "count": 400}, {"status": "REJECT", "count": 50}]},
    "rejected_evolution": {"data": [{"week": 1, "rejected": 25}, {"week": 2, "rejected": 30}]},
    "containers_by_state": {"data": [{"state": "Approved", "count": 10}, {"state": "Pending", "count": 3}]},
    "defect_rate": {"value": 2.3},
}


def _handle_options(route):
    route.fulfill(status=200, headers=CORS_HEADERS)


def _kpi_handler(route):
    """Dispatch handler for all /quality/kpis/ requests."""
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return

    url = route.request.url
    method = route.request.method

    # Filter-options endpoint
    if "filter-options" in url and method == "GET":
        body = json.dumps(FILTER_OPTIONS_RESPONSE)
    # Volatile endpoint
    elif "volatile" in url and method == "POST":
        body = json.dumps(VOLATILE_KPIS_RESPONSE)
    # Any other GET KPI endpoint
    elif method == "GET":
        body = json.dumps(KPI_DATA_RESPONSE)
    else:
        route.fulfill(status=404, headers=CORS_HEADERS)
        return

    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def _kpi_empty_handler(route):
    """Dispatch handler returning empty data."""
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return

    url = route.request.url
    method = route.request.method

    if "filter-options" in url and method == "GET":
        body = json.dumps(FILTER_OPTIONS_RESPONSE)
    elif "volatile" in url and method == "POST":
        body = json.dumps({})
    elif method == "GET":
        body = json.dumps({"data": []})
    else:
        route.fulfill(status=404, headers=CORS_HEADERS)
        return

    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=body,
    )


def _volatile_kpis_handler(route):
    """Handler that only responds to POST /quality/kpis/volatile/."""
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return

    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps(VOLATILE_KPIS_RESPONSE),
    )


def _volatile_empty_handler(route):
    """Handler that returns empty object for volatile POST."""
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return

    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps({}),
    )


def mock_kpi_data(page):
    """Register KPI route interceptor returning standard data.

    Intercepts all GET/POST /quality/kpis/** and returns realistic DTOs.
    """
    page.route("**/quality/kpis/**", _kpi_handler)


def mock_kpi_empty(page):
    """Register KPI route interceptor returning empty data.

    Intercepts all GET/POST /quality/kpis/** and returns {"data": []}.
    """
    page.route("**/quality/kpis/**", _kpi_empty_handler)


def mock_volatile_kpis(page):
    """Register volatile KPI route interceptor returning full data.

    Intercepts POST /quality/kpis/volatile/ → 200 + 14 KPIs.
    """
    page.route("**/quality/kpis/volatile/", _volatile_kpis_handler)


def mock_volatile_empty(page):
    """Register volatile KPI route interceptor returning empty.

    Intercepts POST /quality/kpis/volatile/ → 200 + {}.
    """
    page.route("**/quality/kpis/volatile/", _volatile_empty_handler)
