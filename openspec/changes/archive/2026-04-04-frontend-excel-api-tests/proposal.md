# Proposal: frontend-excel-api-tests

## Intent

Raise confidence in `frontend/src/api/excel.js`, which is currently at 4% coverage, by covering the upload flow and failure handling around `fetch`.

## Scope

### In Scope
- Add Vitest unit tests for successful Excel file upload.
- Add coverage for network errors, 500 server responses, and malformed responses.
- Mock `fetch` and validate returned errors/data shape.

### Out of Scope
- No production code changes unless tests expose a real bug.
- No backend/API contract changes.
- No Docker/container updates.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None.

## Approach

- Create/extend `frontend/src/api/excel.test.js` (or matching test file) using Vitest.
- Mock `global.fetch` for success and failure branches.
- Assert upload request composition, error propagation, and malformed payload handling.
- Keep tests isolated from network and filesystem.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/api/excel.js` | Modified | Behavior verified through unit tests; code only changes if defects are found |
| `frontend/src/api/excel.test.js` | New/Modified | Coverage for upload, network, 500, and malformed-response scenarios |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tests encode assumptions about response format | Medium | Match assertions to actual API behavior and keep malformed cases explicit |
| Flaky fetch mocking | Low | Stub `fetch` per test and restore mocks after each case |

## Rollback Plan

Remove the new/updated test file and revert any incidental production code edits. No data or deployment rollback is needed.

## Dependencies

- Vitest available in the frontend workspace.

## Success Criteria

- [ ] Upload success, network error, 500 error, and malformed response cases are covered.
- [ ] `frontend/src/api/excel.js` coverage increases materially from 4%.
- [ ] Tests run deterministically with mocked `fetch` only.
