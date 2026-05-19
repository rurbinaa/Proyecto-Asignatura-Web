# Rift Analytics (Proyecto Asignatura Web)

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)
![Django](https://img.shields.io/badge/Backend-Django_REST-092E20?logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)

Rift Analytics es una plataforma web integral diseñada para la digitalización, captura y análisis de calidad (QA) en plantas de manufactura. Permite registrar y analizar datos de inspección, cargar archivos Excel, consultar indicadores de calidad y visualizar dashboards interactivos para apoyar la toma de decisiones gerenciales.

## Características principales

- **Dashboard interactivo de calidad**: KPIs en tiempo real como AQL, tasa de defectos, rendimiento por línea/cliente, defectos principales, distribución de aprobación/rechazo y tendencias.
- **Importación masiva desde Excel**: permite cargar archivos `.xlsx` con datos de calidad para procesarlos, previsualizarlos y confirmarlos en la base de datos.
- **Fast Mode / Modo Volátil**: genera dashboards directamente desde un archivo Excel sin guardar los datos permanentemente.
- **Autenticación con JWT**: inicio de sesión con usuarios tipo `manager` y manejo de sesión mediante tokens.
- **Trazabilidad y auditoría**: estructura preparada para analizar inspecciones de calidad relacionadas con tela, costura, empaque y contenedores.
- **Reportes**: generación de reportes corporativos en formato Excel.

## Documentación adicional

- [Glosario de Métricas de Calidad](./docs/glosario-metricas-calidad.md)
- [Manual del Dashboard para Gerencia](./docs/manual-dashboard-gerencia.md)
- [Estructura de Archivos Excel](./docs/excel_structure.md)
- [Endpoints de API](./docs/api/endpoints.md)

## Tecnologías utilizadas

- **Frontend**: React + Vite
- **Backend**: Django + Django REST Framework
- **Autenticación**: JWT con `djangorestframework-simplejwt`
- **Base de datos**: PostgreSQL
- **Cache / servicios auxiliares**: Redis
- **Servidor ASGI**: Daphne
- **Contenedores**: Docker y Docker Compose
- **Procesamiento Excel**: Pandas, OpenPyXL y XlsxWriter

## Estructura general del proyecto

```text
Proyecto-Asignatura-Web/
├── backend/              # API Django REST
├── frontend/             # Aplicación React/Vite
├── docs/                 # Documentación técnica y funcional
├── docker-compose.yml    # Orquestación de servicios Docker
├── README.md
└── .gitignore
```

## Guía de instalación con Docker

El proyecto está dockerizado para que todos los desarrolladores puedan ejecutar el mismo entorno de forma consistente.

### Requisitos previos

1. Git
2. Docker Desktop
3. Docker Compose (normalmente incluido en Docker Desktop)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/rurbinaa/Proyecto-Asignatura-Web.git
cd Proyecto-Asignatura-Web
```

### Paso 2: Configurar variables de entorno

Crea el archivo `.env` dentro de la carpeta `backend`:

```bash
cp backend/.env.example backend/.env
```

Valores mínimos recomendados para desarrollo local:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
```

> Nota: el archivo `.env` no se sube a GitHub por seguridad.

### Paso 3: Levantar los servicios

Desde la raíz del proyecto ejecuta:

```bash
docker compose up --build
```

La primera vez puede tardar varios minutos porque Docker debe descargar imágenes e instalar dependencias.

El `docker-compose.yml` levanta los siguientes servicios:

- PostgreSQL en el puerto `5432`
- Redis en el puerto `6379`
- Backend Django/Daphne en el puerto `8000`
- Frontend React/Vite en el puerto `5173`

Durante el arranque, el backend ejecuta automáticamente:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py bootstrap_auth_users
```

Esto crea las tablas necesarias, carga datos base y genera usuarios iniciales de desarrollo.

### Paso 4: Acceder a la plataforma

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Auth: http://localhost:8000/api/auth/
- API Calidad: http://localhost:8000/quality/

## Acceso inicial

Al iniciar el proyecto con Docker, se crean usuarios de prueba automáticamente.

**Credenciales principales:**

- Email: `gerente@uniwell.com`
- Password: `password123`
- Rol: `manager`

**Otros usuarios disponibles:**

- `gerencia@uniwell.com`
- `manager@uniwell.com`
- `admin@uniwell.com`
- `GERENCIA@uniwell.com`

> Nota: el rol `operator` ya no está habilitado para iniciar sesión. El sistema actualmente trabaja con usuarios tipo `manager`.

## Flujo básico de uso

1. Abrir http://localhost:5173
2. Iniciar sesión con un usuario `manager`
3. Ir al módulo de importación de Excel
4. Subir un archivo `.xlsx` compatible
5. Revisar la previsualización de datos
6. Confirmar la importación para guardar en base de datos o usar Fast Mode para análisis temporal
7. Consultar los dashboards de calidad
8. Aplicar filtros por línea, cliente, estilo, color u otros criterios disponibles
9. Exportar reportes si aplica

Para conocer el formato requerido del archivo Excel, revisar: `docs/excel_structure.md`

## Modos de importación Excel

### Live DB / Persistente

Procesa el archivo Excel, permite previsualizar los datos y luego confirmarlos para guardarlos en la base de datos PostgreSQL.

Flujo general:

`Subir Excel -> Previsualizar -> Confirmar -> Guardar en base de datos -> Consultar dashboards`

### Fast Mode / Volátil

Procesa el archivo Excel en memoria sin guardar los datos de forma permanente.

Flujo general:

`Subir Excel -> Procesar en memoria -> Ver dashboards -> Descartar datos al finalizar`

## Endpoints principales

La documentación completa de endpoints está disponible en `docs/api/endpoints.md`

**Endpoints destacados:**

```text
POST   /api/auth/login/
GET    /api/auth/me/
POST   /api/auth/logout/
POST   /api/auth/token/refresh/

POST   /quality/excel/preview/<filename>/
POST   /quality/excel/confirm/<session_id>/
DELETE /quality/excel/reject/<session_id>/

GET    /quality/kpis/filter-options/
POST   /quality/kpis/volatile/
GET    /quality/reports/corporate-xlsx/
```

## Detener los servicios

Para detener los contenedores sin eliminar los datos persistidos:

```bash
docker compose down
```

Para detener los contenedores y eliminar los volúmenes, incluyendo la base de datos local:

```bash
docker compose down -v
```

> Usa `docker compose down -v` solo si quieres reiniciar la base de datos desde cero.

## Pruebas

El proyecto cuenta con pruebas para backend y frontend.

### Backend

```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run test:run
```

También puedes ejecutar:

```bash
npm run test
npm run test:coverage
npm run lint
```

## Ejecución manual sin Docker

La forma recomendada es usar Docker. Sin embargo, también se puede ejecutar manualmente.

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_auth_users
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend consume el backend en `http://localhost:8000`

Esta URL está configurada en `frontend/src/api/axiosClient.js`

## Archivos que no se suben a GitHub

Por seguridad y buenas prácticas, no se versionan:

- `node_modules/`
- `.env`
- `*.env`
- `db.sqlite3`
- `*.xlsx`
- `dist/`
- `coverage/`
- `.cache/`

Esto significa que cada desarrollador debe instalar dependencias y crear su propio archivo `.env`.

## Notas para entrega o transferencia

Si se entrega este proyecto a otra persona o empresa, se recomienda enviar el repositorio de GitHub y no una carpeta completa con dependencias locales.

No incluir:

- `node_modules`
- `.env`
- `db.sqlite3` con datos reales
- Archivos Excel privados
- Carpetas de build o cobertura

Para ponerlo en marcha:

```bash
git clone https://github.com/rurbinaa/Proyecto-Asignatura-Web.git
cd Proyecto-Asignatura-Web
cp backend/.env.example backend/.env
docker compose up --build
```
