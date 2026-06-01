# Lógica de Sincronización y Prevención de Duplicados

> **Actualizado**: Mayo 2026
> **Archivo principal**: `backend/excel_importer/sync_service.py`

Este documento explica las dos estrategias de sincronización que el sistema usa para importar datos desde Excel a la base de datos, y cómo se previenen duplicados.

---

## Arquitectura General

El sistema implementa **dos estrategias de sincronización** según el tipo de sheet:

| Estrategia | Sheets | Lógica |
|------------|--------|--------|
| **Time-Window Sync** | QC FA Plant, QC FA Customer, Seconds General | Reemplaza registros por rango de fechas |
| **UPSERT** | SecondsA4, Container | Inserta nuevos, actualiza existentes por clave natural |

El flujo general es:

```
Excel → parse (handler_service) → preview (compute_preview_*) → confirm (apply_*) → DB
```

---

## Estrategia 1: Time-Window Sync

**Usada por**: QC FA Plant, QC FA Customer, Seconds General

**Por qué**: Estos sheets no tienen una clave natural única confiable. Un mismo día puede tener múltiples registros con los mismos campos. La estrategia más segura es reemplazar todos los registros de un rango de fechas.

### Flujo de `apply_timewindow()`

```python
def apply_timewindow(excel_rows, model_class, date_field, table_type=None, ...):
    """
    1. Extrae fechas únicas del Excel (normalizadas a ISO)
    2. Busca registros existentes en DB para esas fechas
    3. Compara fechas canónicas (maneja formatos mixtos)
    4. Elimina registros coincidentes por PK
    5. Inserta todos los registros nuevos del Excel
    6. Sincroniza defectos si aplica
    """
```

### Paso a paso

**1. Normalización de fechas**

```python
excel_dates = extract_dates(excel_rows, date_field)
# extract_dates usa parse_date() que normaliza:
# "2026-01-15" → "2026-01-15"
# "01/15/2026" → "2026-01-15"
# "15-Jan-26"  → "2026-01-15"
```

**2. Matching canónico**

```python
# En lugar de WHERE date_1 IN ('2026-01-15', ...) (falla con fechas legacy)
# el sistema carga registros existentes y canoniza en memoria:

existing = qs.only("id", date_column)
canonical_excel_set = set(excel_dates)
ids_to_delete = []

for obj in existing:
    canonical = canonicalize_qc_fa_date(getattr(obj, date_column))
    if canonical in canonical_excel_set:
        ids_to_delete.append(obj.id)
```

**3. Delete + Insert**

```python
# Elimina por PK (preciso, no depende del formato de fecha)
if ids_to_delete:
    model_class.objects.filter(id__in=ids_to_delete).delete()

# Inserta todos los registros nuevos
instances = [_build_instance(model_class, row, ...) for row in excel_rows]
model_class.objects.bulk_create(instances, batch_size=1000)
```

**4. Sincronización de defectos**

```python
# Después de insertar los parent records (QualityQcFa)
# sincroniza los InspectionDefect hijos:
stats = _sync_defects_timewindow(
    excel_rows, model_class, table_type,
    defect_fields, excel_dates, color_map
)
```

### Preview: `compute_preview_timewindow()`

```python
def compute_preview_timewindow(excel_rows, db_queryset, date_field):
    """
    Compara filas por fecha:
    - Cuenta filas Excel vs DB por cada fecha
    - Detecta fechas donde DB tiene más filas (data loss warning)
    - Clasifica: new, modified, unchanged
    """
    return {
        "strategy": "time_window",
        "new": new_count,
        "modified": modified_count,
        "unchanged": unchanged_count,
        "total": len(excel_rows),
        "dates": sorted(excel_dates),
        "date_counts": {date: {"excel": N, "db": N, "diff": N}},
        "warnings": ["Date X: Excel has N rows but DB has M. ..."],
    }
```

---

## Estrategia 2: UPSERT

**Usada por**: SecondsA4, Container

**Por qué**: Estos sheets tienen claves naturales únicas:
- **SecondsA4**: `(date, cut_num, color)`
- **Container**: `(container_number)`

### Flujo de `apply_upsert()`

```python
def apply_upsert(excel_rows, model_class, key_builder, ...):
    """
    1. Construye índice de DB por clave natural
    2. Deduplica filas Excel (última gana)
    3. Para cada fila:
       - Si clave no existe → crear (bulk_create)
       - Si clave existe → actualizar (bulk_update)
    4. Sincroniza defectos si aplica
    """
```

### Paso a paso

**1. Construcción del índice DB**

```python
db_index = {}
for obj in model_class.objects.only(*key_field_names).iterator():
    row_dict = _model_to_dict(obj)
    key = key_builder(row_dict)
    db_index[key] = obj  # Guarda el objeto, no el dict
```

**2. Deduplicación de Excel**

```python
# Si el mismo container_number aparece 2 veces en el Excel,
# la última fila gana (overwrite):
deduped_rows_map = {}
for row in excel_rows:
    deduped_rows_map[key_builder(row)] = row
deduped_rows = list(deduped_rows_map.values())
```

**3. Clasificación y apply**

```python
for row in deduped_rows:
    key = key_builder(row)
    if key not in db_index:
        # Nuevo → crear instancia
        instance = _build_instance(model_class, row, ...)
        new_instances.append(instance)
    else:
        # Existente → actualizar campos
        instance = db_index[key]
        _update_instance(instance, row, ...)
        update_instances.append(instance)

# Batch operations
if new_instances:
    model_class.objects.bulk_create(new_instances, batch_size=1000)
if update_instances:
    model_class.objects.bulk_update(update_instances, update_fields, batch_size=1000)
```

### Preview: `compute_preview_upsert()`

```python
def compute_preview_upsert(excel_rows, db_queryset, key_builder, date_field):
    """
    Compara filas por clave natural:
    - new: clave no existe en DB
    - modified: clave existe pero algún campo difiere
    - unchanged: clave existe y campos idénticos
    """
    return {
        "strategy": "upsert",
        "new": new_count,
        "modified": modified_count,
        "unchanged": unchanged_count,
        "total": len(excel_rows),
        "dates": sorted(dates),
    }
```

---

## Sincronización de Defectos

Los defectos se sincronizan después de los parent records. Hay dos paths:

### `_sync_defects()` (para UPSERT)

```python
def _sync_defects(rows, model_class, defect_fields, color_map=None):
    """
    1. Para cada fila, busca el parent record por clave natural
    2. Para cada campo de defecto con amount > 0:
       a. Resuelve DefectType (auto-seed si no existe)
       b. Crea o actualiza InspectionDefect
    """
```

### `_sync_defects_timewindow()` (para Time-Window)

```python
def _sync_defects_timewindow(rows, model_class, table_type, defect_fields,
                              excel_dates, color_map=None):
    """
    1. Carga todos los parent records para las fechas del Excel
    2. Construye índice por canonical key: (date, po, style, team, color, table_type)
    3. Para cada fila con defectos:
       a. Busca parent por canonical key
       b. Crea InspectionDefect con amount
    4. Auto-seed DefectType si no existe
    5. Retorna stats: created, matched, unmatched, invalid_date, missing_color
    """
```

### Canonical Key para Parent Matching

```python
def build_qc_fa_key(row):
    """
    Clave canónica para emparejar defectos con parents.
    Usa: (canonical_date, po, style, team, color, table_type)
    """
    return (
        canonicalize_qc_fa_date(row.get("date_1", "")),
        int(row.get("po", 0)),
        str(row.get("style", "")).strip(),
        int(row.get("team", 0)),
        str(row.get("color", "")).strip().lower().replace(" ", "_"),
        row.get("table_type"),
    )
```

---

## Normalización de Fechas

### `canonicalize_qc_fa_date()`

Convierte cualquier formato de fecha a ISO `YYYY-MM-DD`:

```python
def canonicalize_qc_fa_date(raw):
    """
    Acepta:
    - "2026-01-15" (ISO) → "2026-01-15"
    - "01/15/2026" (US) → "2026-01-15"
    - "15/01/2026" (EU) → "2026-01-15" (ambiguo, asume EU)
    - 45678 (Excel serial) → "2026-01-15"
    - "15-Jan-26" → "2026-01-15"
    
    Retorna None si no puede parsear.
    """
```

### `parse_date()`

Wrapper que llama a `canonicalize_qc_fa_date()` y maneja errores.

---

## Resolución de Colores

### `_resolve_colors_batch()`

```python
def _resolve_colors_batch(color_names):
    """
    Resuelve nombres de color a instancias Color en O(1) queries.
    
    1. Carga colores existentes en 1 query
    2. Bulk-crea los que faltan (ignore_conflicts)
    3. Retorna {name: Color instance} para O(1) lookups
    """
```

### `_collect_sheet_colors()`

```python
def _collect_sheet_colors(rows, color_field="color"):
    """
    Extrae nombres únicos de color de una lista de rows.
    Normaliza: lowercase, underscore, strip.
    """
```

---

## Transacción Atómica

`apply_session()` ejecuta todo dentro de `transaction.atomic()`:

```python
def apply_session(session):
    """
    Aplica TODOS los sheets en una sola transacción.
    Si cualquier sheet falla, todo se revierte.
    """
    # 1. Hidrata desde Redis si es necesario
    if session.redis_stored:
        _hydrate_session_from_redis(session)
    
    # 2. Resuelve TODOS los colores upfront (1-2 queries)
    color_map = _resolve_colors_batch(all_color_names)
    
    # 3. Aplica cada sheet
    with transaction.atomic():
        apply_timewindow(session.qc_fa_plant_data, QualityQcFa, ...)
        apply_timewindow(session.qc_fa_customer_data, QualityQcFa, ...)
        apply_upsert(session.seconds_a4_data, SecondsA4, ...)
        apply_timewindow(session.seconds_general_data, SecondsGeneral, ...)
        apply_upsert(session.container_data, Container, ...)
```

---

## Prevención de Duplicados

| Mecanismo | Aplica a | Cómo |
|-----------|----------|------|
| **Time-Window delete** | QC FA, Seconds General | Elimina por rango de fechas antes de insertar |
| **Natural key matching** | SecondsA4, Container | UPSERT: si clave existe, actualiza |
| **Deduplicación en upload** | Todos | Última fila gana si hay duplicados en el Excel |
| **Unique constraint** | InspectionDefect | `UNIQUE(inspection, defect_type)` previene duplicados de defectos |
| **Canonical date matching** | QC FA | Maneja fechas en formatos mixtos sin perder registros |

---

## Limitaciones

1. **Time-Window reemplaza, no mergea**: Si el Excel tiene menos filas que la DB para una fecha, las filas faltantes se eliminan.
2. **UPSERT no detecta eliminaciones**: Si una fila existía en DB pero no en Excel, no se elimina.
3. **Formatos de fecha mixtos**: `canonicalize_qc_fa_date` maneja la mayoría pero puede fallar con formatos ambiguos (DD/MM vs MM/DD).
4. **Performance**: Para sheets grandes (>10K filas), el canonical matching carga todos los registros existentes en memoria.

---

## Para Desarrolladores

### Agregar un nuevo sheet

1. Definir `*_REMAP`, `*_NUMERIC_COLUMNS`, `*_NOT_NUMERIC_COLUMNS` en `sheet_configs.py`
2. Crear key builder si tiene clave natural (para UPSERT)
3. Agregar caso en `apply_session()` con la estrategia correcta
4. Agregar preview en `compute_preview()`
5. Tests

### Debuggear sync

```python
# Ver qué fechas se están normalizando
from excel_importer.date_utils import canonicalize_qc_fa_date
print(canonicalize_qc_fa_date("01/15/2026"))  # → "2026-01-15"

# Ver qué registros se van a eliminar
from excel_importer.sync_service import extract_dates
dates = extract_dates(rows, "date_1")
print(dates)  # → {"2026-01-15", "2026-01-16"}
```
