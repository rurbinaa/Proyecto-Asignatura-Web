# Backend Media Test Coverage Specification

## Purpose

Define test coverage requirements for `media_data` backend inspection flows, ensuring reliability of bridge calculations and API state transitions.

## Requirements

### Requirement: Inspection Bridge Unit Tests

The test suite MUST verify `inspection_bridge.py` behavior for all bridging scenarios between media and quality data.

#### Scenario: Bridge rejects unclosed inspection

- GIVEN an InspectionData instance with `is_closed=False`
- WHEN `bridge_inspection(inspection)` is called
- THEN the function MUST raise `ValueError` with message "Inspection must be closed before bridging."

#### Scenario: Bridge handles no matching QC records

- GIVEN a closed inspection with style/color combination that has no matching QualityQcFa records
- WHEN `bridge_inspection(inspection)` is called
- THEN the function MUST return `{"matched_records": 0, "synced_defects": 0, "status": "no_match"}`

#### Scenario: Bridge syncs single QC record with defects

- GIVEN a closed inspection with 3 RevisionDefect records (2 defect_type_A, 1 defect_type_B)
- AND a matching QualityQcFa record with `sample=100`
- WHEN `bridge_inspection(inspection)` is called
- THEN the QC record MUST have `rejected=3`, `accepted=97`, `defects_total=3`
- AND the function MUST return `{"matched_records": 1, "synced_defects": 2, "status": "synced", "total_defects": 3}`

#### Scenario: Bridge syncs multiple QC records for same style/color

- GIVEN a closed inspection matching TWO QualityQcFa records with different batches
- WHEN `bridge_inspection(inspection)` is called
- THEN BOTH QC records MUST be updated with same defect totals
- AND the function MUST return `{"matched_records": 2, ...}`

#### Scenario: Defect aggregation counts by type name

- GIVEN an inspection with RevisionDefect records having defect_counts `[("type_A", 5), ("type_A", 3), ("type_B", 2)]`
- WHEN `_aggregate_defects(inspection)` is called
- THEN it MUST return `{"type_A": 8, "type_B": 2}`

#### Scenario: InspectionDefect sync creates through-table records

- GIVEN a QualityQcFa record and defect_counts with active defect types
- WHEN `_sync_defect_types(qc_record, defect_counts)` is called
- THEN InspectionDefect records MUST be created linking the QC record to each defect type
- AND existing InspectionDefect records for that QC record MUST be deleted before recreation

#### Scenario: InspectionDefect sync skips inactive defect types

- GIVEN defect_counts containing a defect type name where `DefectType.is_active=True`
- AND another defect type name where `DefectType.is_active=False`
- WHEN syncing
- THEN only the active defect type MUST create an InspectionDefect record

### Requirement: Close Inspection Endpoint Tests

The test suite MUST verify the `close_inspection` endpoint handles all state transitions correctly.

#### Scenario: Close rejects already-closed inspection

- GIVEN an inspection with `is_closed=True`
- WHEN POST `/api/inspections/<id>/close_inspection/`
- THEN the response MUST have status 400
- AND contain `{"error": "The inspection is already closed"}`

#### Scenario: Close inspection with defects sets REJECT status

- GIVEN an open inspection with 5 RevisionDefect records
- WHEN POST `/api/inspections/<id>/close_inspection/`
- THEN the inspection MUST have `status='REJECT'`, `is_closed=True`, and `closed_at` set
- AND the response MUST contain `{"result": "REJECT", "total_defects": 5}`
- AND the response MUST include `quality_data_sync` bridge result

#### Scenario: Close inspection without defects sets PASS status

- GIVEN an open inspection with 0 RevisionDefect records
- WHEN POST `/api/inspections/<id>/close_inspection/`
- THEN the inspection MUST have `status='PASS'`, `is_closed=True`, and `closed_at` set
- AND the response MUST contain `{"result": "PASS", "total_defects": 0}`
- AND the response MUST include `quality_data_sync` bridge result

#### Scenario: Close returns bridge synchronization result

- GIVEN a closed inspection matching one QualityQcFa record
- WHEN the endpoint is called
- THEN the response MUST include a `quality_data_sync` key
- AND `quality_data_sync` MUST contain bridge result status and matched records count

### Requirement: Edge Case Coverage

The test suite MUST cover boundary conditions and error states to prevent regressions.

#### Scenario: Zero defects produces PASS and zero totals

- GIVEN a closed inspection with zero RevisionDefect records
- AND matching QualityQcFa with `sample=50`
- WHEN bridging
- THEN QC record MUST have `rejected=0`, `accepted=50`, `defects_total=0`

#### Scenario: Sample smaller than defect count handles gracefully

- GIVEN a QualityQcFa with `sample=10`
- AND defect_counts totaling 15 defects
- WHEN calculating rejected/accepted
- THEN `rejected=15` and `accepted=0` (max fallback)
- AND no negative values allowed

#### Scenario: Null defect_type is excluded from aggregation

- GIVEN RevisionDefect records where `defect_type=None`
- WHEN `_aggregate_defects(inspection)` is called
- THEN those records MUST be excluded from the count