# Proposal: Frontend Dashboard Refactor

## Intent

Reduce `DashboardView.jsx` size and improve separation of concerns by moving pure chart/data transformation logic out of the view layer. This makes the dashboard easier to read, test, and evolve without mixing rendering with data shaping.

## Scope

### In Scope
- Extract all pure data transformation helpers from `frontend/src/views/DashboardView.jsx` into `frontend/src/utils/chartTransforms.js`.
- Include functions like `transformPassReject`, `transformAqlByStyle`, `transformAqlWeekly`, and similar chart-oriented transforms.
- Update `DashboardView.jsx` to import and use the shared utility module.

### Out of Scope
- UI redesign or chart behavior changes.
- Data source, API, or backend contract changes.
- Non-pure logic that belongs to the view component lifecycle.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- None

## Approach

- Identify all deterministic transformation helpers currently embedded in `DashboardView.jsx`.
- Move them into `frontend/src/utils/chartTransforms.js` with stable named exports.
- Keep `DashboardView.jsx` focused on fetching, state, and composition.
- Preserve existing inputs/outputs so the refactor is behavior-preserving.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/views/DashboardView.jsx` | Modified | Remove pure transform helpers and import shared utilities. |
| `frontend/src/utils/chartTransforms.js` | New | Centralize dashboard chart/data transformation functions. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A transform is missed and the view still contains duplicated logic | Medium | Audit for all pure helpers and move them together in one pass. |
| Import paths or export names break the dashboard | Low | Keep function names stable and verify usage after extraction. |

## Rollback Plan

If the refactor causes regressions, revert `DashboardView.jsx` and delete `frontend/src/utils/chartTransforms.js`, restoring the original in-file helpers.

## Dependencies

- No external dependencies.
- Frontend-only change; no Docker/container impact expected.

## Success Criteria

- [ ] All pure dashboard transform helpers live in `frontend/src/utils/chartTransforms.js`.
- [ ] `DashboardView.jsx` imports the helpers and no longer contains chart transformation logic.
- [ ] Dashboard behavior remains unchanged after the refactor.
