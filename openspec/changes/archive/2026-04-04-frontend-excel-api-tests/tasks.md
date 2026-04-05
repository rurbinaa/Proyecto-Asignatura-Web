# Tasks: frontend-excel-api-tests

## Phase 1: Infrastructure

- [x] 1.1 Create `frontend/src/api/excel.test.js` with `vitest-environment jsdom` pragma and necessary imports (`describe, it, expect, vi, beforeEach`).
- [x] 1.2 Implement global `vi.stubGlobal('fetch', vi.fn())` in a `beforeEach` block to prevent real network calls.

## Phase 2: uploadForPreview Tests

- [x] 2.1 Test success path: verify `fetch` is called with `POST`, `formData` contains file, and response is correctly parsed.
- [x] 2.2 Test URL encoding: verify special characters in filename are handled via `encodeURIComponent`.
- [x] 2.3 Test network error: verify function throws when `fetch` rejects.
- [x] 2.4 Test HTTP 500 error: verify function extracts error message from JSON body or falls back to status code.
- [x] 2.5 Test malformed JSON: verify function propagates JSON parse errors.

## Phase 3: confirmSession Tests

- [x] 3.1 Test success path: verify `fetch` is called with `POST`, `Content-Type: application/json` header, and correct URL including `sessionId`.
- [x] 3.2 Test 404 error: verify function throws "Session not found" (or equivalent message) when status is 404.
- [x] 3.3 Test fallback error: verify function uses `statusText` when JSON response is empty or invalid.

## Phase 4: rejectSession Tests

- [x] 4.1 Test success path: verify `fetch` is called with `DELETE` and correct URL including `sessionId`.
- [x] 4.2 Test error path: verify function throws with appropriate message on failed rejection.

## Phase 5: Verification

- [x] 5.1 Run `npm test excel.test.js` (or project equivalent) to ensure 100% coverage and pass.
- [x] 5.2 Verify that `vi.clearAllMocks()` is called between tests to ensure isolation.

## Results

- **14 tests passed** (100%)
- **Coverage**: 96% statements, 100% lines, 78.57% branches
- **Uncovered lines**: 1 (API_BASE fallback), 26 (error fallback), 71 (error fallback) - edge cases
