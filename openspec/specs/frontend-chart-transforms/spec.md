# Chart Transforms Utility Specification

## Purpose

Define the contract for `frontend/src/utils/chartTransforms.js` — a pure data transformation module that normalizes API responses into chart-ready formats. This module SHALL have no side effects, no external dependencies, and deterministic outputs for given inputs.

## Requirements

### Requirement: Pure Transformation Functions

The module MUST export pure functions that transform API response data into chart-compatible formats. All functions SHALL return `null` for null/error inputs and preserve output shape for valid inputs.

#### Scenario: transformPassReject handles valid data

- GIVEN `data = [{name: "PASS", value: 85}, {name: "REJECT", value: 15}]`
- WHEN `transformPassReject(data)` is called
- THEN the result MUST be `[{name: "PASS", value: 85}, {name: "REJECT", value: 15}]`

#### Scenario: transformPassReject returns null for error

- GIVEN `data = {error: "Failed to fetch"}`
- WHEN `transformPassReject(data)` is called
- THEN the result MUST be `null`

#### Scenario: transformAqlByStyle filters and limits

- GIVEN `data = {data: [{label: "Style-A", value: 2.5}, {label: "Style-B", value: 0}, {label: "Style-C", value: 1.8}]}`
- WHEN `transformAqlByStyle(data)` is called
- THEN the result MUST exclude entries where `value === 0`
- AND the result MUST be limited to 12 entries

#### Scenario: transformAqlWeekly preserves series structure

- GIVEN `data = [{name: "AQL", data: [{x: 1, y: 2.3}]}, {name: "Trend", data: [{x: 1, y: 2.1}]}]`
- WHEN `transformAqlWeekly(data)` is called
- THEN the result MUST preserve `name` and `data` for each series

#### Scenario: transformSecondsRework handles result wrapper

- GIVEN `data = {result: [{name: "Sewing", data: [{x: 1, y: 12.3}]}]}`
- WHEN `transformSecondsRework(data)` is called
- THEN the result MUST extract from `result` key and preserve series structure

### Requirement: Formatter Functions

The module MUST export formatter functions that convert numeric values to human-readable strings for chart labels.

#### Scenario: formatPercent formats with 2 decimals

- GIVEN `value = 2.34567`
- WHEN `formatPercent(value)` is called
- THEN the result MUST be `"2.35%"`

#### Scenario: formatPieces rounds to integer

- GIVEN `value = 234.6`
- WHEN `formatPieces(value)` is called
- THEN the result MUST be `"235 piezas"`

#### Scenario: trimCategoryLabel truncates long labels

- GIVEN `value = "This is a very long category name"`
- WHEN `trimCategoryLabel(value)` is called
- THEN the result MUST be `"This is a very lo…"` (18 chars + ellipsis)

### Requirement: Line State Parsing

The module MUST provide `parseLineStateLabel` and `buildLineCountDataByState` for extracting line-state pairs from combined labels.

#### Scenario: parseLineStateLabel splits on last dash

- GIVEN `label = "Line 1 - Line 2 - PASS"`
- WHEN `parseLineStateLabel(label)` is called
- THEN the result MUST be `{line: "Line 1 - Line 2", state: "PASS"}`

#### Scenario: parseLineStateLabel handles malformed input

- GIVEN `label = "NoDashHere"`
- WHEN `parseLineStateLabel(label)` is called
- THEN the result MUST be `{line: "NoDashHere", state: ""}`

#### Scenario: buildLineCountDataByState filters by state

- GIVEN `parseLineStateLabel` returns `{line: "L1", state: "PASS"}` and `{line: "L2", state: "REJECT"}`
- WHEN `buildLineCountDataByState(data, "PASS")` is called
- THEN the result MUST only include entries where `state === "PASS"`

### Requirement: No Side Effects

All exported functions MUST be pure — no mutation of inputs, no global state access, no async operations.

#### Scenario: Functions do not mutate input arrays

- GIVEN an input array `data = [{name: "A", value: 1}]`
- WHEN any transform function is called with `data`
- THEN the original `data` array MUST remain unchanged

#### Scenario: Functions are deterministic

- GIVEN identical inputs called multiple times
- WHEN the same function is invoked
- THEN the result MUST be identical each time