# Rift Analytics (Proyecto Asignatura Web)

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)
![Django](https://img.shields.io/badge/Backend-Django_REST-092E20?logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)

Rift Analytics es una plataforma web para la digitalización y análisis de calidad (QA) en plantas de manufactura de confección textil. Permite a los gerentes cargar reportes Excel de inspección y visualizar KPIs de calidad en dashboards interactivos.

---

## Características Principales

- **Dashboard Interactivo**: KPIs en tiempo real (AQL, Defect Rate, Performance, Heatmaps) para toma de decisiones gerenciales.
- **Importación Excel**: Modo *Live DB* (persiste en PostgreSQL) y *Fast Mode* (volátil en memoria) para procesar reportes al instante.
- **5 Dashboards**: QC FA Plant, QC FA Customer, Seconds A4, Seconds General, Container.
- **Reportes Corporativos**: Generación de Excel con datos consolidados por rango de fechas.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend | React 19 + Vite + Recharts |
| Backend | Django 5 + DRF + SimpleJWT |
| Base de datos | PostgreSQL 16 |
| Cache | Redis 7 |
| Testing | pytest (backend) + Vitest (frontend) |
| Deploy | Vercel (frontend) + Railway (backend) |

---

## Guía de Instalación (Docker)

### Requisitos

1. [Git](https://git-scm.com/install/)
2. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (iniciado antes de avanzar)

### Paso 1: Clonar

```bash
git clone https://github.com/rurbinaa/Proyecto-Asignatura-Web.git
cd Proyecto-Asignatura-Web
```

### Paso 2: Variables de entorno

```bash
cp backend/.env.example backend/.env
```

Para desarrollo local, los valores preconfigurados del `.env.example` funcionan.

### Paso 3: Levantar servicios

```bash
docker compose up --build
```

La primera vez toma unos minutos mientras descarga dependencias.

### Paso 4: Acceder

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/

---

## Detener Servicios

```bash
docker compose down
```

Para borrar la base de datos y empezar de cero:

```bash
docker compose down -v
```

---

## Testing

**Backend (pytest):**
```bash
cd backend
pytest                    # Todos los tests (1,137 tests)
pytest --ignore=e2e       # Sin Playwright E2E
pytest -m unit            # Solo unit tests
```

**Frontend (Vitest):**
```bash
cd frontend
npm run test:run          # Single run (1,006 tests)
npm run test              # Watch mode
npm run test:coverage     # Con coverage
```

---

## Documentación Técnica

La documentación completa del proyecto está en [`PROJECT.md`](./PROJECT.md). Cubre:

- Arquitectura y stack tecnológico
- Modelos de base de datos y ERD
- Todos los endpoints API
- Workflows detallados (Excel import, Fast Mode, Auth, Dashboards, Filtros, Bootstrap, Testing)
- Guía de desarrollo y convenciones

Documentación adicional en [`/docs`](./docs/):

- [Endpoints API](./docs/api/endpoints.md)
- [Convenciones Git](./docs/general/conventions.md)
- [Modelo de Datos](./docs/general/backend-plan.md)
- [Sincronización Excel](./docs/validation_logic.md)
- [Docker Workflow](./docs/docker_workflow.md)
- [Documentación de Tests](./docs/tests.md)

---

## Estructura del Proyecto

```
Proyecto-Asignatura-Web/
├── backend/                  # Django + DRF
│   ├── auth_data/            # Autenticación JWT
│   ├── quality_data/         # KPIs, dashboards, modelos
│   ├── excel_importer/       # Parseo y sincronización Excel
│   └── backend/              # Configuración Django
├── frontend/                 # React + Vite
│   └── src/
│       ├── api/              # Capa de comunicación con backend
│       ├── views/            # Páginas y dashboards
│       ├── Components/       # Componentes reutilizables
│       └── contexts/         # Auth context
├── docs/                     # Documentación adicional
├── PROJECT.md                # Documentación técnica completa
└── docker-compose.yml        # 4 servicios: db, redis, backend, frontend
```
