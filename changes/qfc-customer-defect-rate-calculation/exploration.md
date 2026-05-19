# Exploration: QFC Customer Defect Rate Calculation

## Current State

The **Defect Rate** (displayed as "AQL %") is consistently calculated as `SUM(defects_total) / SUM(sample) * 100` everywhere in the codebase — both for **Plant** (QFA, `table_type='QFA'`) and **Customer** (QFC, `table_type='QFC'`) contexts. The `context` query parameter (`plant` or `customer`) only filters *which records* to aggregate, but does **not** change the formula.

For **Customer (QFC)**, the correct formula must be:

```
defect_rate = SUM(defects_total) / SUM(accepted + rejected) * 100
```

instead of the current:

```
defect_rate = SUM(defects_total) / SUM(sample) * 100
```

## Affected Areas

### 1. Backend — `DefectRateView` (primary target)

- **File**: `backend/quality_data/views/__init__.py` (lines 1061–1093)
- **Endpoint**: `GET /api/kpis/defect-rate/`
- **Problem**: Always computes `round((total_defects / total_sample) * 100, 2)` regardless of context. Queryset is filtered by `get_filtered_queryset()` which applies QFA/QFC filter, but the denominator remains `sample`.
- **Fix needed**: Detect that context is `customer` (QFC) and use `total_accepted + total_rejected` as denominator instead of `total_sample`.

### 2. Backend — `AqlKpiViewSet` (AQL endpoints)

- **File**: `backend/quality_data/views/__init__.py`
- **Endpoints**:
  - `aql_by_team()` (line 1321–1368): `SUM(defects_total) / SUM(sample) * 100`
  - `aql_by_style()` (line 1370–1410): `SUM(defects_total) / SUM(sample) * 100`
  - `aql_weekly()` (line 1412–1482): `SUM(defects_total) / SUM(sample) * 100`
  - `audited_pieces()` (line 1484–1516): SUM(sample) — this one is fine as-is (it measures pieces audited, not defect rate)
- **Problem**: Same issue — all AQL % calculations use `sample` as denominator, ignoring context.

### 3. Backend — `VolatileKpiView._calc_defect_rate()`

- **File**: `backend/quality_data/views/__init__.py` (lines 1849–1862)
- **Note**: This only processes QC FA Plant sheet. NOT affected by the bug (no QFC data goes through volatile path).

### 4. Frontend — `kpiCalculations.js`

- **File**: `frontend/src/utils/kpiCalculations.js` (lines 267–285)
- **Functions**: `calculateDefectRate()`, `calculateAqlByStyle()`, `calculateAqlWeekly()`
- **Note**: All used in volatile/fast mode only, which only processes QC FA Plant data. NOT affected by the bug.

### 5. Tests — `test_kpis.py` and `test_qc_context_filtering.py`

- **File**: `backend/quality_data/tests/test_qc_context_filtering.py` (lines 357–374)
- Current test `test_context_customer_calculates_from_qfc_only` expects `5.5` based on `sample` denominator. Coincidentally the test data has `sample == accepted + rejected` for all records, so the test would still pass after the change — but it wouldn't verify the new logic properly.
- **New tests needed**: Create records where `sample != accepted + rejected` to validate the context-aware formula.

## Approaches

### 1. Context-aware formula in DefectRateView only

Add logic in `DefectRateView.get()` to check the resolved context and switch denominator.

| Pros | Cons |
|------|------|
| Minimal change, targeted fix | AQL endpoints would still be wrong for Customer |

**Effort**: Low

### 2. Context-aware formula in ALL defect-rate / AQL endpoints

Modify `DefectRateView`, `AqlKpiViewSet.aql_by_team`, `aql_by_style`, `aql_weekly` to use `accepted + rejected` as denominator when context is customer.
- Inline the context check in each view method (repetitive but explicit).

| Pros | Cons |
|------|------|
| Covers all affected endpoints | Repetitive logic scattered across views |

**Effort**: Medium

### 3. Helper function + centralize denominator logic

Create a helper like `_resolve_defect_rate_denominator(total_sample, total_accepted, total_rejected, table_type)` that returns `total_sample` for QFA and `total_accepted + total_rejected` for QFC.

| Pros | Cons |
|------|------|
| Single source of truth, easy to test in isolation | Slightly more refactoring |

**Effort**: Medium

## Recommendation

**Approach 3** — Create a shared helper function. It's the cleanest separation of concerns and makes testing straightforward. The AQL % concept is mathematically the same for both contexts; only the denominator changes. A single helper with a unit test ensures consistency.

### Implementation sketch

```python
def _resolve_defect_rate_denominator(total_sample, total_accepted, total_rejected, table_type):
    """
    Return the appropriate denominator for defect-rate / AQL % calculations.
    
    - QFA (Plant): uses sample size (traditional AQL formula).
    - QFC (Customer): uses accepted + rejected (pass + fail).
    """
    if table_type == "QFC":
        return (total_accepted or 0) + (total_rejected or 0)
    return total_sample or 0
```

Each affected view already resolves `table_type` via `_resolve_context_table_type()` inside `_apply_context_filter()`. The view would need to also aggregate `accepted` and `rejected` when context is QFC, or the helper can be called with the already-computed aggregates.

## Risks

- **Existing tests mask the bug**: Current test data has `sample == accepted + rejected` for all QFC records. The tests will pass even after the fix, giving false confidence. **Must add new test data** where `sample != accepted + rejected`.
- **Edge case**: If `accepted + rejected = 0` for a QFC grouping, the formula returns 0 (same as current `sample = 0` guard).
- **Audited Pieces** endpoint sums `sample` and is correct as-is — it's a volume metric, not a rate.
- **Volatile/fast mode** only processes QC FA Plant and is NOT affected.

## Ready for Proposal

Yes — all affected files and the precise change needed have been identified.
