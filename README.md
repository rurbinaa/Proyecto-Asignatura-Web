# Rift Analytics (Proyecto Asignatura Web)

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)
![Django](https://img.shields.io/badge/Backend-Django_REST-092E20?logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)

Rift Analytics es una plataforma web integral diseñada para la digitalización, captura y análisis de calidad (QA) en plantas de manufactura. Permite a los operadores registrar defectos en tiempo real (Touch Capture) y a la gerencia auditar el rendimiento mediante un **Dashboard de Calidad Interactivo** y la carga masiva de lotes vía Excel.

---

## 📋 Características Principales

- **Dashboard Interactivo de Calidad**: KPIs en tiempo real (AQL, Tasa de Defectos, Rendimiento por Línea/Cliente, Heatmaps de Defectos, etc.) para toma de decisiones gerenciales.
- **Importación Masiva (Excel Sync)**: Modos *Live DB* (persistencia) y *Fast Mode* (volátil en memoria) para procesar reportes de calidad al instante.
- **Touch Capture**: Interfaz para operadores en piso de planta para captura rápida de defectos.
- **Trazabilidad y Auditoría**: Arquitectura de base de datos preparada para manejar cruces de inspecciones de tela, costura y empaque.

Para más detalles operativos, consulta la documentación en `/docs`:
- [Glosario de Métricas de Calidad](./docs/glosario-metricas-calidad.md)
- [Manual del Dashboard para Gerencia](./docs/manual-dashboard-gerencia.md)

---

## 🚀 Guía de Instalación (Entorno Docker)

El proyecto está dockerizado para garantizar que todos los desarrolladores tengan el mismo entorno de ejecución.

### Requisitos Previos
1. **[Git](https://git-scm.com/install/)**: Para clonar el repositorio.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: Motor de contenedores (Asegúrate de iniciarlo antes de avanzar).

### Paso 1: Clonar el Repositorio
Abre tu terminal y ejecuta:
```bash
git clone https://github.com/rurbinaa/Proyecto-Asignatura-Web.git
cd Proyecto-Asignatura-Web
```

### Paso 2: Configurar Variables de Entorno
Crea una copia del archivo `.env.example` y renómbralo a `.env`. Este archivo contiene las credenciales de base de datos y configuración del proyecto.
```bash
cp .env.example .env
```
*(Nota: Para el desarrollo local inicial, puedes mantener los valores preconfigurados del `.env.example`).*

### Paso 3: Levantar los Servicios
Construye las imágenes e inicia los contenedores. La primera vez tomará un par de minutos mientras se descargan las dependencias (Node, Python, PostgreSQL, etc.).
```bash
docker compose up --build
```

### Paso 4: Acceder a la Plataforma
Una vez que la terminal indique que los servicios de React y Django están corriendo, accede desde tu navegador:
- 💻 **Frontend (Interfaz de Usuario)**: [http://localhost:5173](http://localhost:5173)
- ⚙️ **Backend (API REST)**: [http://localhost:8000/api/](http://localhost:8000/api/)

---

## 🛑 Detener los Servicios

Para detener los contenedores de forma segura **sin perder los datos de tu base de datos**, abre una nueva terminal en la raíz del proyecto (o presiona `Ctrl + C` en la terminal que corre los logs) y ejecuta:
```bash
docker compose down
```
*(Si en algún momento necesitas borrar la base de datos y empezar de cero, puedes usar `docker compose down -v`).*

---

## 🧪 Pruebas (Testing)

El proyecto cuenta con suites de pruebas tanto en Frontend (Vitest) como en Backend (Pytest).

**Backend (Django):**
```bash
cd backend
pytest
```

**Frontend (React):**
```bash
cd frontend
npm run test:run
```