# Documentación de Tests — Rift Analytics

> **Actualizado**: Mayo 2026
> **Backend**: 1,137 tests (pytest)
> **Frontend**: 1,006 tests (vitest)

---

## Resumen

| Suite | Runner | Tests | Estado |
|-------|--------|-------|--------|
| Backend | pytest | 1,137 | ✅ Passing |
| Frontend | vitest | 1,006 | ✅ Passing (4 skipped) |
| E2E | Playwright | 3 | ⚠️ Requiere browsers |
| **Total** | | **2,146** | |

---

## Backend (pytest)

### Ejecución

```bash
cd backend

# Todos los tests
pytest

# Sin E2E (Playwright)
pytest --ignore=e2e

# Solo unit tests (sin DB)
pytest -m unit

# Solo integration tests (con DB)
pytest -m integration

# Con coverage
pytest --cov=quality_data --cov=excel_importer --cov-report=html

# Tests específicos
pytest quality_data/tests/test_kpis.py::TestAqlByStyle

# Verbose
pytest -v
```

### Configuración

**Archivo**: `backend/pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = backend.settings
python_files = tests.py test_*.py *_tests.py
base_url = http://localhost:5173
markers =
    e2e: End-to-end tests using Playwright (requires running app)
    unit: Fast unit tests (no DB required)
    integration: Tests that require database access
```

**Base de datos**: Los tests usan SQLite in-memory (configurado en `settings.py`):

```python
if 'test' in sys.argv or any('pytest' in arg for arg in sys.argv):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

### Estructura de tests

```
backend/
├── auth_data/tests/
│   └── test_auth.py                    # Login, JWT, roles, bootstrap
├── quality_data/tests/
│   ├── test_kpis.py                    # KPIs principales (AQL, performance, defectos)
│   ├── test_volatile_kpis.py           # KPIs volátiles (Fast Mode)
│   ├── test_container_kpis.py          # KPIs de contenedor
│   ├── test_seconds_a4_analytics.py    # KPIs SecondsA4
│   ├── test_seconds_general_analytics.py # KPIs SecondsGeneral
│   ├── test_qc_context_filtering.py    # Filtros QFA/QFC
│   ├── test_dashboard_assemblers.py    # Ensambladores de dashboard
│   ├── test_dashboard_contracts.py     # Contratos de DTO
│   ├── test_kpi_dto_serializers.py     # Serializers de KPI
│   ├── test_corporate_xlsx_service.py  # Reportes corporativos
│   ├── test_excel_v2_views.py          # Excel workflow (preview/confirm/reject)
│   └── test_legacy.py                  # Tests legacy
├── excel_importer/tests/
│   ├── test_handler_service.py         # Parseo de Excel
│   ├── test_sync_service.py            # Sincronización (upsert + timewindow)
│   └── test_date_utils.py              # Normalización de fechas
└── e2e/
    ├── test_dashboard.py               # E2E dashboard (Playwright)
    ├── test_excel_import.py            # E2E import (Playwright)
    └── test_navigation.py              # E2E navigation (Playwright)
```

### Ejemplo de test backend

```python
# quality_data/tests/test_kpis.py
import pytest
from quality_data.models import QualityQcFa, Color

@pytest.mark.django_db
class TestAqlByStyle:
    """Tests for GET /quality/kpis/aql-by-style/"""
    
    def test_returns_data_for_plant_context(self, api_client):
        # Arrange
        color = Color.objects.create(name="black")
        QualityQcFa.objects.create(
            table_type="QFA",
            date_1="2026-01-15",
            week=3,
            customer="Customer-A",
            team=1,
            po=1001,
            style="Style-1",
            batch=1,
            color=color,
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
    
    def test_empty_db_returns_empty_data(self, api_client):
        response = api_client.get('/quality/kpis/aql-by-style/?context=plant')
        assert response.status_code == 200
        assert response.data['data'] == []
```

### Ejemplo de test de sync

```python
# excel_importer/tests/test_sync_service.py
import pytest
from excel_importer.sync_service import apply_timewindow, apply_upsert

@pytest.mark.django_db
class TestApplyTimewindow:
    def test_replaces_records_in_date_range(self):
        # Arrange: crear registros existentes
        # Act: apply_timewindow con nuevos datos
        # Assert: registros reemplazados correctamente
    
    def test_handles_canonical_date_matching(self):
        # Arrange: crear registros con fechas legacy "01/15/2026"
        # Act: apply_timewindow con fechas ISO "2026-01-15"
        # Assert: matching correcto por fecha canónica

@pytest.mark.django_db
class TestApplyUpsert:
    def test_inserts_new_records(self):
        # Arrange: DB vacía
        # Act: apply_upsert con datos
        # Assert: registros creados
    
    def test_updates_existing_records(self):
        # Arrange: crear registros existentes
        # Act: apply_upsert con datos modificados
        # Assert: registros actualizados
```

---

## Frontend (vitest)

### Ejecución

```bash
cd frontend

# Watch mode (desarrollo)
npm run test

# Single run (CI)
npm run test:run

# Con coverage
npm run test:coverage
```

### Configuración

**Archivo**: `frontend/vite.config.js`

```javascript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary', 'html'],
      include: ['src/**/*.{js,jsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.test.*',
        'src/main.jsx',
      ],
    },
  }
})
```

### Estructura de tests

```
frontend/src/
├── api/
│   ├── auth.test.js                    # Tests de API auth
│   ├── axiosClient.test.js             # Tests de interceptors
│   ├── excel.test.js                   # Tests de API Excel
│   ├── kpi.test.js                     # Tests de API KPIs
│   └── reports.test.js                 # Tests de API reports
├── Components/
│   ├── DateRangePicker.test.jsx
│   ├── ExcelUploader.test.jsx
│   ├── Navbar.test.jsx
│   ├── ReportGenerator.test.jsx
│   ├── Sidebar.test.jsx
│   └── kpi/
│       ├── BarChartKpi.test.jsx
│       ├── ContainerFilterBar.test.jsx
│       ├── DonutChartKpi.test.jsx
│       ├── FilterBar.test.jsx
│       ├── HeatmapKpi.test.jsx
│       ├── KpiCard.test.jsx
│       ├── KpiNumberCard.test.jsx
│       ├── LineChartKpi.test.jsx
│       └── lineChartUtils.test.js
├── views/
│   ├── LoginView.test.jsx
│   ├── DashboardShell.test.jsx
│   ├── dashboardMetricUtils.test.js
│   ├── useVolatileDashboardCache.test.js
│   └── dashboards/
│       ├── ContainerDashboard.test.jsx
│       ├── CustomerDashboard.test.jsx
│       ├── PlantDashboard.test.jsx
│       ├── QcfaKpiDashboard.test.jsx
│       ├── SecondsA4Dashboard.test.jsx
│       └── SecondsGeneralDashboard.test.jsx
├── contexts/
│   └── AuthContext.test.jsx
└── hooks/
    └── withRoleProtection.test.jsx
```

### Mocking con MSW

Los tests usan Mock Service Worker para interceptar llamadas API:

```javascript
// src/test/msw/handlers.js
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Auth
  http.post('/api/auth/login/', () => {
    return HttpResponse.json({
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      role: 'manager',
    });
  }),
  
  http.get('/api/auth/me/', () => {
    return HttpResponse.json({
      id: 1,
      email: 'manager@test.com',
      role: 'manager',
      is_manager: true,
    });
  }),
  
  // KPIs
  http.get('/quality/kpis/aql-by-style/', () => {
    return HttpResponse.json({
      data: [{ label: 'Style-1', value: 2.5 }],
    });
  }),
  
  // Filter options
  http.get('/quality/kpis/filter-options/', () => {
    return HttpResponse.json({
      week: [1, 2, 3],
      team: [1, 2],
      style: ['Style-1'],
      color: ['black'],
      customer: ['Customer-A'],
      batch: [100],
    });
  }),
];
```

### Ejemplo de test frontend

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
    
    expect(screen.getByText('Style-1')).toBeInTheDocument();
    expect(screen.getByText('Style-2')).toBeInTheDocument();
  });
  
  it('shows loading state', () => {
    render(<BarChartKpi data={[]} loading={true} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
  
  it('shows error state', () => {
    render(<BarChartKpi data={[]} error="Failed to load" />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });
});
```

### Ejemplo de test de dashboard

```jsx
// views/dashboards/QcfaKpiDashboard.test.jsx
import { render, screen, waitFor } from '@testing-library/react';
import QcfaKpiDashboard from './QcfaKpiDashboard';

describe('QcfaKpiDashboard', () => {
  it('renders KPI cards after loading', async () => {
    render(<QcfaKpiDashboard context="plant" />);
    
    // Espera a que carguen los KPIs
    await waitFor(() => {
      expect(screen.getByText('AQL by Style')).toBeInTheDocument();
    });
  });
  
  it('renders with volatile file in fast mode', async () => {
    const mockFile = new File([''], 'test.xlsx');
    render(<QcfaKpiDashboard context="plant" volatileFile={mockFile} isFastMode={true} />);
    
    await waitFor(() => {
      expect(screen.getByText('AQL by Style')).toBeInTheDocument();
    });
  });
});
```

---

## E2E (Playwright)

### Ejecución

```bash
cd backend

# Requiere Playwright browsers instalados
playwright install chromium

# Ejecutar E2E
pytest e2e/
```

### Tests E2E

```python
# e2e/test_dashboard.py
def test_filter_bar_visible(page):
    """Verifica que la barra de filtros es visible en el dashboard."""
    page.goto("http://localhost:5173")
    # Login
    page.fill('input[type="email"]', 'manager@test.com')
    page.fill('input[type="password"]', 'password')
    page.click('button[type="submit"]')
    # Verificar filtro
    expect(page.locator('.filter-bar')).to_be_visible()
```

### Estado actual

Los tests E2E requieren browsers de Playwright que no están instalados en el entorno Docker. Para ejecutarlos localmente:

```bash
# Instalar browsers
playwright install chromium

# Ejecutar
pytest e2e/ --browser chromium
```

---

## Coverage

### Backend

```bash
cd backend
pytest --cov=quality_data --cov=excel_importer --cov=auth_data --cov-report=html
# Abre htmlcov/index.html
```

### Frontend

```bash
cd frontend
npm run test:coverage
# Abre coverage/index.html
```

---

## Convenciones de Tests

### Backend

- Usar `pytest` fixtures, no `unittest.TestCase`
- Usar `@pytest.mark.django_db` para tests que necesitan DB
- Usar `@pytest.mark.unit` para tests sin DB
- Nombres descriptivos: `test_returns_empty_when_no_data`
- Arrange → Act → Assert

### Frontend

- Usar `describe` + `it` (vitest)
- Usar `@testing-library/react` para render
- Usar `screen.getByText`, `screen.getByRole` para queries
- Mockear API con MSW handlers
- Tests junto al componente que testea: `Component.test.jsx`

---

## CI/CD

Los tests corren automáticamente en:

- **Backend**: GitHub Actions (pytest)
- **Frontend**: Vercel Preview (vitest run)
- **PR checks**: Vercel deploy preview + test run

---

## Troubleshooting

### Tests fallan por DB

```bash
# Limpiar DB de test
rm -f backend/.pytest_cache/v/cache/lastfailed
pytest --create-db
```

### Tests fallan por import

```bash
# Verificar que el path está correcto
cd backend && python -c "import quality_data"
```

### Frontend tests fallan por MSW

```bash
# Verificar handlers
cd frontend && npm run test:run -- --reporter=verbose
```
