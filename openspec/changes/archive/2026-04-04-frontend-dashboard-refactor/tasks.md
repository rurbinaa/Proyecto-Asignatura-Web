# frontend-dashboard-refactor Tasks

## Phase 1: Extract Chart Transform Functions

- [x] 1.1 Create `frontend/src/utils/chartTransforms.js` with 13 pure transformation functions
- [x] 1.2 Move 6 formatter functions to chartTransforms.js
- [x] 1.3 Move 2 helper functions (parseLineStateLabel, buildLineCountDataByState) to chartTransforms.js
- [x] 1.4 Update DashboardView.jsx to import from chartTransforms.js
- [x] 1.5 Run lint and tests to verify no broken references

## Summary

All extracted functions:
- **13 transforms**: transformPassReject, transformAqlByStyle, transformAqlWeekly, transformAuditedPieces, transformRejectedEvolution, transformAcReRateByLine, transformPerformanceByCustomer, transformPerformanceByLine, transformTopDefects, transformFabricDefects, transformContainersByState, transformDefectsByStyleType, transformSecondsRework
- **6 formatters**: formatPercent, formatPieces, formatCount, formatSeconds, formatWeekLabel, formatAcceptanceIndex, trimCategoryLabel
- **2 helpers**: parseLineStateLabel, buildLineCountDataByState

**Status**: ✅ Phase 1 complete - all functions extracted and verified.
