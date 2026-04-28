"""
Mock Excel import API route handlers for E2E tests.

Provides factories that register page.route() interceptors for:
POST /quality/excel/preview/{filename}/
POST /quality/excel/confirm/{sessionId}/
DELETE /quality/excel/reject/{sessionId}/
"""

import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "http://localhost:5173",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
}

PREVIEW_RESPONSE = {
    "session_id": 42,
    "status": "preview_ready",
    "preview": {
        "QC FA Plant": {
            "new": 10,
            "modified": 2,
            "unchanged": 1,
            "warnings": 0,
            "total": 13,
        },
        "QC FA Customer": {
            "new": 5,
            "modified": 0,
            "unchanged": 0,
            "warnings": 0,
            "total": 5,
        },
        "SecondsA4": {
            "new": 3,
            "modified": 1,
            "unchanged": 0,
            "warnings": 0,
            "total": 4,
        },
        "Seconds General": {
            "new": 2,
            "modified": 0,
            "unchanged": 1,
            "warnings": 0,
            "total": 3,
        },
        "Container": {
            "new": 8,
            "modified": 0,
            "unchanged": 0,
            "warnings": 1,
            "total": 8,
        },
    },
    "warnings": [],
}

CONFIRM_RESPONSE = {
    "session_id": 42,
    "status": "success",
    "message": "Import completed successfully. 28 records processed.",
}

REJECT_RESPONSE = {
    "session_id": 42,
    "status": "cancelled",
    "message": "Import cancelled. No changes applied.",
}


def _handle_options(route):
    route.fulfill(status=200, headers=CORS_HEADERS)


def _excel_handler_generator(responses):
    """Generate a route handler for Excel endpoints with given response map.

    Args:
        responses: dict mapping URL substring -> (status_code, response_body_dict)
    """
    def handler(route):
        if route.request.method == "OPTIONS":
            _handle_options(route)
            return

        url = route.request.url
        for pattern, (status, body) in responses.items():
            if pattern in url:
                route.fulfill(
                    status=status,
                    content_type="application/json",
                    headers=CORS_HEADERS,
                    body=json.dumps(body),
                )
                return

        route.fulfill(status=404, headers=CORS_HEADERS)

    return handler


# ── Route handlers for individual scenarios ──────────────────────────────────

def _preview_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps(PREVIEW_RESPONSE),
    )


def _confirm_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps(CONFIRM_RESPONSE),
    )


def _reject_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    route.fulfill(
        status=200,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps(REJECT_RESPONSE),
    )


def _confirm_error_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    route.fulfill(
        status=500,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps({"error": "Internal server error during confirm."}),
    )


def _analyze_error_handler(route):
    if route.request.method == "OPTIONS":
        _handle_options(route)
        return
    route.fulfill(
        status=500,
        content_type="application/json",
        headers=CORS_HEADERS,
        body=json.dumps({"error": "File processing failed. Invalid format."}),
    )


def mock_excel_preview(page):
    """Register Excel preview route interceptor.

    Intercepts POST /quality/excel/preview/{filename}/ → 200 + preview data.
    """
    page.route("**/quality/excel/preview/**", _preview_handler)


def mock_excel_confirm(page):
    """Register Excel confirm route interceptor.

    Intercepts POST /quality/excel/confirm/{sessionId}/ → 200 + success.
    """
    page.route("**/quality/excel/confirm/**", _confirm_handler)


def mock_excel_reject(page):
    """Register Excel reject route interceptor.

    Intercepts DELETE /quality/excel/reject/{sessionId}/ → 200 + cancelled.
    """
    page.route("**/quality/excel/reject/**", _reject_handler)


def mock_excel_analyze_error(page):
    """Register Excel preview route that returns a 500 error.

    Intercepts POST /quality/excel/preview/{filename}/ → 500.
    """
    page.route("**/quality/excel/preview/**", _analyze_error_handler)


def mock_excel_confirm_error(page):
    """Register Excel confirm route that returns a 500 error.

    Intercepts POST /quality/excel/confirm/{sessionId}/ → 500.
    """
    page.route("**/quality/excel/confirm/**", _confirm_error_handler)
