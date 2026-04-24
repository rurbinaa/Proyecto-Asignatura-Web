# Delta for Backend Test Coverage

## ADDED Requirements

### Requirement: Handler Service Error Handling Tests

The test suite MUST verify `excel_importer/handler_service.py` handles all error conditions gracefully.

#### Scenario: Corrupted Excel file raises appropriate exception

- GIVEN a file object that is not a valid Excel file
- WHEN `load_and_clean(file_obj, ...)` is called
- THEN the function MUST raise an exception with descriptive error message
- AND the exception MUST NOT expose internal implementation details

#### Scenario: Invalid file format rejects processing

- GIVEN a file with extension `.pdf` or `.csv` instead of `.xlsx`
- WHEN `load_and_clean()` is called
- THEN the function MUST raise `ValueError` or propagate `BadZipFile` from openpyxl

#### Scenario: Missing required columns handled gracefully

- GIVEN an Excel file missing columns defined in `remap_columns`
- WHEN `load_and_clean()` processes the file
- THEN missing columns MUST be created with default values (0 for numeric, "UNKNOWN" for text)

#### Scenario: Empty file returns empty DataFrame

- GIVEN an Excel file with no data rows
- WHEN `load_and_clean()` processes the file
- THEN the function MUST return an empty DataFrame without raising exception

#### Scenario: File read exception during upload

- GIVEN a file object with I/O error (permission denied, file locked)
- WHEN `load_and_clean()` or `load_pivot_range()` is called
- THEN the exception MUST propagate with meaningful context

#### Scenario: Defect fields normalization handles None/0 input

- GIVEN `defeacts_fields` parameter as `None` or `0`
- WHEN `_normalize_defects_fields(defeacts_fields)` is called
- THEN the function MUST return empty list `[]`

#### Scenario: CharField truncation respects max_length

- GIVEN model class with `max_length` constraints and data exceeding limits
- WHEN `_truncate_charfields(model_class, data)` is called
- THEN string values MUST be truncated to `max_length` characters

---

### Requirement: VolatileKpiView Edge Case Tests

The test suite MUST verify `VolatileKpiView` in `quality_data/views.py` handles all edge cases without database dependency.

#### Scenario: Empty DataFrame returns empty KPIs

- GIVEN an Excel file with valid headers but zero data rows
- WHEN `VolatileKpiView.post(request)` processes the file
- THEN response MUST return empty arrays for all KPI keys
- AND `defect_rate` MUST return `{"label": "Defect Rate", "value": 0}`

#### Scenario: Missing file parameter returns 400

- GIVEN a POST request without `file` in request.FILES
- WHEN `VolatileKpiView.post(request)` is called
- THEN response MUST return `{"error": "No file provided"}` with status 400

#### Scenario: Zero sample avoids division by zero

- GIVEN rows where `sample=0` for all records
- WHEN `_calc_aql_by_style(rows)` or `_calc_defect_rate(rows)` is called
- THEN the function MUST return valid results with `aql=0` or `value=0`
- AND MUST NOT raise `ZeroDivisionError`

#### Scenario: Invalid date format in filter computation

- GIVEN rows with malformed or null `date_1` values
- WHEN processing KPIs
- THEN the function MUST handle nulls gracefully without crashing

#### Scenario: Negative or outliers in numeric columns

- GIVEN rows with negative `rejected`, `defects_total`, or outlier values
- WHEN computing `rejected_evolution` or `defect_rate`
- THEN calculations MUST proceed without validation errors

#### Scenario: Single row returns valid trend

- GIVEN a DataFrame with exactly one row
- WHEN `_calc_aql_weekly(rows)` is called
- THEN trend data MUST equal the single AQL point (trend = actual)

#### Scenario: Pivot parser exceptions are caught

- GIVEN `parse_seconds_rework()` or `parse_fabric_defects()` raising exception
- WHEN `VolatileKpiView.post()` processes the file
- THEN the exception MUST be caught
- AND corresponding KPI key MUST return `null` in response

#### Scenario: Filter options computation with partial data

- GIVEN rows missing `color`, `batch`, or `style` columns
- WHEN `_compute_filter_options(rows)` is called
- THEN missing fields MUST return empty arrays
- AND present fields MUST return distinct values

---

### Requirement: Test Isolation and Fixtures

Test code MUST be isolated from production database and use fixtures for data simulation.

#### Scenario: In-memory file upload simulation

- GIVEN pytest fixtures creating `io.BytesIO` with valid Excel content
- WHEN tests call `load_and_clean()` or view endpoints
- THEN no database writes MUST occur
- AND file operations MUST use seekable in-memory streams

#### Scenario: Mock defect types for inspection tests

- GIVEN `DefectType` fixtures with known `name` and `is_active` values
- WHEN testing defect aggregation
- THEN tests MUST use `@pytest.mark.django_db` with controlled fixture data