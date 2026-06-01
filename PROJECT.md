# Rift Analytics — Documentación Técnica Completa

> **Última actualización**: Mayo 2026
> **Para quién**: Desarrolladores que heredan el proyecto y necesitan entenderlo para mantenerlo, evolucionarlo o debuggearlo.

---

## Tabla de Contenidos

1. [Qué es Rift Analytics](#1-qué-es-rift-analytics)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura General](#3-arquitectura-general)
4. [Backend (Django)](#4-backend-django)
5. [Frontend (React)](#5-frontend-react)
6. [Base de Datos](#6-base-de-datos)
7. [API Endpoints](#7-api-endpoints)
8. [Flujo de Importación Excel](#8-flujo-de-importación-excel)
9. [Sistema de KPIs y Dashboards](#9-sistema-de-kpis-y-dashboards)
10. [Autenticación y Autorización](#10-autenticación-y-autorización)
11. [Docker y Entorno](#11-docker-y-entorno)
12. [Testing](#12-testing)
13. [Guía de Desarrollo](#13-guía-de-desarrollo)
14. [Despliegue (Vercel + Railway)](#14-despliegue-vercel--railway)
15. [Decisiones de Arquitectura](#15 decisiones-de-arquitectura)
16. [Deuda Técnica Conocida](#16-deuda-técnica-conocida)
17. [Glosario de Términos del Dominio](#17-glosario-de-términos-del-dominio)
18. [Workflows Detallados](#18-workflows-detallados)

---

## 1. Qué es Rift Analytics

Rift Analytics es una plataforma web para **digitalización y análisis de calidad (QA)** en plantas de manufactura de confección textil. Resuelve dos problemas:

1. **Captura de datos**: Los operadores cargan reportes de inspección Excel y el sistema los parsea, valida y persiste automáticamente.
2. **Análisis gerencial**: La gerencia ve dashboards interactivos con KPIs de calidad (AQL, defectos, rendimiento por línea/cliente, etc.) para tomar decisiones.

### Usuarios del sistema

| Rol | Acceso | Ejemplo de uso |
|-----|--------|----------------|
| **Manager** | Login + Dashboard + Excel Upload + Reports | Sube Excel semanal, revisa KPIs, descarga reportes corporativos |
| **Operator** | (Deprecado) Solo existía para Touch Capture que fue removido | — |

### Dominio de negocio

El sistema maneja datos de **5 fuentes de inspección** diferentes:

| Fuente | Descripción | Modelo Django |
|--------|-------------|---------------|
| **QC FA Plant** | Inspecciones de calidad final en planta | `QualityQcFa(table_type="QFA")` |
| **QC FA Customer** | Inspecciones de calidad final del cliente | `QualityQcFa(table_type="QFC")` |
| **SecondsA4** | Segundas piezas (rework) por corte | `SecondsA4` |
| **Seconds General** | Segundas piejas general con detalle de defectos | `SecondsGeneral` + `SecondsGeneralDefect` |
| **Container** | Inspección de contenedores de empaque | `Container` + `ContainerInspectionDefect` |

---

## 2. Stack Tecnológico

### Backend

| Componente | Tecnología | Versión | Para qué |
|------------|------------|---------|----------|
| Framework | Django + DRF | ≥5.0 | API REST |
| ASGI Server | Daphne | — | Servidor asíncrono |
| Base de datos | PostgreSQL | 16 | Persistencia principal |
| Cache | Redis | 7-alpine | Cache de KPIs y sesiones Excel |
| Auth | SimpleJWT | — | Tokens JWT stateless |
| Excel parsing | pandas + openpyxl | — | Lectura de archivos .xlsx |
| Excel writing | xlsxwriter | ≥3.2.0 | Generación de reportes corporativos |
| Testing | pytest + pytest-django | — | Suite de tests backend |

### Frontend

| Componente | Tecnología | Versión | Para qué |
|------------|------------|---------|----------|
| Framework | React | 19.2 | UI |
| Build tool | Vite + SWC | 7.x | Dev server y bundling |
| HTTP client | Axios | 1.15 | Comunicación con API |
| Charts | Recharts | 3.8 | Gráficos de KPIs |
| Icons | Lucide React + React Icons | — | Iconografía |
| File upload | react-dropzone | 15 | Drag & drop de Excel |
| Testing | Vitest + Testing Library | 4.x | Unit/integration tests frontend |
| Mocking | MSW (Mock Service Worker) | 2.13 | Mock de API en tests |
| Package manager | Bun | — | Instalación y scripts |

### Infraestructura

| Componente | Tecnología | Para qué |
|------------|------------|----------|
| Containerización | Docker Compose | Entorno local consistente |
| Deploy backend | Railway | Hosting del API |
| Deploy frontend | Vercel | Hosting del SPA |
| CI/CD | GitHub Actions (Vercel auto) | Preview deployments en PRs |

---

## 3. Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)              │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Views   │  │  Components  │  │  API Layer (axios)    │  │
│  │  (pages) │  │  (KPI cards, │  │  - auth.js            │  │
│  │          │  │   charts,    │  │  - kpi.js             │  │
│  │          │  │   filters)   │  │  - excel.js           │  │
│  └──────────┘  └──────────────┘  │  - reports.js         │  │
│                                  └───────────┬───────────┘  │
└──────────────────────────────────────────────┼──────────────┘
                                               │ HTTP/JSON
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (Django + DRF)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  auth_data   │  │ quality_data │  │  excel_importer  │   │
│  │  (login,     │  │ (KPIs,       │  │  (parse, sync,   │   │
│  │   JWT, roles)│  │  dashboards, │  │   preview)       │   │
│  │              │  │  reports)    │  │                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                          │                    │              │
└──────────────────────────┼────────────────────┼──────────────┘
                           │                    │
              ┌────────────┴────────────────────┴──────────┐
              │              DATA LAYER                     │
              │  ┌─────────────┐    ┌─────────────────┐    │
              │  │ PostgreSQL  │    │     Redis        │    │
              │  │ (models,    │    │ (cache KPIs,     │    │
              │  │  migrations)│    │  Excel preview)  │    │
              │  └─────────────┘    └─────────────────┘    │
              └────────────────────────────────────────────┘
```

### Principios de diseño

- **Backend stateless**: JWT sin sesiones server-side. Redis solo para cache.
- **Preview-before-commit**: El Excel se parsea primero, el usuario revisa, luego confirma.
- **Dual mode**: Los mismos KPIs se calculan desde DB (live) o desde Excel en memoria (volatile/fast mode).
- **Context isolation**: QFA y QFC comparten modelo pero se aíslan por `table_type`.

---

## 4. Backend (Django)

### Estructura de directorios

```
backend/
├── backend/              # Configuración del proyecto Django
│   ├── settings.py       # Settings principal
│   ├── urls.py           # URL routing raíz
│   ├── asgi.py           # ASGI entry point (Daphne)
│   └── wsgi.py           # WSGI entry point (legacy)
├── auth_data/            # App de autenticación
│   ├── models.py         # UserProfile (extiende Django User)
│   ├── views.py          # Login, CurrentUser, Logout
│   ├── serializers.py    # CustomTokenObtainPairSerializer
│   ├── urls.py           # /api/auth/*
│   ├── management/       # Comandos: seed_auth_users, bootstrap_auth_users
│   └── tests/            # test_auth.py
├── quality_data/         # App principal de calidad
│   ├── models.py         # Todos los modelos de datos
│   ├── views/            # Views organizadas por dominio
│   │   ├── __init__.py   # KPIs principales (QC FA)
│   │   ├── container_views.py
│   │   ├── seconds_a4_views.py
│   │   └── seconds_gen_views.py
│   ├── urls.py           # /quality/*
│   ├── serializers.py    # Serializers para KPIs
│   ├── volatile_kpi_service.py  # Cálculo de KPIs en memoria (Fast Mode)
│   ├── dashboard_assemblers.py  # Ensamblaje de datos para dashboards
│   ├── dashboard_contracts.py   # DTOs y contratos de dashboard
│   ├── corporate_xlsx_service.py # Generación de reportes Excel
│   ├── init_data_models.py      # Seed data (colores, defectos)
│   └── tests/            # Suite completa de tests
├── excel_importer/       # App de importación Excel
│   ├── handler_service.py # Parseo principal de Excel
│   ├── sync_service.py   # Persistencia a DB
│   ├── sheet_configs.py  # Configuración de columnas por sheet
│   ├── date_utils.py     # Normalización de fechas
│   ├── pivot_parsers.py  # Parseo de tablas pivot
│   └── tests/            # Tests de importación
├── manage.py
├── requirements.txt
├── Dockerfile
├── pytest.ini
└── .env.example
```

### Django Apps

#### `auth_data` — Autenticación

Responsabilidad: Login JWT, perfil de usuario, roles.

**Modelo principal**:
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=CASCADE)
    role = models.CharField(choices=[('manager','Manager'), ('operator','Operator')])
    # properties: is_manager, is_operator
```

**Endpoints**:
- `POST /api/auth/login/` → JWT access + refresh token
- `GET /api/auth/me/` → Usuario actual (rechaza operators)
- `POST /api/auth/logout/` → No-op (JWT stateless)
- `POST /api/auth/token/refresh/` → Renovar access token

**Comandos management**:
- `seed_auth_users` — Crea usuarios de prueba
- `bootstrap_auth_users` — Crea usuarios iniciales del sistema (manager por defecto)

#### `quality_data` — Calidad y KPIs

Responsabilidad: Todos los modelos de datos de calidad, KPIs, dashboards, reportes.

**Modelos** (ver sección 6 para detalle completo):
- `QualityQcFa` — QC FA Plant + Customer (unificado con `table_type`)
- `InspectionDefect` — Defectos individuales por inspección QC FA
- `SecondsA4` — Datos de segundas piezas por corte
- `SecondsGeneral` — Datos generales de segundas piezas
- `SecondsGeneralDefect` — Defectos por SecondsGeneral
- `Container` — Inspecciones de contenedores
- `ContainerInspectionDefect` — Defectos por contenedor
- `ExcelSyncSession` — Sesiones de importación (preview/confirm/reject)
- `Color`, `DefectType`, `ContainerDefectType`, `SecondsGeneralDefectType` — Catálogos

**Views organizadas por archivo**:
- `views/__init__.py` — KPIs principales de QC FA (AQL, performance, defectos, etc.)
- `views/container_views.py` — KPIs de contenedores
- `views/seconds_a4_views.py` — KPIs de SecondsA4
- `views/seconds_gen_views.py` — KPIs de SecondsGeneral

#### `excel_importer` — Importación Excel

Responsabilidad: Parsear archivos Excel, normalizar datos, sincronizar con DB.

**Archivos clave**:
- `handler_service.py` — `load_and_clean()` parsea cada sheet del Excel según configuración
- `sync_service.py` — `apply_timewindow()` persiste datos con estrategia de reemplazo por ventana temporal
- `sheet_configs.py` — Mapeo de columnas Excel → campos Django, tipos numéricos, campos de defectos
- `date_utils.py` — `canonicalize_qc_fa_date()` normaliza fechas en formatos mixtos
- `pivot_parsers.py` — Parseo de tablas pivot embebidas en el Excel

---

## 5. Frontend (React)

### Estructura de directorios

```
frontend/src/
├── api/                    # Capa de comunicación con backend
│   ├── axiosClient.js      # Instancia Axios + interceptors + token storage
│   ├── auth.js             # Login, logout, getCurrentUser
│   ├── kpi.js              # Todas las funciones de KPI (14+ endpoints)
│   ├── excel.js            # Preview, confirm, reject de Excel
│   └── reports.js          # Descarga de reportes corporativos
├── contexts/
│   └── AuthContext.jsx     # Context de autenticación (user, login, logout)
├── hooks/
│   └── withRoleProtection.jsx  # HOC para proteger rutas por rol
├── views/                  # Páginas principales
│   ├── LoginView.jsx       # Formulario de login
│   ├── DashboardShell.jsx  # Shell con tabs para 5 dashboards
│   ├── QualityReportsView.jsx # Vista de reportes
│   └── dashboards/         # Dashboards individuales
│       ├── QcfaKpiDashboard.jsx    # Componente compartido QFA/QFC
│       ├── PlantDashboard.jsx      # Wrapper context="plant"
│       ├── CustomerDashboard.jsx   # Wrapper context="customer"
│       ├── SecondsA4Dashboard.jsx  # Dashboard SecondsA4
│       ├── SecondsGeneralDashboard.jsx # Dashboard SecondsGeneral
│       └── ContainerDashboard.jsx  # Dashboard Container
├── Components/             # Componentes reutilizables
│   ├── Sidebar.jsx         # Navegación lateral
│   ├── Navbar.jsx          # Barra superior
│   ├── ExcelUploader.jsx   # Drag & drop de Excel
│   ├── DateRangePicker.jsx # Selector de rango de fechas
│   ├── ReportGenerator.jsx # Generador de reportes
│   └── kpi/                # Componentes de KPI
│       ├── KpiCard.jsx         # Card contenedor de KPI
│       ├── BarChartKpi.jsx     # Gráfico de barras
│       ├── LineChartKpi.jsx    # Gráfico de líneas
│       ├── DonutChartKpi.jsx   # Gráfico dona
│       ├── HeatmapKpi.jsx      # Heatmap
│       ├── KpiNumberCard.jsx   # Card numérico simple
│       ├── FilterBar.jsx       # Filtros del dashboard
│       ├── ContainerFilterBar.jsx # Filtros específicos de contenedor
│       └── SecondsA4FilterBar.jsx # Filtros específicos de SecondsA4
├── utils/
│   └── volatileFilters.js  # Utilidades para filtros de Fast Mode
├── test/
│   └── setup.js            # Configuración de Vitest
├── App.jsx                 # Componente raíz + routing por estado
├── App.css                 # Estilos globales
└── main.jsx                # Entry point
```

### Routing

El frontend NO usa react-router. La navegación se maneja con **estado local** en `App.jsx`:

```jsx
const [activeView, setActiveView] = useState('excel'); // 'excel' | 'dashboard' | 'reports'
```

El `Sidebar` actualiza `activeView` y el `AppContent` renderiza el componente correspondiente. La vista activa se persiste en `localStorage` con key `rift-activeView`.

### Flujo de datos

```
User → Component → API function (api/kpi.js) → axiosClient → Backend
                                                ↓
                                    Interceptor agrega JWT
                                    Interceptor maneja 401
```

### Dashboard Architecture

`DashboardShell` maneja 5 "sheets" (tabs):

| Sheet | Componente | Context | Datos |
|-------|------------|---------|-------|
| QC FA Plant | `PlantDashboard` | `context=plant` | QualityQcFa QFA |
| QC FA Customer | `CustomerDashboard` | `context=customer` | QualityQcFa QFC |
| Seconds A4 | `SecondsA4Dashboard` | — | SecondsA4 |
| Seconds General | `SecondsGeneralDashboard` | — | SecondsGeneral |
| Container | `ContainerDashboard` | — | Container |

`PlantDashboard` y `CustomerDashboard` son wrappers que pasan `context` a `QcfaKpiDashboard`, que es el componente compartido que renderiza los 14 cards de KPI.

### KPI Components

Cada KPI se renderiza en un `KpiCard` que contiene:
- Título
- Valor o gráfico (Bar, Line, Donut, Heatmap, Number)
- Loading state con spinner
- Error state

Los datos se transforman con funciones en `dashboardMetricUtils.js` y `lineChartUtils.js`.

---

## 6. Base de Datos

### Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐
│     Color       │       │   DefectType     │
│  (catálogo)     │       │   (catálogo)     │
└────────┬────────┘       └────────┬─────────┘
         │                         │
         │ FK                      │ FK
         ▼                         ▼
┌─────────────────────────────────────────────┐
│              QualityQcFa                    │
│  table_type: QFA | QFC                      │
│  date_1, week, customer, team, line_code    │
│  po, style, batch, color_id, qty            │
│  seconds, accepted, rejected, sample        │
│  defects_total, aql, pass_or_fail           │
└────────────────────┬────────────────────────┘
                     │ 1:N
                     ▼
┌─────────────────────────────────────────────┐
│           InspectionDefect                   │
│  inspection_id (FK → QualityQcFa)           │
│  defect_type_id (FK → DefectType)           │
│  amount                                      │
│  UNIQUE(inspection, defect_type)             │
└─────────────────────────────────────────────┘


┌─────────────────────────────────────────────┐
│              SecondsA4                       │
│  year, week, date, cut_num, style           │
│  cut_qty, color_id, first_quality_qty_sewing│
│  sample, pass_field, fail_field             │
│  sew_def, fab_def, accepted, rejected       │
│  total_of_2ds, percentage_of_2ds            │
│  line, seconds_by_sew, seconds_by_fab       │
└─────────────────────────────────────────────┘


┌───────────────────────┐       ┌──────────────────────────┐
│   SecondsGeneral      │       │  SecondsGeneralDefectType│
│  date, week, team     │       │  (catálogo)              │
│  customer, style      │       └────────────┬─────────────┘
│  color, po, size      │                    │
│  produced, fixed      │                    │ FK
│  definitive           │                    │
└───────────┬───────────┘                    │
            │ 1:N                            │
            ▼                                │
┌────────────────────────────────────────────┴─┐
│         SecondsGeneralDefect                  │
│  seconds_general_id (FK)                      │
│  defect_type_id (FK)                          │
│  amount                                       │
│  UNIQUE(seconds_general, defect_type)         │
└───────────────────────────────────────────────┘


┌───────────────────────┐       ┌──────────────────────────┐
│     Container         │       │   ContainerDefectType    │
│  container_number     │       │   (catálogo)             │
│  date, customer       │       └────────────┬─────────────┘
│  total_palette        │                    │
│  total_palette_pass   │                    │ FK
│  total_palette_rejected│                   │
│  percentage_pass      │                    │
│  percentage_reject    │                    │
└───────────┬───────────┘                    │
            │ 1:N                            │
            ▼                                │
┌────────────────────────────────────────────┴─┐
│       ContainerInspectionDefect               │
│  container_id (FK)                            │
│  defect_type_id (FK)                          │
│  amount                                       │
│  UNIQUE(container, defect_type)               │
└───────────────────────────────────────────────┘


┌───────────────────────────────────────────────┐
│           ExcelSyncSession                     │
│  status: pending | confirmed | rejected        │
│  created_at                                    │
│  redis_stored: bool                            │
│  qc_fa_plant_data (JSON)                       │
│  qc_fa_customer_data (JSON)                    │
│  seconds_a4_data (JSON)                        │
│  seconds_general_data (JSON)                   │
│  container_data (JSON)                         │
│  *_preview (JSON) — diff summary per sheet     │
│  warnings (JSON)                               │
└───────────────────────────────────────────────┘
```

### Índices importantes

```python
# QualityQcFa
idx_qcfa_team_pof        → (week, team)
idx_qcfa_natural_lookup   → (table_type, date_1, po, style, team, color, line_code)

# SecondsGeneral
idx_sg_week              → (week)
```

### Datos seed (init_data_models.py)

El sistema precarga estos catálogos al iniciar:
- **36 colores** corporativos (athletic_orange, black, navy, etc.)
- **50 tipos de defectos** de confección (broken_stitch, loose_thread, etc.)
- **15 tipos de defectos** de contenedor (dirt_label, crushed_corners, etc.)

---

## 7. API Endpoints

### Autenticación (`/api/auth/`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/login/` | Login con email/password → JWT | No |
| GET | `/me/` | Usuario actual | Sí |
| POST | `/logout/` | Logout (no-op) | Sí |
| POST | `/token/refresh/` | Renovar access token | No |

### Excel Workflow (`/quality/excel/`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/preview/<filename>/` | Upload + preview sin persistir | Sí |
| POST | `/confirm/<session_id>/` | Confirmar y aplicar cambios | Sí |
| DELETE | `/reject/<session_id>/` | Rechazar preview | Sí |

### KPIs QC FA (`/quality/kpis/`)

Todos aceptan filtros: `date_range`, `week`, `team`, `style`, `color`, `customer`, `batch`, `context` (plant|customer).

| Endpoint | Descripción | Tipo de respuesta |
|----------|-------------|-------------------|
| `/aql-by-style/` | AQL por estilo | Bar chart data |
| `/aql-weekly/` | AQL semanal + tendencia | Line chart data |
| `/audited-pieces/` | Piezas auditadas por semana | Line chart data |
| `/ac-re-rate-by-line/` | PASS/REJECT por línea | Bar chart data |
| `/performance-by-customer/` | Performance por cliente | Bar chart data |
| `/performance-by-line/` | Performance por línea | Bar chart data |
| `/top-defects/` | Top defectos por cantidad | Bar chart data |
| `/fabric-defects/` | Defectos de tela | Bar chart data |
| `/defects-by-style-type/` | Heatmap estilo × defecto | Heatmap data |
| `/defect-composition/` | Composición de defectos (donut) | Donut chart data |
| `/defect-trend-top-3/` | Tendencia top 3 defectos | Line chart data |
| `/pass-reject-distribution/` | Distribución PASS/REJECT | Donut chart data |
| `/rejected-evolution/` | Evolución semanal de rechazos | Line chart data |
| `/defect-rate/` | Tasa global de defectos | Scalar |
| `/filter-options/` | Opciones dinámicas para filtros | Object |

### KPIs SecondsGeneral (`/quality/kpis/seconds-general/`)

| Endpoint | Descripción |
|----------|-------------|
| `/defects-by-customer/` | Defectos agrupados por cliente |
| `/defects-by-style/` | Defectos agrupados por estilo |
| `/weekly-trend/` | Tendencia semanal |
| `/sewing-vs-fabric/` | Costura vs Tela (donut) |

### KPIs SecondsA4 (`/quality/kpis/seconds-a4/`)

| Endpoint | Descripción |
|----------|-------------|
| `/pass-fail-weekly/` | Pass vs Fail por semana |
| `/defects-by-type/` | Defectos por tipo |
| `/acceptance-by-line/` | Aceptación por línea |
| `/weekly-volume/` | Volumen semanal |

### KPIs Container (`/quality/kpis/container/`)

| Endpoint | Descripción |
|----------|-------------|
| `/by-status/` | Contenedores por estado |
| `/defects-by-type/` | Defectos por tipo |
| `/weekly-trend/` | Tendencia semanal |
| `/customer-performance/` | Performance por cliente |

### Otros

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/kpis/volatile/` | KPIs en memoria (Fast Mode) |
| GET | `/kpis/containers-by-state/` | Contenedores por rango de % pass |
| GET | `/reports/corporate-xlsx/` | Descarga reporte Excel corporativo |

---

## 8. Flujo de Importación Excel

### Modo Live DB (persistente)

```
1. Usuario arrastra Excel → ExcelUploader
2. POST /quality/excel/preview/<filename>/
   ├── handler_service.load_and_clean() parsea cada sheet
   ├── sync_service.compute_diff() compara con DB
   ├── Crea ExcelSyncSession(status="pending")
   └── Retorna preview + warnings
3. Usuario revisa preview → Confirma o Rechaza
4a. POST /quality/excel/confirm/<session_id>/
    ├── sync_service.apply_timewindow() reemplaza datos
    ├── Crea InspectionDefects / SecondsGeneralDefects
    └── Actualiza session a "confirmed"
4b. DELETE /quality/excel/reject/<session_id>/
    └── Elimina session
```

### Modo Fast Mode (volátil)

```
1. Usuario arrastra Excel → ExcelUploader
2. Frontend envía archivo al backend como multipart
3. POST /quality/kpis/volatile/
   ├── handler_service.load_and_clean() parsea
   ├── volatile_kpi_service calcula TODOS los KPIs en memoria
   └── Retorna KPIs sin persistir nada
4. Frontend muestra dashboard con datos volátiles
```

### Configuración de sheets (sheet_configs.py)

Cada sheet del Excel tiene:
- **SHEET_NAMES**: Nombre de la sheet, fila de header, número de columnas
- **REMAP**: Mapeo columna Excel → campo Django
- **NUMERIC_COLUMNS**: Campos que deben parsearse como números
- **AMOUNT_DEFEACTS_FIELDS**: Campos de defectos (se convierten en InspectionDefect)

### Estrategia de sincronización (sync_service.py)

`apply_timewindow()` implementa reemplazo por ventana temporal:
1. Identifica el rango de fechas en los datos nuevos
2. Elimina registros existentes en ese rango
3. Inserta los nuevos registros
4. Para defectos: usa `_sync_defects_via_handler()` con canonical key matching

---

## 9. Sistema de KPIs y Dashboards

### Arquitectura de KPIs

```
                    ┌─────────────────────┐
                    │   Frontend kpi.js   │
                    │  fetchAllKpis()     │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   Backend Views     │
                    │  KpiFilterMixin     │
                    │  + queryset filters │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  Live DB     │ │  Volatile    │ │  Dashboard   │
     │  (queryset)  │ │  (pandas)    │ │  Assemblers  │
     └──────────────┘ └──────────────┘ └──────────────┘
```

### KpiFilterMixin

Todos los KPI views heredan de `KpiFilterMixin` que proporciona:
- Filtros comunes: `date_range`, `week`, `team`, `style`, `color`, `customer`, `batch`
- Filtro `context`: `plant` (QFA) o `customer` (QFC)
- Método `_resolve_context_table_type()` para aislar datos

### Volatile KPI Service

`volatile_kpi_service.py` calcula KPIs sin tocar la DB:
- Abre Excel con `pd.ExcelFile` una vez
- Parsea sheets on-demand via `load_and_clean()`
- Aplica filtros en memoria con `apply_volatile_filters()`
- Retorna los mismos DTOs que los endpoints live

### Dashboard Contracts

`dashboard_contracts.py` define los DTOs estandarizados:
- Formatos de respuesta para cada tipo de gráfico
- Labels de buckets para contenedores
- Contratos de serialización

### Dashboard Assemblers

`dashboard_assemblers.py` ensambla datos completos para dashboards:
- Combina múltiples KPIs en una sola respuesta
- Maneja la lógica de secciones (Excel Reports vs Rift Analytics Insights)

---

## 10. Autenticación y Autorización

### Flujo de autenticación

```
1. User → POST /api/auth/login/ {email, password}
2. Backend → CustomTokenObtainPairSerializer
   ├── Valida credenciales
   ├── Verifica que NO sea operator
   └── Retorna {access, refresh, role}
3. Frontend → Guarda tokens en localStorage
   ├── rift-access-token
   └── rift-refresh-token
4. Cada request → axiosClient interceptor agrega Authorization: Bearer <token>
5. 401 response → Interceptor despacha evento 'auth-unauthorized'
   └── AuthContext limpia tokens y redirige a login
```

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Configurable via env
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Configurable via env
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Roles

| Rol | Acceso | Estado |
|-----|--------|--------|
| `manager` | Todo (dashboard, excel, reports) | Activo |
| `operator` | (Deprecado) Rechazado en /me/ | Legacy |

### Bootstrap de usuarios

`bootstrap_auth_users` crea usuarios iniciales:
- Ejecuta `seed_auth_users` primero
- Luego intenta eliminar usuarios legacy con delete guardado (catch ProtectedError)
- En Docker se ejecuta automáticamente al iniciar

---

## 11. Docker y Entorno

### docker-compose.yml

4 servicios:

| Servicio | Imagen | Puerto | Dependencias |
|----------|--------|--------|--------------|
| `db` | postgres:16 | 5432 | — |
| `redis` | redis:7-alpine | 6379 | — |
| `backend` | Custom Dockerfile | 8000 | db (healthy), redis (healthy) |
| `frontend` | Custom Dockerfile | 5173 | db, backend |

### Backend startup sequence

```bash
1. python manage.py makemigrations
2. python manage.py migrate
3. python manage.py shell -c 'seed colors, defect types, container defect types'
4. python manage.py bootstrap_auth_users
5. daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

### Variables de entorno (.env)

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb

# Django
DJANGO_SECRET_KEY=tu-secret-key
DJANGO_DEBUG=True

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_SECRET_KEY=tu-jwt-secret
```

### Volúmenes

- `postgres_data_dev` — Persistencia de PostgreSQL
- `redis_data` — Persistencia de Redis
- `./backend:/app` — Montaje de código backend (hot reload)
- `./frontend:/app` — Montaje de código frontend (hot reload)

---

## 12. Testing

### Backend (pytest)

```bash
cd backend
pytest                    # Todos los tests
pytest --ignore=e2e       # Sin E2E (Playwright)
pytest -m unit            # Solo unit tests
pytest -m integration     # Solo integration tests
pytest --cov              # Con coverage
```

**Configuración**: `pytest.ini`
- `DJANGO_SETTINGS_MODULE = backend.settings`
- Tests usan SQLite in-memory (configurado en settings.py)
- Markers: `e2e`, `unit`, `integration`

**Estructura de tests**:
```
backend/
├── auth_data/tests/test_auth.py
├── quality_data/tests/
│   ├── test_kpis.py                    # KPIs principales
│   ├── test_volatile_kpis.py           # KPIs volátiles
│   ├── test_container_kpis.py          # KPIs de contenedor
│   ├── test_seconds_a4_analytics.py    # KPIs SecondsA4
│   ├── test_seconds_general_analytics.py # KPIs SecondsGeneral
│   ├── test_qc_context_filtering.py    # Filtros QFA/QFC
│   ├── test_dashboard_assemblers.py    # Ensambladores
│   ├── test_dashboard_contracts.py     # Contratos
│   ├── test_kpi_dto_serializers.py     # Serializers
│   ├── test_corporate_xlsx_service.py  # Reportes
│   ├── test_excel_v2_views.py          # Excel workflow
│   └── test_legacy.py                  # Tests legacy
├── excel_importer/tests/
│   ├── test_handler_service.py         # Parseo de Excel
│   ├── test_sync_service.py            # Sincronización
│   └── test_date_utils.py              # Normalización fechas
└── e2e/                                # Playwright (requiere browser)
```

### Frontend (Vitest)

```bash
cd frontend
npm run test              # Watch mode
npm run test:run          # Single run
npm run test:coverage     # Con coverage
```

**Configuración**: `vite.config.js` → `test` section
- Environment: jsdom
- Setup: `src/test/setup.js`
- Coverage: v8 provider

**Estructura de tests**:
```
frontend/src/
├── api/*.test.js                     # Tests de API layer
├── Components/**/*.test.jsx          # Tests de componentes
├── views/**/*.test.jsx               # Tests de views
├── views/dashboards/*.test.jsx       # Tests de dashboards
└── hooks/*.test.jsx                  # Tests de hooks
```

**Mocking**: MSW (Mock Service Worker) intercepta llamadas API en tests.
- Handlers: `src/test/msw/handlers.js`

---

## 13. Guía de Desarrollo

### Setup local

```bash
# 1. Clonar
git clone https://github.com/rurbinaa/Proyecto-Asignatura-Web.git
cd Proyecto-Asignatura-Web

# 2. Variables de entorno
cp backend/.env.example backend/.env

# 3. Levantar
docker compose up --build

# 4. Acceder
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/api/
```

### Desarrollo sin Docker

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Necesitas PostgreSQL y Redis corriendo localmente
python manage.py migrate
python manage.py bootstrap_auth_users
python manage.py runserver

# Frontend
cd frontend
bun install
bun run dev
```

### Agregar un nuevo KPI

1. **Backend**: Crear view en `quality_data/views/` heredando de `KpiFilterMixin`
2. **Backend**: Registrar URL en `quality_data/urls.py`
3. **Frontend**: Agregar función en `api/kpi.js`
4. **Frontend**: Crear componente de gráfico o reutilizar existente
5. **Frontend**: Agregar al dashboard correspondiente en `views/dashboards/`
6. **Tests**: Agregar tests backend y frontend

### Agregar un nuevo modelo

1. Crear modelo en `quality_data/models.py`
2. `python manage.py makemigrations`
3. `python manage.py migrate`
4. Agregar serializer si necesita API
5. Crear view + URL
6. Agregar al `sheet_configs.py` si se importa desde Excel
7. Tests

### Convenciones de código

**Backend (Python)**:
- Django conventions (PEP 8)
- Views organizadas por dominio (no todo en un archivo)
- Tests con pytest, no con unittest.TestCase
- Commits: conventional commits (`feat:`, `fix:`, `chore:`, `test:`)

**Frontend (JavaScript/JSX)**:
- Functional components con hooks
- NO class components
- Tests con Testing Library + Vitest
- CSS modules o CSS files alongside components
- Commits: conventional commits

---

## 14. Despliegue (Vercel + Railway)

### Frontend → Vercel

- Conectado al repo de GitHub
- Auto-deploy en push a `main`
- Preview deployments en PRs
- Build command: `bun run build`
- Output: `dist/`

### Backend → Railway

- Conectado al repo de GitHub
- Variables de entorno configuradas en Railway dashboard
- Usa PostgreSQL y Redis de Railway (no Docker)
- Start command: `daphne -b 0.0.0.0 -p $PORT backend.asgi:application`

### Variables de entorno en producción

```bash
# Railway (backend)
DJANGO_SECRET_KEY=<secret>
DJANGO_DEBUG=False
POSTGRES_URL=<railway-postgres-url>
REDIS_URL=<railway-redis-url>
JWT_SECRET_KEY=<jwt-secret>
ALLOWED_HOSTS=<railway-domain>

# Vercel (frontend)
VITE_API_URL=<railway-backend-url>
```

---

## 15. Decisiones de Arquitectura

### Por qué JWT y no sesiones

El backend es stateless. JWT permite escalar horizontalmente sin sticky sessions. El trade-off es que el logout es un no-op (no se puede invalidar el token server-side sin blacklist).

### Por qué pandas para Excel

Los archivos Excel de manufactura tienen formatos complejos (headers en filas intermedias, celdas mergeadas, datos mixtos). pandas + openpyxl maneja estos casos mucho mejor que librerías más simples.

### Por qué QFA/QFC comparten modelo

QC FA Plant y Customer tienen la misma estructura de datos. Se unificaron en un solo modelo `QualityQcFa` con campo `table_type` para evitar duplicación. El filtro `context=plant|customer` aísla los datos.

### Por qué Fast Mode

Los gerentes quieren "qué pasaría si" sin persistir datos. Fast Mode parsea el Excel en memoria y calcula KPIs al instante. El trade-off es que no hay historial.

### Por qué CSS Grid y no Masonry

Los dashboards usaban react-masonry-css pero se cambió a CSS Grid con `layoutRole` (metric/standard/wide/composed) para:
- Layout determinista (no depende del orden de render)
- Mejor control de responsive breakpoints
- Sin dependencia externa

---

## 16. Deuda Técnica Conocida

| Issue | Severidad | Descripción |
|-------|-----------|-------------|
| PR #42 es un mega-PR | Alta | ~37K líneas mezclando README, features, fixes, cleanup. Debería separarse. |
| Commits "muchas cosas" | Media | 2 commits con mensaje genérico. Dificulta bisecting. |
| media_data eliminada pero no limpiada | Baja | El app fue eliminado del routing pero los archivos CSV de datos siguen en raíz. |
| Operator role deprecado pero presente | Baja | El modelo UserProfile aún tiene 'operator' como choice. El código lo rechaza en /me/. |
| E2E tests no corren | Media | Playwright requiere browsers que no están en el entorno Docker. |
| date_1 es CharField | Media | Las fechas se almacenan como strings, no como DateField. Se normalizan con canonicalize_qc_fa_date(). |
| Tests con SQLite in-memory | Baja | Los tests usan SQLite aunque prod usa PostgreSQL. Puede causar diferencias sutiles. |

---

## 17. Glosario de Términos del Dominio

| Término | Significado |
|---------|-------------|
| **AQL** | Acceptable Quality Level — % máximo de defectos aceptable |
| **QC FA** | Quality Control Final Audit — Inspección final de calidad |
| **QFA** | QC FA Plant — Inspección en planta |
| **QFC** | QC FA Customer — Inspección del cliente |
| **Seconds** | Segundas piezas — prendas con defectos que requieren rework |
| **SecondsA4** | Segundas piezas por corte (formato A4) |
| **Seconds General** | Segundas piejas con detalle de defectos por tipo |
| **Defect Rate** | Tasa de defectos = defectos_total / sample |
| **Pass/Fail** | Resultado de inspección: PASS o FAIL |
| **Rework** | Reparación de prendas con defectos |
| **Sewing Defects** | Defectos de costura (picado, hilo suelto, etc.) |
| **Fabric Defects** | Defectos de tela (corrido, barre, manchas, etc.) |
| **Container** | Contenedor de empaque inspeccionado |
| **Palette** | Paleta/carga dentro de un contenedor |
| **Batch** | Lote de producción |
| **PO** | Purchase Order — Orden de compra |
| **Team** | Línea/equipo de producción (número) |
| **Line Code** | Código de línea de producción |
| **Fast Mode** | Modo volátil — KPIs sin persistir en DB |
| **Volatile** | Datos calculados en memoria, no guardados |
| **Time Window** | Ventana temporal para reemplazo de datos |

---

## 18. Workflows Detallados

### 18.1 Workflow de Importación Excel (Live DB)

Este es el flujo principal del sistema. Un manager sube un Excel con datos de calidad y el sistema lo procesa, valida, y persiste.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW IMPORTACIÓN EXCEL                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  DROP    │───▶│ ANALYZE  │───▶│ PREVIEW  │───▶│ CONFIRM  │              │
│  │  FILE    │    │ (parse)  │    │ (review) │    │ (persist)│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       │               │               │               ▼                    │
│       │               │               │          ┌──────────┐              │
│       │               │               │          │  REJECT  │              │
│       │               │               │          │ (delete) │              │
│       │               │               │          └──────────┘              │
│       ▼               ▼               ▼                                    │
│  ExcelUploader   ExcelPreviewView   ExcelConfirmView                       │
│  (frontend)      (backend)         (backend)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Paso 1: Upload (Frontend)

**Componente**: `ExcelUploader.jsx`
**Archivo**: `frontend/src/Components/ExcelUploader.jsx`

```jsx
// Estado del uploader
const [uploadState, setUploadState] = useState('idle');
// Estados posibles: idle → analyzing → preview_ready → confirming → success | error
```

**Acciones del usuario**:
1. Arrastra archivo .xlsx al dropzone (react-dropzone)
2. Selecciona archivo → muestra nombre y tamaño
3. Click en "Analyze" → dispara `handleAnalyze()`

**Código clave**:
```jsx
const handleAnalyze = async () => {
  setUploadState('analyzing');
  const result = await uploadForPreview(selectedFile);  // POST /quality/excel/preview/
  setSessionId(result.session_id);
  setPreviewStats(result.preview);
  setUploadState('preview_ready');
};
```

#### Paso 2: Preview (Backend)

**Endpoint**: `POST /quality/excel/preview/<filename>/`
**View**: `ExcelPreviewView` en `quality_data/views/__init__.py`
**Servicios involucrados**:
- `handler_service.load_and_clean()` — Parsea cada sheet
- `sync_service.compute_preview()` — Calcula diff contra DB

**Flujo interno del backend**:

```python
# 1. Recibe archivo multipart
file_obj = request.FILES['file']

# 2. Parsea cada sheet con load_and_clean()
for sheet_config in SHEET_NAMES:
    rows = load_and_clean(
        file_obj,
        remap_columns=REMAP,
        numeric_columns=NUMERIC_COLUMNS,
        defeacts_fields=AMOUNT_DEFEACTS_FIELDS,
        sheet=sheet_config[0],      # Nombre de la sheet
        header=sheet_config[1],     # Fila de header
        cols=sheet_config[2]        # Número de columnas
    )

# 3. Calcula preview (diff contra DB)
preview = compute_preview(rows, model_class)

# 4. Crea ExcelSyncSession con status="pending"
session = ExcelSyncSession.objects.create(
    status="pending",
    qc_fa_plant_data=rows_qfa,
    qc_fa_plant_preview=preview_qfa,
    # ... demás sheets
)

# 5. Retorna session_id + preview + warnings
return Response({
    "session_id": session.id,
    "status": "pending",
    "preview": { "qc_fa_plant": [...], ... },
    "warnings": [...]
})
```

**Función `load_and_clean()` en detalle** (`excel_importer/handler_service.py`):

```python
def load_and_clean(file_obj, remap_columns, numeric_columns, defeacts_fields, 
                   sheet, header, cols, excel_file=None):
    """
    1. Lee sheet del Excel con pd.read_excel()
    2. Remapea columnas (Excel names → Django field names)
    3. Convierte tipos numéricos (pd.to_numeric errors='coerce')
    4. Rellena NaN (0 para numéricos, "UNKNOWN" para texto)
    5. Filtra filas inválidas (PO != 0, etc.)
    6. Trunca CharFields que excedan max_length
    7. Retorna lista de dicts listos para persistir
    """
```

**Función `compute_preview()`**:

```python
def compute_preview(rows, model_class, **filters):
    """
    Compara filas parseadas contra DB existente.
    Retorna:
    - total_rows: filas en Excel
    - existing_rows: filas ya en DB
    - new_rows: filas a insertar
    - date_range: rango de fechas detectado
    """
```

#### Paso 3: Revisión del Preview (Frontend)

**Estado**: `uploadState === 'preview_ready'`

El usuario ve:
- Número de filas por sheet (QC FA Plant: 150, QC FA Customer: 80, etc.)
- Warnings si hay datos problemáticos
- Botones "Confirm" y "Cancel"

**UI del preview**:
```jsx
{uploadState === 'preview_ready' && (
  <div className="preview-panel">
    <h3>Preview</h3>
    <ul>
      <li>QC FA Plant: {previewStats.qc_fa_plant.length} rows</li>
      <li>QC FA Customer: {previewStats.qc_fa_customer.length} rows</li>
      <li>SecondsA4: {previewStats.seconds_a4.length} rows</li>
      <li>Seconds General: {previewStats.seconds_general.length} rows</li>
      <li>Container: {previewStats.container.length} rows</li>
    </ul>
    {apiError && <div className="warning">{apiError}</div>}
    <button onClick={handleConfirm}>Confirm Import</button>
    <button onClick={handleReject}>Cancel</button>
  </div>
)}
```

#### Paso 4a: Confirmar (Backend)

**Endpoint**: `POST /quality/excel/confirm/<session_id>/`
**View**: `ExcelConfirmView`

**Flujo interno**:

```python
@transaction.atomic  # Transacción atómica — todo o nada
def post(request, session_id):
    session = ExcelSyncSession.objects.get(id=session_id, status="pending")
    
    # 1. Resuelve colores (bulk create si no existen)
    color_map = _resolve_colors_batch(all_color_names)
    
    # 2. Aplica cada sheet con apply_timewindow()
    stats = {}
    for sheet_name, rows in session.get_all_data().items():
        if rows:
            sheet_stats = apply_timewindow(rows, model_class, color_map)
            stats[sheet_name] = sheet_stats
    
    # 3. Actualiza session a "confirmed"
    session.status = "confirmed"
    session.save()
    
    return Response({"session_id": session.id, "status": "confirmed", "stats": stats})
```

**Función `apply_timewindow()` en detalle** (`excel_importer/sync_service.py`):

```python
def apply_timewindow(rows, model_class, color_map, table_type=None):
    """
    Estrategia de sincronización por ventana temporal.
    
    1. Determina rango de fechas en los datos nuevos
    2. Elimina registros existentes en ese rango (DELETE ... WHERE date BETWEEN)
    3. Inserta nuevos registros (bulk_create)
    4. Para defectos: sync_defects_via_handler() con canonical key matching
    
    Retorna stats: {created: N, deleted: N, defects_created: N, ...}
    """
```

**Flujo de defectos** (`_sync_defects_via_handler()`):

```python
def _sync_defects_via_handler(rows, parent_model, defect_model, parent_filters, 
                               table_type=None, color_map=None):
    """
    1. Para cada fila con defectos > 0:
       a. Busca el parent record (QualityQcFa) usando canonical key
       b. Crea o actualiza InspectionDefect con amount
    2. Auto-seed DefectType si no existe (bulk_create ignore_conflicts)
    3. Retorna stats: {created: N, matched: N, unmatched: N}
    """
```

#### Paso 4b: Rechazar (Backend)

**Endpoint**: `DELETE /quality/excel/reject/<session_id>/`
**View**: `ExcelRejectView`

```python
def delete(request, session_id):
    session = ExcelSyncSession.objects.get(id=session_id, status="pending")
    session.delete()  # Elimina session y todos sus datos JSON
    return Response({"status": "rejected"})
```

#### Paso 5: Confirmación (Frontend)

**Estado**: `uploadState === 'success'`

```jsx
{uploadState === 'success' && (
  <div className="success-panel">
    <CheckCircle /> Import successful!
    <p>{importStats.total} rows processed</p>
    <button onClick={resetUploader}>Import Another</button>
  </div>
)}
```

---

### 18.2 Workflow de Fast Mode (Volatile KPIs)

Fast Mode permite al gerente ver KPIs sin persistir datos en la DB. Útil para "qué pasaría si".

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW FAST MODE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  DROP    │───▶│  SEND TO │───▶│ CALCULATE│───▶│ SHOW     │              │
│  │  FILE    │    │  BACKEND │    │ KPIs     │    │ DASHBOARD│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  ExcelUploader   POST /volatile/  volatile_      DashboardShell            │
│  (frontend)      (backend)        kpi_service    (frontend)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Paso 1: Upload y Envío

**Componente**: `ExcelUploader.jsx`

```jsx
const handleVolatileDashboard = () => {
  onVolatileDashboard(selectedFile);  // Pasa archivo al padre
};

// En App.jsx:
const handleVolatileDashboard = (file) => {
  setVolatileFile(file);
  setActiveView('dashboard');  // Cambia a vista dashboard
};
```

#### Paso 2: Cálculo de KPIs (Backend)

**Endpoint**: `POST /quality/kpis/volatile/`
**Servicio**: `volatile_kpi_service.py`

**Flujo interno**:

```python
class VolatileWorkbookService:
    def __init__(self, file_obj):
        # Abre Excel UNA VEZ con pd.ExcelFile
        self._excel_file = pd.ExcelFile(file_obj, engine='openpyxl')
    
    def get_parsed_data(self, dashboard, context=None):
        """
        Parsea sheet on-demand según dashboard solicitado.
        
        - "qcfa" + context="plant" → QC FA Plant rows
        - "qcfa" + context="customer" → QC FA Customer rows
        - "container" → Container rows
        - "seconds_a4" → SecondsA4 rows
        - "seconds_general" → Seconds General rows
        """
        if dashboard == "qcfa":
            if context == "customer":
                return load_and_clean(..., sheet="QC FA Customer", ...)
            else:
                return load_and_clean(..., sheet="QC FA Plant", ...)
        # ... demás dashboards
```

**Cálculo de KPIs**:

```python
def calculate_volatile_kpis(file_obj, context="plant", filters=None):
    """
    1. Crea VolatileWorkbookService(file_obj)
    2. Parsea sheets necesarios
    3. Aplica filtros en memoria (apply_volatile_filters)
    4. Calcula cada KPI con la misma lógica que los endpoints live
    5. Retorna dict con todos los KPIs
    """
    service = VolatileWorkbookService(file_obj)
    
    # KPIs de QC FA
    rows, defect_fields = service.get_parsed_data("qcfa", context=context)
    rows = apply_volatile_filters(rows, "qcfa", filters)
    
    kpis = {
        "aql_by_style": calc_aql_by_style(rows),
        "aql_weekly": calc_aql_weekly(rows),
        "audited_pieces": calc_audited_pieces(rows),
        # ... 14+ KPIs
    }
    
    return kpis
```

#### Paso 3: Recepción en Frontend

**Componente**: `DashboardShell.jsx`

```jsx
function DashboardShell({ volatileFile }) {
  const [activeSheet, setActiveSheet] = useState('plant');
  const isFastMode = Boolean(volatileFile);
  
  return (
    <div className="dashboard-shell">
      <nav className="dashboard-shell-tabs">
        {/* 5 tabs: Plant, Customer, Seconds A4, Seconds General, Container */}
      </nav>
      <Suspense fallback={<div>Loading...</div>}>
        <ActiveComponent 
          volatileFile={volatileFile} 
          isFastMode={isFastMode} 
        />
      </Suspense>
    </div>
  );
}
```

#### Paso 4: Dashboard en Modo Volatile

**Componente**: `QcfaKpiDashboard.jsx`

```jsx
function QcfaKpiDashboard({ context, volatileFile, isFastMode }) {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    async function loadKpis() {
      if (isFastMode && volatileFile) {
        // Modo volatile: calcula KPIs desde el archivo
        const result = await fetchVolatileKpis(volatileFile, context);
        setKpis(result);
      } else {
        // Modo live: fetch desde DB
        const result = await fetchAllKpis(context);
        setKpis(result);
      }
      setLoading(false);
    }
    loadKpis();
  }, [context, isFastMode, volatileFile]);
  
  // Renderiza 14 cards de KPI
  return (
    <div className="dashboard-section__grid">
      {kpis && buildExcelSection(kpis).map(card => (
        <KpiCard key={card.id} {...card} />
      ))}
    </div>
  );
}
```

---

### 18.3 Workflow de Autenticación

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW AUTENTICACIÓN                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  LOGIN   │───▶│  VALIDATE│───▶│  STORE   │───▶│  REDIRECT│              │
│  │  FORM    │    │  JWT     │    │  TOKENS  │    │  TO APP  │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  LoginView      POST /login/    localStorage     AppContent                │
│  (frontend)     (backend)       (frontend)       (frontend)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Paso 1: Login Form

**Componente**: `LoginView.jsx`

```jsx
function LoginView() {
  const { login } = useAuth();
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(credentials);
    if (!success) setError('Invalid credentials');
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="email" onChange={e => setCredentials({...credentials, email: e.target.value})} />
      <input type="password" onChange={e => setCredentials({...credentials, password: e.target.value})} />
      <button type="submit">Login</button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}
```

#### Paso 2: Validación JWT (Backend)

**Endpoint**: `POST /api/auth/login/`
**View**: `LoginView` (hereda de `TokenObtainPairView`)
**Serializer**: `CustomTokenObtainPairSerializer`

```python
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 1. Valida email + password con Django auth
        data = super().validate(attrs)
        
        # 2. Verifica que NO sea operator
        if self.user.profile.role == 'operator':
            raise PermissionDenied('Operator role is no longer supported.')
        
        # 3. Agrega role al token
        data['role'] = self.user.profile.role
        
        return data
```

#### Paso 3: Almacenamiento de Tokens (Frontend)

**Servicio**: `axiosClient.js`

```javascript
export const tokenStorage = {
  getAccessToken() {
    return localStorage.getItem('rift-access-token');
  },
  setTokens({ access, refresh }) {
    if (access) localStorage.setItem('rift-access-token', access);
    if (refresh) localStorage.setItem('rift-refresh-token', refresh);
  },
  clear() {
    localStorage.removeItem('rift-access-token');
    localStorage.removeItem('rift-refresh-token');
  },
};
```

#### Paso 4: Interceptor de Requests

**Archivo**: `axiosClient.js`

```javascript
// Request interceptor: agrega JWT a cada request
axiosClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: maneja 401 (token expirado)
axiosClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    return Promise.reject(error);
  }
);
```

#### Paso 5: Verificación de Sesión

**Componente**: `AuthContext.jsx`

```jsx
const checkSession = useCallback(async () => {
  if (!tokenStorage.getAccessToken()) {
    setUser(null);
    setLoading(false);
    return;
  }
  
  try {
    const userDto = await getCurrentUserRequest();  // GET /api/auth/me/
    setUser(userDto);
  } catch {
    tokenStorage.clear();
    setUser(null);
  } finally {
    setLoading(false);
  }
}, []);

// Ejecuta al montar el componente
useEffect(() => { checkSession(); }, [checkSession]);
```

---

### 18.4 Workflow de Dashboards (Live Mode)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW DASHBOARD LIVE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  SELECT  │───▶│  FETCH   │───▶│ TRANSFORM│───▶│  RENDER  │              │
│  │  TAB     │    │  KPIs    │    │  DATA    │    │  CHARTS  │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  DashboardShell   api/kpi.js     dashboardMetric   Recharts               │
│  (frontend)       (frontend)     Utils.js          (frontend)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Paso 1: Selección de Tab

**Componente**: `DashboardShell.jsx`

```jsx
const SHEETS = {
  plant: { label: 'QC FA Plant', Component: PlantDashboard },
  customer: { label: 'QC FA Customer', Component: CustomerDashboard },
  seconds_a4: { label: 'Seconds A4', Component: SecondsA4Dashboard },
  seconds_gen: { label: 'Seconds General', Component: SecondsGeneralDashboard },
  container: { label: 'Container', Component: ContainerDashboard },
};

// Renderiza tabs
<nav className="dashboard-shell-tabs" role="tablist">
  {Object.entries(SHEETS).map(([key, { label }]) => (
    <button
      key={key}
      role="tab"
      aria-selected={activeSheet === key}
      onClick={() => setActiveSheet(key)}
    >
      {label}
    </button>
  ))}
</nav>
```

#### Paso 2: Fetch de KPIs

**Archivo**: `api/kpi.js`

```javascript
export async function fetchAllKpis(context, filters = {}) {
  const endpoints = [
    fetchAqlByStyle(filters, context),
    fetchAqlWeekly(filters, context),
    fetchAuditedPieces(filters, context),
    fetchAcReRateByLine(filters, context),
    fetchPerformanceByCustomer(filters, context),
    fetchPerformanceByLine(filters, context),
    fetchTopDefects(filters, context),
    fetchDefectsByStyleType(filters, context),
    fetchDefectComposition(filters, context),
    fetchDefectTrendTop3(filters, context),
    fetchPassRejectDistribution(filters, context),
    fetchRejectedEvolution(filters, context),
    fetchDefectRate(filters, context),
    fetchFilterOptions(filters),
  ];
  
  // Fetch paralelo con Promise.all
  const results = await Promise.all(endpoints);
  
  return {
    aql_by_style: results[0],
    aql_weekly: results[1],
    // ... todos los KPIs
  };
}
```

**Función helper para construir URLs**:

```javascript
function buildQueryString(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        params.append(key, value.join(','));
      } else {
        params.append(key, value);
      }
    }
  });
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

function resolveKpiUrl(endpoint, filters = {}, context) {
  const allParams = { ...filters };
  if (context) allParams.context = context;
  return `/quality/kpis/${endpoint}/${buildQueryString(allParams)}`;
}
```

#### Paso 3: Transformación de Datos

**Archivo**: `views/dashboardMetricUtils.js`

```javascript
// Transforma datos del backend al formato que esperan los gráficos
export function transformAqlByStyle(data) {
  return data.map(item => ({
    name: item.label,
    value: item.value,
  }));
}

export function transformAqlWeekly(data) {
  return data.map(series => ({
    name: series.name,
    data: series.data.map(point => ({
      x: point.x,
      y: point.y,
    })),
  }));
}
```

**Archivo**: `Components/kpi/lineChartUtils.js`

```javascript
// Utilidades para gráficos de líneas
export function sortWeekLabels(labels) {
  return labels.sort((a, b) => {
    const weekA = parseInt(a.replace('W', ''));
    const weekB = parseInt(b.replace('W', ''));
    return weekA - weekB;
  });
}
```

#### Paso 4: Renderizado de Charts

**Componente**: `QcfaKpiDashboard.jsx`

```jsx
function QcfaKpiDashboard({ context }) {
  const [kpis, setKpis] = useState(null);
  const [filters, setFilters] = useState({});
  
  useEffect(() => {
    fetchAllKpis(context, filters).then(setKpis);
  }, [context, filters]);
  
  // Construye secciones de cards
  const excelSection = buildExcelSection(kpis);
  const riftSection = buildRiftSection(kpis);
  
  return (
    <>
      <FilterBar filters={filters} onFilterChange={setFilters} />
      
      <section className="dashboard-section">
        <h3>Original Excel Reports</h3>
        <div className="dashboard-section__grid">
          {excelSection.map(card => (
            <KpiCard key={card.id} {...card}>
              {card.type === 'bar' && <BarChartKpi data={card.data} />}
              {card.type === 'line' && <LineChartKpi data={card.data} />}
              {card.type === 'donut' && <DonutChartKpi data={card.data} />}
              {card.type === 'heatmap' && <HeatmapKpi data={card.data} />}
              {card.type === 'number' && <KpiNumberCard value={card.value} />}
            </KpiCard>
          ))}
        </div>
      </section>
      
      <section className="dashboard-section">
        <h3>Rift Analytics Insights</h3>
        <div className="dashboard-section__grid">
          {riftSection.map(card => (
            <KpiCard key={card.id} {...card} />
          ))}
        </div>
      </section>
    </>
  );
}
```

---

### 18.5 Workflow de Reportes Corporativos

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW REPORTES CORPORATIVOS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  SELECT  │───▶│  REQUEST │───▶│ GENERATE │───▶│ DOWNLOAD │              │
│  │  DATES   │    │  REPORT  │    │  XLSX    │    │  FILE    │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  DateRangePicker  GET /reports/  corporate_xlsx   Browser                  │
│  (frontend)       (backend)      _service.py      download                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Paso 1: Selección de Fechas

**Componente**: `QualityReportsView.jsx`

```jsx
function QualityReportsView() {
  const [dateRange, setDateRange] = useState({ from: '', to: '' });
  
  const handleGenerate = async () => {
    const blob = await downloadCorporateReport(dateRange.from, dateRange.to);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `QA_Report_${dateRange.from}_${dateRange.to}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <div>
      <DateRangePicker value={dateRange} onChange={setDateRange} />
      <button onClick={handleGenerate}>Generate Report</button>
    </div>
  );
}
```

#### Paso 2: Generación del Excel (Backend)

**Endpoint**: `GET /quality/reports/corporate-xlsx/?from_date=2026-01-01&to_date=2026-01-31`
**Servicio**: `corporate_xlsx_service.py`

**Flujo interno**:

```python
def generate_corporate_xlsx(from_date, to_date):
    """
    Genera Excel corporativo con 5 sheets:
    1. QC FA Plant (table_type="QFA")
    2. QC FA Customer (table_type="QFC")
    3. SecondsA4
    4. Seconds General
    5. Container
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    for config in CORPORATE_XLSX_EXPORT_CONFIG:
        sheet = workbook.add_worksheet(config["sheet_name"])
        
        # 1. Query datos filtrados por fecha
        queryset = get_filtered_queryset(config, from_date, to_date)
        
        # 2. Escribe headers
        for col, header in enumerate(config["columns"]):
            sheet.write(0, col, header)
        
        # 3. Escribe filas
        for row_idx, record in enumerate(queryset, start=1):
            for col_idx, field in enumerate(config["columns"]):
                value = getattr(record, field, "")
                sheet.write(row_idx, col_idx, value)
    
    workbook.close()
    output.seek(0)
    return output
```

**Configuración de export** (`sheet_configs.py`):

```python
CORPORATE_XLSX_EXPORT_CONFIG = [
    {
        "dataset": "qfa",
        "sheet_name": "QC FA Plant",
        "model": "QualityQcFa",
        "queryset_filters": {"table_type": "QFA"},
        "columns": QC_FA_PLANT_EXPORT_COLUMNS,
        "defect_columns": QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
    },
    # ... 4 más
]
```

---

### 18.6 Workflow de Filtros del Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW FILTROS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  USER    │───▶│  UPDATE  │───▶│  RE-FETCH│───▶│  RE-RENDER│             │
│  │  FILTER  │    │  STATE   │    │  KPIs    │    │  CHARTS   │             │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  FilterBar        useState        api/kpi.js       React                   │
│  (frontend)       (frontend)      (frontend)       re-render               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### FilterBar Component

**Archivo**: `Components/kpi/FilterBar.jsx`

```jsx
function FilterBar({ filters, onFilterChange }) {
  const [filterOptions, setFilterOptions] = useState(null);
  
  // Carga opciones al montar
  useEffect(() => {
    fetchFilterOptions().then(setFilterOptions);
  }, []);
  
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };
  
  return (
    <div className="filter-bar">
      <select onChange={e => handleChange('week', e.target.value)}>
        <option value="">All Weeks</option>
        {filterOptions?.week.map(w => <option key={w} value={w}>W{w}</option>)}
      </select>
      
      <select onChange={e => handleChange('team', e.target.value)}>
        <option value="">All Teams</option>
        {filterOptions?.team.map(t => <option key={t} value={t}>Team {t}</option>)}
      </select>
      
      <select onChange={e => handleChange('style', e.target.value)}>
        <option value="">All Styles</option>
        {filterOptions?.style.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
      
      <select onChange={e => handleChange('color', e.target.value)}>
        <option value="">All Colors</option>
        {filterOptions?.color.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
      
      <select onChange={e => handleChange('customer', e.target.value)}>
        <option value="">All Customers</option>
        {filterOptions?.customer.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
    </div>
  );
}
```

#### Backend Filter Processing

**Mixin**: `KpiFilterMixin` en `quality_data/views/__init__.py`

```python
class KpiFilterMixin:
    """
    Proporciona filtros comunes para todos los KPI views.
    
    Query params soportados:
    - date_range: "2026-01-01,2026-01-31"
    - week: "1,2,3"
    - team: "1,2"
    - style: "Style-1,Style-2"
    - color: "black,white"
    - customer: "Customer-X"
    - batch: "100,101"
    - context: "plant" | "customer"
    """
    
    def get_queryset_filters(self, request):
        filters = Q()
        
        if date_range := request.query_params.get('date_range'):
            from_date, to_date = date_range.split(',')
            filters &= Q(date_1__gte=from_date, date_1__lte=to_date)
        
        if week := request.query_params.get('week'):
            filters &= Q(week__in=week.split(','))
        
        if team := request.query_params.get('team'):
            filters &= Q(team__in=team.split(','))
        
        # ... más filtros
        
        return filters
```

---

### 18.7 Workflow de Bootstrap del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW BOOTSTRAP                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  DOCKER  │───▶│  MIGRATE │───▶│  SEED    │───▶│  CREATE  │              │
│  │  START   │    │  DB      │    │  DATA    │    │  USERS   │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│       ▼               ▼               ▼               ▼                    │
│  docker-compose   manage.py      manage.py       manage.py                 │
│  up --build       migrate        shell           bootstrap_auth_users      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Secuencia de Inicio (docker-compose.yml)

```yaml
backend:
  command: >
    sh -c "python manage.py makemigrations &&
           python manage.py migrate &&
           python manage.py shell -c '
             from quality_data.init_data_models import COMPANY_COLORS, GARMENT_DEFECT_TYPES, CONTAINER_DEFECT_TYPES;
             from quality_data.models import Color, DefectType, ContainerDefectType;
             [Color.objects.get_or_create(name=n, defaults={\"is_active\": True}) for n in COMPANY_COLORS];
             [DefectType.objects.get_or_create(name=n) for n in GARMENT_DEFECT_TYPES];
             [ContainerDefectType.objects.get_or_create(name=n) for n in CONTAINER_DEFECT_TYPES];
             print(\"DB seeded\")
           ' &&
           python manage.py bootstrap_auth_users &&
           daphne -b 0.0.0.0 -p 8000 backend.asgi:application"
```

#### Paso 1: Migraciones

```bash
python manage.py makemigrations  # Crea archivos de migración si hay cambios
python manage.py migrate         # Aplica migraciones a PostgreSQL
```

#### Paso 2: Seed Data

```python
# Colores corporativos (36 colores)
Color.objects.get_or_create(name="black", defaults={"is_active": True})
Color.objects.get_or_create(name="white", defaults={"is_active": True})
# ... 34 más

# Tipos de defectos de confección (50 tipos)
DefectType.objects.get_or_create(name="broken_stitch")
DefectType.objects.get_or_create(name="loose_thread")
# ... 48 más

# Tipos de defectos de contenedor (15 tipos)
ContainerDefectType.objects.get_or_create(name="dirt_label")
ContainerDefectType.objects.get_or_create(name="crushed_corners")
# ... 13 más
```

#### Paso 3: Bootstrap Users

**Comando**: `management/commands/bootstrap_auth_users.py`

```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Ejecuta seed_auth_users primero
        call_command('seed_auth_users')
        
        # 2. Elimina usuarios legacy con delete guardado
        legacy_users = User.objects.filter(
            username__in=['admin', 'test_user', 'demo_user']
        )
        
        for user in legacy_users:
            try:
                user.delete()  # Intenta eliminar
            except ProtectedError:
                # Si tiene FK protegidas, skip
                self.stdout.write(f"Skipped {user.username} (protected)")
            except Exception as e:
                # Cualquier otro error, skip
                self.stdout.write(f"Skipped {user.username} ({e})")
```

---

### 18.8 Workflow de Testing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW TESTING                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  BACKEND (pytest)                                                           │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  WRITE   │───▶│  RUN     │───▶│  CHECK   │───▶│  FIX     │              │
│  │  TEST    │    │  PYTEST  │    │  COVERAGE│    │  FAILURES│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│                                                                             │
│  FRONTEND (vitest)                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  WRITE   │───▶│  RUN     │───▶│  CHECK   │───▶│  FIX     │              │
│  │  TEST    │    │  VITEST  │    │  COVERAGE│    │  FAILURES│              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Backend Testing

```bash
# Ejecutar todos los tests
cd backend && pytest

# Ejecutar sin E2E (Playwright)
pytest --ignore=e2e

# Ejecutar solo unit tests
pytest -m unit

# Ejecutar con coverage
pytest --cov=quality_data --cov=excel_importer --cov-report=html

# Ejecutar tests específicos
pytest quality_data/tests/test_kpis.py::TestAqlByStyle
```

**Ejemplo de test backend**:

```python
# quality_data/tests/test_kpis.py
class TestAqlByStyle:
    """Tests for GET /quality/kpis/aql-by-style/"""
    
    def test_returns_data_for_plant_context(self, api_client, db):
        # Arrange: crear datos de prueba
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2026-01-15",
            week=3,
            customer="Customer-A",
            team=1,
            po=1001,
            style="Style-1",
            batch=1,
            color=Color.objects.create(name="black"),
            qty=100,
            seconds=5,
            accepted=95,
            rejected=5,
            sample=50,
            defects_total=3,
            aql=2.5,
            pass_or_fail="Pass"
        )
        
        # Act
        response = api_client.get('/quality/kpis/aql-by-style/?context=plant')
        
        # Assert
        assert response.status_code == 200
        assert len(response.data['data']) > 0
        assert response.data['data'][0]['label'] == "Style-1"
```

#### Frontend Testing

```bash
# Ejecutar en watch mode
cd frontend && npm run test

# Ejecutar una sola vez
npm run test:run

# Ejecutar con coverage
npm run test:coverage
```

**Ejemplo de test frontend**:

```jsx
// Components/kpi/BarChartKpi.test.jsx
import { render, screen } from '@testing-library/react';
import BarChartKpi from './BarChartKpi';

describe('BarChartKpi', () => {
  it('renders bars for each data point', () => {
    const data = [
      { name: 'Style-1', value: 10 },
      { name: 'Style-2', value: 20 },
    ];
    
    render(<BarChartKpi data={data} />);
    
    // Verifica que se renderizan las barras
    expect(screen.getByText('Style-1')).toBeInTheDocument();
    expect(screen.getByText('Style-2')).toBeInTheDocument();
  });
  
  it('shows loading state', () => {
    render(<BarChartKpi data={[]} loading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

**Mocking con MSW**:

```jsx
// test/msw/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/quality/kpis/aql-by-style/', () => {
    return HttpResponse.json({
      data: [
        { label: 'Style-1', value: 2.5 },
        { label: 'Style-2', value: 3.0 },
      ],
    });
  }),
  
  http.get('/quality/kpis/filter-options/', () => {
    return HttpResponse.json({
      week: [1, 2, 3],
      team: [1, 2],
      style: ['Style-1', 'Style-2'],
      color: ['black', 'white'],
      customer: ['Customer-A'],
      batch: [100, 101],
    });
  }),
];
```

---

## Documentación Adicional

- [Endpoints API](./docs/api/endpoints.md) — Contratos de todos los endpoints REST
- [Convenciones Git](./docs/general/conventions.md) — Branching, commits, flujo de trabajo
- [Modelo de Datos Backend](./docs/general/backend-plan.md) — Detalle de modelos y campos
- [Lógica de Sincronización](./docs/validation_logic.md) — Estrategias Time-Window y UPSERT
- [Docker Workflow](./docs/docker_workflow.md) — Comandos útiles para contenedores
- [Documentación de Tests](./docs/tests.md) — Suites, estructura, cómo ejecutar

---

> **Nota para devs que heredan este proyecto**: El código está bien estructurado pero el PR #42 es un mega-PR que mezcla todo. Si necesitas entender un cambio específico, busca por conventional commit message (`feat:`, `fix:`, `test:`). Los commits de "muchas cosas" son los únicos que no siguen la convención.
