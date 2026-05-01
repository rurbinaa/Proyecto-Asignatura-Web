## Auth

### 1. POST /api/auth/login/
**Descripción**: Login con email y password. Rechaza explícitamente el rol `operator`.
**Body JSON**
```json
{
  "email": "manager1@uniwell.com",
  "password": "********"
}
```
**Respuesta JSON**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "role": "manager"
}
```

### 2. GET /api/auth/me/
**Descripción**: Devuelve el usuario autenticado actual. Si el perfil es `operator`, responde 403.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "id": 1,
  "email": "manager1@uniwell.com",
  "first_name": "Ana",
  "last_name": "Perez",
  "role": "manager",
  "is_manager": true,
  "is_operator": false
}
```

### 3. POST /api/auth/logout/
**Descripción**: Logout stateless sobre JWT. No invalida tokens del lado servidor.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "detail": "Successfully logged out."
}
```

### 4. POST /api/auth/token/refresh/
**Descripción**: Renueva el access token usando SimpleJWT.
**Body JSON**
```json
{
  "refresh": "jwt_refresh_token"
}
```
**Respuesta JSON**
```json
{
  "access": "new_jwt_access_token"
}
```

## Excel workflow

### 5. POST /quality/process/<filename>/
**Descripción**: Endpoint legacy de validación previa del Excel. Mantiene compatibilidad hacia atrás.
**Body JSON**: `N/A` (multipart/form-data con campo `file`)
**Respuesta JSON**: `N/A` (HTTP 204 sin contenido)

### 6. POST /quality/excel/preview/<filename>/
**Descripción**: Sube el Excel y devuelve un preview sin persistir cambios.
**Body JSON**: `N/A` (multipart/form-data con campo `file`)
**Respuesta JSON**
```json
{
  "session_id": 123,
  "status": "pending",
  "preview": {
    "qc_fa_plant": [],
    "qc_fa_customer": [],
    "seconds_a4": [],
    "seconds_general": [],
    "container": []
  },
  "warnings": []
}
```

### 7. POST /quality/excel/confirm/<session_id>/
**Descripción**: Confirma un preview pendiente y aplica los cambios.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "session_id": 123,
  "status": "confirmed",
  "message": "Changes applied successfully"
}
```

### 8. DELETE /quality/excel/reject/<session_id>/
**Descripción**: Rechaza un preview pendiente sin aplicar cambios.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "session_id": 123,
  "status": "rejected",
  "message": "Session rejected, no changes applied"
}
```

## KPI dashboard

### 9. GET /quality/kpis/aql-by-style/
**Descripción**: AQL por estilo. Soporta filtros `date_range`, `week`, `team`, `style`, `color`, `customer`, `batch`.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "Style-1", "value": 2.5}
  ]
}
```

### 10. GET /quality/kpis/aql-weekly/
**Descripción**: Serie semanal de AQL con línea de tendencia. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "AQL", "data": [{"x": 1, "y": 2.5}]},
    {"name": "Trend", "data": [{"x": 1, "y": 2.5}]}
  ]
}
```

### 11. GET /quality/kpis/audited-pieces/
**Descripción**: Piezas auditadas por semana. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "Pieces", "data": [{"x": 1, "y": 100}]}
  ]
}
```

### 12. GET /quality/kpis/ac-re-rate-by-line/
**Descripción**: Conteo PASS/REJECT por línea. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "1 - PASS", "value": 45}
  ]
}
```

### 13. GET /quality/kpis/seconds-rework/
**Descripción**: Segundos de rework por semana para sewing y fabric. Soporta `date_range`.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "Sewing", "data": [{"x": 1, "y": 12.3}]},
    {"name": "Fabric", "data": [{"x": 1, "y": 5.6}]}
  ]
}
```

### 14. GET /quality/kpis/performance-by-customer/
**Descripción**: Performance por cliente. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "Customer X", "value": 92.5}
  ]
}
```

### 15. GET /quality/kpis/performance-by-line/
**Descripción**: Performance por línea. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "Line 1", "value": 95.2}
  ]
}
```

### 16. GET /quality/kpis/top-defects/
**Descripción**: Top defects por suma de amount. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "Loose Thread", "value": 234}
  ]
}
```

### 17. GET /quality/kpis/fabric-defects/
**Descripción**: Defectos de tela agregados desde `SecondsGeneral`. Soporta `date_range` y `week`.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"label": "Corrido", "value": 45},
    {"label": "Barre", "value": 23}
  ]
}
```

### 18. GET /quality/kpis/defects-by-style-type/
**Descripción**: Heatmap estilo × defecto. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"x": "Style-1", "y": "Loose Thread", "value": 45}
  ]
}
```

### 19. GET /quality/kpis/pass-reject-distribution/
**Descripción**: Distribución PASS/REJECT. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "PASS", "value": 85},
    {"name": "REJECT", "value": 15}
  ]
}
```

### 20. GET /quality/kpis/rejected-evolution/
**Descripción**: Evolución semanal de rejected. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "Rejected", "data": [{"x": 1, "y": 23}]}
  ]
}
```

### 21. GET /quality/kpis/containers-by-state/
**Descripción**: Contenedores por rango de `percentage_pass`. Soporta `customer` y rango por `date_range` o `from_date`/`to_date`.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "data": [
    {"name": "< 80%", "value": 3},
    {"name": "80-90%", "value": 12},
    {"name": "90-95%", "value": 8},
    {"name": "> 95%", "value": 4}
  ]
}
```

### 22. GET /quality/kpis/defect-rate/
**Descripción**: Tasa global de defectos. Soporta los mismos filtros que arriba.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "label": "Defect Rate",
  "value": 2.34
}
```

### 23. POST /quality/kpis/volatile/
**Descripción**: Calcula KPIs en memoria desde un Excel sin persistir en DB.
**Body JSON**: `N/A` (multipart/form-data con campo `file`)
**Respuesta JSON**
```json
{
  "aql_by_style": [],
  "aql_weekly": [],
  "audited_pieces": [],
  "ac_re_rate_by_line": [],
  "seconds_rework": null,
  "performance_by_customer": [],
  "performance_by_line": [],
  "top_defects": [],
  "fabric_defects": null,
  "defects_by_style_type": [],
  "pass_reject_distribution": [],
  "rejected_evolution": [],
  "containers_by_state": null,
  "defect_rate": {"label": "Defect Rate", "value": 0},
  "filter_options": {
    "week": [],
    "team": [],
    "style": [],
    "color": [],
    "customer": [],
    "batch": []
  }
}
```

### 24. GET /quality/kpis/filter-options/
**Descripción**: Devuelve opciones dinámicas para filtros del dashboard.
**Body JSON**: `N/A`
**Respuesta JSON**
```json
{
  "week": [1, 2],
  "team": [1, 2],
  "style": ["Style-1"],
  "color": ["red"],
  "customer": ["Customer X"],
  "batch": [100, 101]
}
```

## Reports

### 25. GET /quality/reports/corporate-xlsx/
**Descripción**: Genera el reporte corporativo XLSX para un rango de fechas. Requiere `from_date` y `to_date`.
**Body JSON**: `N/A`
**Respuesta JSON**: `N/A` (descarga binary XLSX, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)

## Legacy removed from routing

- `media_data` ya no está montado en `backend/backend/urls.py`, así que las rutas de captura/bridge (`/api/v1/inspections/*`, `/api/v1/defects/*`, `/api/v1/close_inspection/*`) no forman parte del contrato vigente.
