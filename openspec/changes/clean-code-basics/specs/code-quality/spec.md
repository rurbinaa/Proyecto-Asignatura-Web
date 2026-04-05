# Delta for Code Quality

## ADDED Requirements

### Requirement: Lint Compliance

The codebase MUST maintain zero lint warnings and errors across both backend and frontend layers to ensure maintainability and reduce technical debt.

#### Scenario: Backend Python lint cleanup

- GIVEN the backend codebase at `backend/`
- WHEN `ruff check --fix .` is executed
- THEN all auto-fixable lint issues are resolved
- AND the remaining lint output is clean or contains only intentionally suppressed violations

#### Scenario: Frontend dead code removal

- GIVEN frontend source files with identified unused imports and variables
- WHEN dead code removal is applied
- THEN all unused imports and variables are removed from `App.jsx`, `ExcelUploader.jsx`, `kpiCalculations.js`, and affected tests
- AND ESLint no longer reports unused symbol warnings for these files

### Requirement: React Hooks Correctness

Components using React hooks MUST conform to the Rules of Hooks to prevent runtime bugs and rendering issues.

#### Scenario: useCallback dependency completeness

- GIVEN `DashboardView.jsx` with a `useCallback` that references `filters`
- WHEN the hook dependency array is reviewed
- THEN `filters` is included in the dependency array
- AND the React Developer Tools shows no dependency warnings

#### Scenario: useEffect state update isolation

- GIVEN `DefectPopover.jsx` with state updates inside `useEffect`
- WHEN the component renders initially
- THEN the state update does not trigger a cascaded re-render within the same render cycle
- AND the browser console shows no React warnings about state updates during render

## MODIFIED Requirements

None

## REMOVED Requirements

None