# Modelo De Datos Backend (Estado Implementado)

Este documento refleja el estado real del modelo en `backend/quality_data/models.py` y su complemento de carga inicial en `backend/quality_data/init_data_models.py`.

## 1. Resumen General

- App principal: `quality_data`.
- Esquemas funcionales: control de calidad (`QualityQcFa`, `InspectionDefect`), segundos (`SecondsA4`, `SecondsGeneral`) y contenedores (`Container`, `ContainerInspectionDefect`).
- Catalogos reutilizables: `Color`, `DefectType`, `ContainerDefectType`.
- Relaciones M2M con tabla intermedia: `QualityQcFa <-> DefectType` y `Container <-> ContainerDefectType`.

## 2. Tablas Y Campos

### 2.1 `Color`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `name` | `CharField(max_length=50)` | No | - | `unique=True` |
| `is_active` | `BooleanField` | No | `True` | - |

Uso relacional:
- FK desde `QualityQcFa.color`.
- FK desde `SecondsA4.color`.

### 2.2 `DefectType`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `name` | `CharField(max_length=100)` | No | - | `unique=True` |
| `is_active` | `BooleanField` | No | `True` | - |

Uso relacional:
- M2M con `QualityQcFa` via `InspectionDefect`.

### 2.3 `QualityQcFa`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `table_type` | `CharField(max_length=3)` | No | - | `choices=[QFA,QFC]` |
| `date_1` | `CharField(max_length=20)` | No | - | - |
| `week` | `IntegerField` | No | - | - |
| `customer` | `CharField(max_length=50)` | No | - | - |
| `team` | `IntegerField` | No | - | - |
| `coord` | `CharField(max_length=50)` | No | - | - |
| `date_2` | `CharField(max_length=20)` | Blank si | `""` | - |
| `po` | `IntegerField` | No | - | - |
| `style` | `CharField(max_length=50)` | No | - | - |
| `batch` | `IntegerField` | No | - | - |
| `color` | `ForeignKey(Color)` | No | - | `on_delete=PROTECT` |
| `qty` | `IntegerField` | No | - | - |
| `seconds` | `IntegerField` | No | - | - |
| `accepted` | `IntegerField` | No | - | - |
| `rejected` | `IntegerField` | No | - | - |
| `sample` | `IntegerField` | No | - | - |
| `defects_total` | `IntegerField` | No | `0` | - |
| `aql` | `FloatField` | No | - | - |
| `pass_or_fail` | `CharField(max_length=10)` | No | - | - |
| `defects` | `ManyToManyField(DefectType)` | - | - | `through=InspectionDefect` |

### 2.4 `InspectionDefect` (tabla intermedia de defectos de inspeccion)

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `inspection` | `ForeignKey(QualityQcFa)` | No | - | `on_delete=CASCADE` |
| `defect_type` | `ForeignKey(DefectType)` | No | - | `on_delete=PROTECT` |
| `amount` | `IntegerField` | No | `0` | - |

Constraints:
- `UniqueConstraint(fields=["inspection", "defect_type"], name="unique_quality_qc_fa_defect")`.

### 2.5 `SecondsA4`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `year` | `IntegerField` | No | - | - |
| `week` | `IntegerField` | No | - | - |
| `date` | `CharField(max_length=20)` | No | - | - |
| `cut_num` | `IntegerField` | No | - | - |
| `style` | `CharField(max_length=50)` | No | - | - |
| `cut_qty` | `IntegerField` | No | - | - |
| `color` | `ForeignKey(Color)` | No | - | `on_delete=PROTECT` |
| `first_quality_qty_sewing` | `IntegerField` | No | - | - |
| `sample` | `IntegerField` | No | - | - |
| `pass_field` | `IntegerField` | No | - | - |
| `fail_field` | `IntegerField` | No | - | - |
| `sew_def` | `IntegerField` | No | - | - |
| `fab_def` | `IntegerField` | No | - | - |
| `accepted` | `IntegerField` | No | - | - |
| `rejected` | `IntegerField` | No | - | - |
| `total_of_2ds` | `IntegerField` | No | - | - |
| `percentage_of_2ds` | `FloatField` | No | - | - |
| `line` | `CharField(max_length=20)` | No | - | - |
| `seconds_by_sew` | `IntegerField` | No | - | - |
| `seconds_by_fab` | `IntegerField` | No | - | - |
| `seconds_sew_a4` | `IntegerField` | No | - | - |
| `seconds_fab_a4` | `IntegerField` | No | - | - |

### 2.6 `SecondsGeneral`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `date` | `CharField(max_length=20)` | No | - | - |
| `week` | `IntegerField` | No | - | - |
| `corrido_2` | `IntegerField` | No | - | - |
| `barre` | `IntegerField` | No | - | - |
| `otros_3` | `IntegerField` | No | - | - |
| `degradacion` | `IntegerField` | No | - | - |
| `bordados` | `IntegerField` | No | - | - |
| `total_de_tela` | `IntegerField` | No | - | - |

### 2.7 `ContainerDefectType`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `name` | `CharField(max_length=100)` | No | - | `unique=True` |
| `is_active` | `BooleanField` | No | `True` | - |

Uso relacional:
- M2M con `Container` via `ContainerInspectionDefect`.

### 2.8 `Container`

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `container_number` | `IntegerField` | No | - | - |
| `customer` | `CharField(max_length=50)` | No | - | - |
| `transfer_of_container` | `IntegerField` | No | `0` | - |
| `total_palette` | `IntegerField` | No | - | - |
| `total_palette_pass` | `IntegerField` | No | - | - |
| `total_palette_rejected` | `IntegerField` | No | - | - |
| `percentage_pass` | `FloatField` | No | - | - |
| `percentage_reject` | `FloatField` | No | - | - |
| `defects` | `ManyToManyField(ContainerDefectType)` | - | - | `through=ContainerInspectionDefect` |

### 2.9 `ContainerInspectionDefect` (tabla intermedia de defectos de contenedor)

| Campo | Tipo Django | Null/Blank | Default | Restricciones |
|---|---|---|---|---|
| `id` | `BigAutoField` | No | Auto | PK |
| `container` | `ForeignKey(Container)` | No | - | `on_delete=CASCADE` |
| `defect_type` | `ForeignKey(ContainerDefectType)` | No | - | `on_delete=PROTECT` |
| `amount` | `PositiveIntegerField` | No | `0` | - |

Constraints:
- `UniqueConstraint(fields=["container", "defect_type"], name="unique_container_defect")`.

## 3. Relaciones Del Modelo

- `QualityQcFa.color -> Color` (N:1).
- `SecondsA4.color -> Color` (N:1).
- `QualityQcFa <-> DefectType` (N:M via `InspectionDefect`).
- `Container <-> ContainerDefectType` (N:M via `ContainerInspectionDefect`).

## 4. Catalogos Iniciales (`init_data_models.py`)

Funciones de carga inicial:
- `SaveColor()` carga `COMPANY_COLORS` en `Color` si no existen.
- `SaveDefects()` carga `GARMENT_DEFECT_TYPES` en `DefectType` si no existen.
- `SaveDefectsContainer()` carga `CONTAINER_DEFECT_TYPES` en `ContainerDefectType` si no existen.

Regla de insercion:
- Patrón `if not Model.objects.filter(name=i).exists(): Model.objects.create(...)`.

## 5. Referencias De Codigo

- `backend/quality_data/models.py`
- `backend/quality_data/init_data_models.py`
- `docs/diagrams/.plantuml`
