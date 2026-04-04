# Tasks: Complete Backend Test Coverage

## Phase 1: Excel Importer Service Tests

- [x] 1.1 Add `test_load_and_clean_corrupted_file` to `excel_importer/tests/test_handler_service.py` to verify exception handling for non-Excel files.
- [x] 1.2 Add `test_load_and_clean_invalid_extension` to verify `ValueError`/`BadZipFile` on `.pdf`/`.csv`.
- [x] 1.3 Add `test_load_and_clean_missing_columns` to verify default value injection for missing remapped columns.
- [x] 1.4 Add `test_load_and_clean_empty_file` to verify empty DataFrame return instead of crash.
- [x] 1.5 Add `test_normalize_defects_fields_null_input` to verify it returns `[]` when input is `None` or `0`.
- [x] 1.6 Add `test_truncate_charfields_limits` to verify strings are truncated to model `max_length`.

## Phase 2: VolatileKpiView Edge Case Tests

- [x] 2.1 Create `quality_data/tests/test_volatile_kpis.py` with `VolatileKpiViewTest` class.
- [x] 2.2 Add `test_volatile_post_missing_file` to verify 400 response when no file is provided.
- [x] 2.3 Add `test_volatile_post_empty_dataframe` to verify empty KPI arrays and zero defect rate.
- [x] 2.4 Add `test_volatile_zero_division_safety` to verify `_calc_aql_by_style` and `_calc_defect_rate` handle `sample=0` without crashing.
- [x] 2.5 Add `test_volatile_trend_single_point` to verify `_calc_aql_weekly` trend calculation with 1 data point.
- [x] 2.6 Add `test_volatile_filter_options_missing_columns` to verify `_compute_filter_options` returns empty arrays for missing fields.
- [x] 2.7 Add `test_volatile_parser_exception_resilience` to verify `VolatileKpiView.post` returns `null` for individual KPIs if their specific parsers fail.

## Phase 3: Infrastructure and Isolation

- [x] 3.1 Create `backend/conftest.py` (if not exists) or add shared `excel_file_factory` fixture using `io.BytesIO` and `pandas.to_excel`.
- [x] 3.2 Verify all new tests in Phase 1 and 2 use in-memory files and do not persist data to the real DB (except for necessary setup fixtures).

## Phase 4: Verification

- [x] 4.1 Run `pytest backend/excel_importer/tests/test_handler_service.py` and verify 100% pass.
- [x] 4.2 Run `pytest backend/quality_data/tests/test_volatile_kpis.py` and verify 100% pass.
- [x] 4.3 Check coverage report for `excel_importer/handler_service.py` and `quality_data/views.py` (specifically `VolatileKpiView`).
