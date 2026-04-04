# Proposal: Clean Code Basics

## Intent

Reduce low-value lint noise and eliminate a pair of React hook issues so the codebase is easier to maintain and safer to evolve.

## Scope

### In Scope
- Run `ruff check --fix .` in `backend/` to apply safe Python cleanup.
- Remove dead imports/variables in frontend files: `App.jsx`, `ExcelUploader.jsx`, `kpiCalculations.js`, and affected tests.
- Fix React Hooks warnings in `DashboardView.jsx` and `DefectPopover.jsx`.

### Out of Scope
- Behavioral refactors or feature changes.
- API contract changes.
- Large stylistic rewrites beyond lint-driven cleanup.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- None

## Approach

- Apply automated backend cleanup first with Ruff auto-fixes.
- Manually remove unused frontend symbols where the linter reports dead code.
- Update `DashboardView.jsx` to include `filters` in the `useCallback` dependency array.
- Refactor `DefectPopover.jsx` to avoid cascaded renders caused by `setState` inside `useEffect`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/` | Modified | Ruff-driven Python cleanup across the backend. |
| `frontend/src/App.jsx` | Modified | Remove dead imports/variables. |
| `frontend/src/components/ExcelUploader.jsx` | Modified | Remove dead imports/variables. |
| `frontend/src/utils/kpiCalculations.js` | Modified | Remove dead imports/variables. |
| `frontend/src/views/DashboardView.jsx` | Modified | Fix `useCallback` dependency warning. |
| `frontend/src/components/DefectPopover.jsx` | Modified | Fix render cascade from `setState` in `useEffect`. |
| `frontend/tests/` | Modified | Remove dead imports/variables in tests. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Ruff auto-fix changes code beyond the intended cleanup | Low | Review diff and keep changes limited to safe lint fixes. |
| Hook dependency fix changes memoization behavior | Medium | Make the dependency update explicit and verify the component still renders correctly. |
| DefectPopover state refactor alters initial render timing | Medium | Keep the fix minimal and preserve existing UI behavior. |

## Rollback Plan

Revert the proposal’s follow-up implementation commit(s) if lint cleanup or hook fixes introduce regressions. Because this change is non-functional, rollback is limited to restoring the previous file versions.

## Dependencies

- Existing ESLint/Ruff rules must remain the source of truth for cleanup.
- Frontend and backend work can proceed independently.

## Success Criteria

- [ ] `ruff check --fix .` completes cleanly in `backend/`.
- [ ] Frontend lint warnings for dead imports/variables are removed in the listed files.
- [ ] `DashboardView.jsx` no longer warns about the missing `filters` dependency.
- [ ] `DefectPopover.jsx` no longer triggers cascaded render warnings from `useEffect` state updates.
