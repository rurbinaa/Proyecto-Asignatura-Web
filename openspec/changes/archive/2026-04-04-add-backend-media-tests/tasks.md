# Tasks: add-backend-media-tests

## Phase 1: Inspection Bridge Unit Tests

- [x] 1.1 Bridge rejects unclosed inspection — `test_bridge_raises_on_open_inspection`
- [x] 1.2 Bridge handles no matching QC records — `test_bridge_no_match_returns_no_match_status`
- [x] 1.3 Bridge syncs single QC record with defects — `test_bridge_syncs_single_qc_record_with_defects`
- [x] 1.4 Bridge syncs multiple QC records for same style/color — `test_bridge_syncs_multiple_qc_records`
- [x] 1.5 Defect aggregation counts by type name — `test_aggregate_defects_sums_by_type`
- [x] 1.6 InspectionDefect sync creates through-table records — `test_sync_defect_types_creates_records` + `test_sync_defect_types_deletes_existing_before_creating`
- [x] 1.7 InspectionDefect sync skips inactive defect types — `test_sync_skips_inactive_defect_types`

## Phase 2: Close Inspection Endpoint Tests

- [x] 2.1 Close rejects already-closed inspection — `test_close_already_closed_returns_400`
- [x] 2.2 Close inspection with defects sets REJECT status — `test_close_with_defects_returns_reject` + `test_close_with_defects_includes_bridge_result`
- [x] 2.3 Close inspection without defects sets PASS status — `test_close_without_defects_returns_pass` + `test_close_without_defects_includes_bridge_result`
- [x] 2.4 Close returns bridge synchronization result — `test_close_includes_bridge_result_keys` + `test_close_bridges_to_correct_qc_record`

## Phase 3: Edge Case Coverage

- [x] 3.1 Zero defects produces PASS and zero totals — `test_zero_defects_produces_pass_and_zero_totals`
- [x] 3.2 Sample smaller than defect count handles gracefully — `test_sample_smaller_than_defect_count_handles_gracefully`
- [x] 3.3 Null defect_type is excluded from aggregation — `test_null_defect_type_excluded_from_aggregation`

## Additional (Out of Scope)

- [x] Undo defect endpoint tests — `UndoDefectTest` class (bonus coverage)
