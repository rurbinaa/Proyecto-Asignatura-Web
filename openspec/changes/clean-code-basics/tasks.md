# Tasks: Clean Code Basics

## Phase 1: Backend Cleanup

- [x] 1.1 Execute `ruff check --fix .` in `backend/` to apply automated lint fixes.
- [x] 1.2 Verify backend remains functional and lint output is clean.

## Phase 2: Frontend Dead Code Removal

- [x] 2.1 Remove unused imports and variables in `frontend/src/App.jsx`.
- [x] 2.2 Remove unused imports and variables in `frontend/src/Components/ExcelUploader.jsx`.
- [x] 2.3 Remove unused imports and variables in `frontend/src/utils/kpiCalculations.js`.
- [x] 2.4 Cleanup unused imports and variables in `frontend/src/views/DashboardView.test.jsx`, `frontend/src/Components/ExcelUploader.test.jsx`, and other affected test files.

## Phase 3: React Hooks Fixes

- [x] 3.1 Update `useCallback` dependency array in `frontend/src/views/DashboardView.jsx` to include `filters`.
- [x] 3.2 Refactor `frontend/src/Components/DefectPopover.jsx` to eliminate `setState` inside `useEffect` that causes cascaded renders.
- [x] 3.3 Verify `DefectPopover.jsx` initial render timing and state behavior matches existing UI requirements without React warnings.

## Phase 4: Final Verification

- [x] 4.1 Run `npm run lint` (or equivalent) in `frontend/` to ensure zero warnings for the targeted files.
- [x] 4.2 Verify frontend application loads and components render without console warnings or runtime errors. (Tests pass: 115 passed, 4 skipped; lint passes)

(End of file - total 24 lines)
