# Exploration: hotfix-container-upsert-and-dashboard-render

## Current State

### Issue 1: Container Bulk Insert Unique Constraint Error
The `bulk_insert_container` function in `handler_service.py:263-278` uses Django's `bulk_create` without the `ignore_conflicts=True` flag. The `Container` model has a unique constraint on `container_number`:

```python
# backend/quality_data/models.py:126
class Container(models.Model):
    container_number = models.IntegerField(unique=True)  # <-- UNIQUE constraint
```

When importing Excel sheets containing duplicate `container_number` values, the bulk insert fails with:
```
unique constraint "quality_data_container_container_number_key"
```

This is a **known limitation** of `bulk_create` - it doesn't handle duplicates gracefully.

### Issue 2: Dashboard KPI Cards Rendering Blank in Fast Mode
The volatile endpoint (`VolatileKpiView` in `views.py:1334-1347`) returns `defectRate` as an **object** with a specific shape:

```python
# backend/quality_data/views.py:1334-1347
def _calc_defect_rate(self, rows):
    # ...
    return {"label": "Defect Rate", "value": value}  # Returns OBJECT
```

However, the frontend's `normalizeVolatileResponse` in `kpi.js:124` only maps keys (snake_case → camelCase), but does **not** transform the object shape to match live endpoint contracts.

The live KPI endpoints return `defectRate` as a raw **number** (see line 1347: `value` is already the number), but the volatile endpoint wraps it in `{"label", "value"}`.

Looking at DashboardView line 360:
```jsx
<KpiNumberCard
  value={defectRate !== null && !isNullOrError(defectRate) ? defectRate : null}
  // ...
/>
```

When `defectRate` is an object like `{"label": "Defect Rate", "value": 2.5}`, the condition `defectRate !== null` passes (object is truthy), but passing an object to `KpiNumberCard` which expects a number causes it to render `"—"`.

At `KpiNumberCard.jsx:2`:
```javascript
const displayValue = typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : '—';
```

Since value is an object, `typeof value === 'number'` is false, so it shows "—" (dash).

## Affected Areas

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| 1 | `backend/excel_importer/handler_service.py` | 278 | `bulk_create` without `ignore_conflicts=True` |
| 1 | `backend/quality_data/models.py` | 126 | `container_number` has `unique=True` |
| 2 | `backend/quality_data/views.py` | 1334-1347 | `_calc_defect_rate` returns object instead of number |
| 2 | `frontend/src/api/kpi.js` | 124-161 | `normalizeVolatileResponse` maps keys but doesn't transform object shape |
| 2 | `frontend/src/views/DashboardView.jsx` | 358-364 | Passes `defectRate` to `KpiNumberCard` expecting a number |

## Root Causes

### Issue 1: Container Bulk Insert
**Root Cause**: The function uses `bulk_create` without conflict handling. When Excel contains duplicate `container_number` values, Django throws a database constraint violation.

**Line-level evidence**:
- `handler_service.py:278`: `created_containers = Container.objects.bulk_create(container_instances, batch_size=1000)`
- `models.py:126`: `container_number = models.IntegerField(unique=True)`

### Issue 2: Dashboard KPI Blank Cards
**Root Cause**: The volatile endpoint returns `defectRate` as an object `{"label": "Defect Rate", "value": 2.5}`, but the frontend adapter and consumer expect a raw number like live endpoints return.

**Line-level evidence**:
- `views.py:1347`: `return {"label": "Defect Rate", "value": value}` - returns object
- `kpi.js:148-157`: Only maps keys, doesn't unwrap `{label, value}` → number
- `DashboardView.jsx:360`: Passes object to `KpiNumberCard` expecting number

## Approaches

### Issue 1: Container Bulk Insert

| Approach | Description | Pros | Cons | Effort |
|----------|-------------|------|------|--------|
| **A. Add `ignore_conflicts=True`** | Add flag to `bulk_create` to skip duplicates | Minimal code change, leverages Django | Silently ignores duplicates (may lose data) | Low |
| **B. Use upsert logic** | Implement custom upsert (query existing, update or create) | Full control, preserves data | More complex, requires additional queries | Medium |
| **C. Dedupe in memory before bulk_create** | Deduplicate Excel rows by container_number before insert | Simple, maintains bulk performance | Loses duplicate rows silently | Low |

### Issue 2: Dashboard KPI Blank Cards

| Approach | Description | Pros | Cons | Effort |
|----------|-------------|------|------|--------|
| **A. Fix backend volatile endpoint** | Return raw number in `_calc_defect_rate` | Consistent with live endpoints | Changes one KPI behavior | Low |
| **B. Fix frontend adapter** | Unwrap `{label, value}` → number in `normalizeVolatileResponse` | Preserves backend shape, fixes at boundary | Additional adapter logic | Low |
| **C. Fix frontend consumer** | Check if value is object and extract `.value` in DashboardView | Minimal risk, defensive coding | Scattered fix, more conditionals | Low |

## Recommendation

### Issue 1: Container Bulk Insert
**Recommend Approach A** — Add `ignore_conflicts=True` to `bulk_create`. This is the minimal fix that leverages Django's built-in handling.

**Alternative**: If preserving all data is critical, implement Approach B with a custom upsert. However, this adds complexity and the issue likely stems from Excel containing intentional duplicates that should be de-duped at import time.

### Issue 2: Dashboard KPI Blank Cards
**Recommend Approach B** — Fix at the frontend adapter (`normalizeVolatileResponse`). This fixes the contract mismatch at the API boundary without changing backend behavior.

However, there's a deeper issue: `defectRate` is the **only** KPI that returns an object. All other KPIs return arrays or null. This inconsistency in the volatile endpoint is the root cause. The cleaner fix would be **Approach A** — make `_calc_defect_rate` return a raw number to match live endpoints.

## Minimal Fixes

### Issue 1
```python
# backend/excel_importer/handler_service.py:278
created_containers = Container.objects.bulk_create(
    container_instances, 
    batch_size=1000,
    ignore_conflicts=True  # ADD THIS
)
```

### Issue 2 (Backend)
```python
# backend/quality_data/views.py:1334-1347
def _calc_defect_rate(self, rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return 0  # Return raw number, not object
    
    total_defects = df['defects_total'].sum()
    total_sample = df['sample'].sum()
    
    value = 0
    if total_sample > 0:
        value = round((total_defects / total_sample) * 100, 2)
    
    return value  # Return raw number, not object
```

### Issue 2 (Frontend Alternative)
```javascript
// frontend/src/api/kpi.js - normalizeVolatileResponse
// After mapping keys, unwrap object values
if (normalized.defectRate && typeof normalized.defectRate === 'object' && 'value' in normalized.defectRate) {
  normalized.defectRate = normalized.defectRate.value;
}
```

## Test Plan

### Issue 1
1. Create Excel with duplicate container_numbers
2. Run container import
3. Verify import succeeds (no constraint error)
4. Verify only unique containers are created

### Issue 2
1. Upload Excel file in fast-mode dashboard
2. Verify "Tasa de Defectos" KPI card displays numeric value (e.g., "2.50%")
3. Verify no blank/dash rendering

## Risks

- **Issue 1**: `ignore_conflicts=True` silently drops duplicate rows. If user expects all data to be imported, this could hide data issues.
- **Issue 2**: Changing backend return type could break any other consumers expecting the object shape (though likely none exist).

## Ready for Proposal

**Yes** — Root causes identified with line-level evidence. Minimal fixes recommended. Both issues are straightforward hotfixes with low risk.
