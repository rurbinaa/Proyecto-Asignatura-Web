# Specification: frontend-api-excel

## Purpose

Define test coverage requirements for `frontend/src/api/excel.js`, covering upload/confirm/reject operations with deterministic, mocked `fetch` behavior.

## Requirements

### Requirement: uploadForPreview Success Path

The test suite MUST verify that `uploadForPreview(file)` correctly constructs the FormData request and returns the expected response shape.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Success with valid file | A File object with `.xlsx` extension | `uploadForPreview(file)` is called with mocked `fetch` returning `{ok: true, json: {session_id: 1, status: 'pending', preview: {...}, warnings: []}}` | Returns the parsed JSON response with `session_id`, `status`, `preview`, `warnings` |
| URL encodes filename | A File object with special characters in name (e.g., `file (1).xlsx`) | `uploadForPreview(file)` is called | Fetch URL contains `encodeURIComponent(filename)` |
| FormData contains file | A File object | `uploadForPreview(file)` is called | FormData has `file` field containing the File object |
| POST method used | Any File | `uploadForPreview(file)` is called | `fetch` called with `method: 'POST'` |

### Requirement: uploadForPreview Error Paths

The test suite MUST verify error handling for network failures, HTTP errors, and malformed responses.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Network error | `fetch` throws a network error (e.g., `TypeError: Failed to fetch`) | `uploadForPreview(file)` is called | Throws error with network failure message |
| HTTP 500 with JSON body | `fetch` returns `{ok: false, status: 500, json: {error: 'Internal Server Error'}}` | `uploadForPreview(file)` is called | Throws `Error` with message `'Internal Server Error'` |
| HTTP 500 with text body | `fetch` returns `{ok: false, status: 500, json: throws, statusText: 'Internal Server Error'}` | `uploadForPreview(file)` is called | Throws `Error` with message containing `500` |
| HTTP 400 bad request | `fetch` returns `{ok: false, status: 400, json: {error: 'Invalid file format'}}` | `uploadForPreview(file)` is called | Throws `Error` with message `'Invalid file format'` |
| Malformed JSON response | `fetch` returns `{ok: true, json: throws SyntaxError}` | `uploadForPreview(file)` is called | Throws error (JSON parse failure propagates) |
| Response missing session_id | `fetch` returns `{ok: true, json: {status: 'pending'}}` | `uploadForPreview(file)` is called | Returns incomplete response (caller handles undefined) |

### Requirement: confirmSession Success Path

The test suite MUST verify that `confirmSession(sessionId)` sends the correct POST request and returns the confirmation response.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Confirm success | A valid `sessionId` | `confirmSession(sessionId)` with mocked `fetch` returning `{ok: true, json: {session_id: 1, status: 'confirmed', message: '...'}}` | Returns response with `session_id`, `status`, `message` |
| URL includes sessionId | `sessionId` is `42` | `confirmSession(42)` called | Fetch URL contains `/confirm/42/` |
| JSON content-type header | Any valid sessionId | `confirmSession(sessionId)` called | Request includes `Content-Type: application/json` |

### Requirement: confirmSession Error Paths

The test suite MUST verify error handling for confirmation failures.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| HTTP 404 session not found | `fetch` returns `{ok: false, status: 404, json: {error: 'Session not found'}}` | `confirmSession(999)` called | Throws `Error` with message `'Session not found'` |
| HTTP 500 server error | `fetch` returns `{ok: false, status: 500, statusText: 'Internal Server Error'}` | `confirmSession(1)` called | Throws `Error` with message containing `500` |
| Malformed JSON error | `fetch` returns `{ok: false, status: 500}` and `json()` throws | `confirmSession(1)` called | Throws `Error` with `statusText` fallback |

### Requirement: rejectSession Success Path

The test suite MUST verify that `rejectSession(sessionId)` sends the correct DELETE request and returns the rejection response.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Reject success | A valid `sessionId` | `rejectSession(sessionId)` with mocked `fetch` returning `{ok: true, json: {session_id: 1, status: 'rejected', message: '...'}}` | Returns response with `session_id`, `status`, `message` |
| URL includes sessionId | `sessionId` is `42` | `rejectSession(42)` called | Fetch URL contains `/reject/42/` |
| DELETE method used | Any valid sessionId | `rejectSession(sessionId)` called | `fetch` called with `method: 'DELETE'` |

### Requirement: rejectSession Error Paths

The test suite MUST verify error handling for rejection failures.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| HTTP 404 session not found | `fetch` returns `{ok: false, status: 404, json: {error: 'Session not found'}}` | `rejectSession(999)` called | Throws `Error` with message `'Session not found'` |
| HTTP 500 server error | `fetch` returns `{ok: false, status: 500, statusText: 'Internal Server Error'}` | `rejectSession(1)` called | Throws `Error` with message containing `500` |

### Requirement: Fetch Mocking Isolation

The test suite MUST ensure complete isolation from network and proper mock restoration.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| Mock cleared per test | Multiple tests run sequentially | Each test completes | `beforeEach` clears all mocks with `vi.clearAllMocks()` |
| Mock restored after suite | All tests complete | Suite finishes | No leakage to other test files |
| FormData not mocked | `uploadForPreview` test | File passed to FormData | Browser FormData API used (not mocked) |

### Requirement: Test Organization

The test file MUST follow existing project conventions.

| Scenario | Given | When | Then |
|----------|-------|------|------|
| File location | `frontend/src/api/excel.js` exists | Test file created | Located at `frontend/src/api/excel.test.js` |
| Environment pragma | Test file created | File inspected | First line is `/** @vitest-environment jsdom */` |
| Imports follow pattern | Test file created | File inspected | Imports `describe, it, expect, vi, beforeEach` from `vitest` |
| Tests grouped by function | Test file created | File inspected | Three `describe` blocks: one per exported function |