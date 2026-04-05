# Proposal: Complete Backend Tests

## Intent

Close the remaining backend coverage gaps so the test suite better protects critical import and KPI logic. This change targets the highest-risk untested paths in Excel ingestion and volatile KPI calculations without changing runtime behavior.

## Scope

### In Scope
- Add tests for `excel_importer/handler_service.py` covering upload handling, corrupted files, invalid formats, missing columns, and file-reading exceptions.
- Add tests for `quality_data/views.py` covering `VolatileKpiView` and real-time KPI calculations using data processing only.
- Validate error handling and edge cases around bad input, not persistence behavior.

### Out of Scope
- Any production code refactor beyond minimal testability helpers, if needed.
- Database schema, API contract, or frontend changes.
- Broader coverage work outside the two named backend modules.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None.

## Approach

- Build focused pytest coverage around the existing public entry points.
- Use fixtures/mocks to simulate uploads, malformed Excel content, missing headers, and IO failures.
- Exercise `VolatileKpiView` with representative payloads and assert computed KPI outputs directly from processed data.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `excel_importer/handler_service.py` | Modified | Add tests for upload, parsing, and exception paths |
| `quality_data/views.py` | Modified | Add view-level tests for volatile KPI processing |
| `backend/tests/` or module test files | New/Modified | Add/extend pytest coverage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Test fixtures become brittle | Med | Keep fixtures small and align them with existing helpers |
| Hidden coupling requires minor test hooks | Low | Prefer mocks over production refactors |

## Rollback Plan

Remove the new/updated tests if they prove flaky or overly coupled. No production rollback is expected because the change is test-only.

## Dependencies

- Existing pytest-django test setup.
- Sample Excel fixtures or in-memory file mocks.

## Success Criteria

- [ ] The missing backend edge cases in both target modules are covered by automated tests.
- [ ] Backend coverage increases materially, especially in the two named files.
- [ ] Tests pass without changing application behavior.
