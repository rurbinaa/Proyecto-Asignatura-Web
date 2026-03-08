# Plan de Desarrollo Backend (Django / DRF)

Este documento detalla la estrategia de implementación para el backend del proyecto **Uniwell Apparel**, basado en el análisis de los archivos Excel históricos, el BRIEF de requerimientos (RF-002, RF-004) y el modelo de datos unificado.

## 1. Patrón Arquitectónico y Stack
* **Framework:** Django con Django REST Framework (DRF) para exponer las APIs hacia el frontend en Vite/React.
* **Base de Datos:** PostgreSQL (recomendado para producción) ya que maneja de forma muy eficiente las consultas de agrupación para analíticas y mapas de calor (JSONB y cálculos geoespaciales si en el futuro se requirieran). Para desarrollo, SQLite es suficiente.
* **Autenticación:** JSON Web Tokens (JWT) mediante `djangorestframework-simplejwt`.

## 2. Sugerencia de Arquitectura de Aplicaciones (Django Apps)
Para mantener un código limpio y escalable, se sugiere dividir el backend en las siguientes aplicaciones (mediante el comando `python manage.py startapp <nombre>`):

### A. `users` (Gestión de Usuarios y Accesos)
* **Modelos:** Heredar de `AbstractUser` para crear la entidad `User`.
* **Propósito:** Manejar roles (Inspector, Supervisor, Gerente), turnos (`Shift`), email y credenciales. 
* **Endpoints:** Login (Token), Registro, Perfil.

### B. `catalogs` (Datos Maestros y Estáticos)
* **Modelos:** `Customer`, `ProductionLine`, `DefectCategory`, `DefectType`, `Style`, `PurchaseOrder`.
* **Propósito:** Agrupar todos los catálogos de los que dependen las inspecciones. Rara vez se eliminan, frecuentemente se leen.
* **Endpoints:** CRUD completo para gestionar líneas nuevas, nuevos clientes, o añadir tipos de defectos (Catálogos necesarios para los selectores del frontend).

### C. `qc` (Quality Control & Inspections)
* **Modelos:** `Inspection`, `InspectionDefect`.
* **Propósito:** Es el núcleo transaccional. Manejará tanto la ingesta masiva (Excel) como la captura táctil en planta.
* **Endpoints y Servicios:** 
  * `POST /api/qc/inspections/excel-upload/`: Subida de archivos (Ver sección dinámica).
  * `POST /api/qc/inspections/`: Creación desde la app táctil, procesando DTOs.
  * `GET /api/qc/analytics/`: Endpoints especializados en agrupar métricas (AQL Promedio, Defecto más común, Reportes para mapas de calor).

### D. `logistics` (Auditoría de Contenedores)
* **Modelos:** `ContainerAudit`, `ContainerDefect`.
* **Propósito:** Desacoplar las métricas de prendas (QC) de las métricas de embarque/tarimas. 
* **Endpoints:** Registro de validación de contenedores y defectos logísticos (etiquetas sucias, cajas rotas).

---

## 3. Estrategia de Ingesta de Datos 

### Ingesta Masiva mediante Excel (RF-002)
Dado que los datos de control de calidad llevan años almacenados en el archivo Excel `QA Data report 2025.xlsx`:

1. **Herramienta:** Usar la librería `pandas` instalada en tu entorno de Python dentro de un servicio o utilitario propio en Django (ej. `services/excel_processor.py`).
2. **Método:** 
   * **Transacciones Atómicas:** Todo el archivo debe leerse dentro de un bloque `with transaction.atomic():`. Si hay un error de validación en la fila 200, los cambios se revierten para no dejar la base de datos "a medias".
   * **Resolución Relacional (`get_or_create`):** El script leerá, por ejemplo, el cliente "Grunt Style". Verificará si existe en el catálogo `Customer`; si no, lo creará al vuelo. Igual con el código de "Estilo", las "Líneas", etc.
   * **Transposición (Unpivot):** Transformar las columnas horizontales de defectos del Excel a filas verticales para su guardado en `InspectionDefect` con `DefectCount = X` y coordenadas `X/Y = null`.

### Ingesta por Interfaz Táctil (RF-004)
Este flujo exige el registro de defectos puntuales y dibujados sobre la prenda:

1. **DTOs Combinados (Nested Serializers):** El frontend enviará un JSON con la data consolidada de la inspección y un "array" con cada defecto detectado.
2. **Estructura Esperada del JSON:**
   ```json
   {
       "inspector_id": 4,
       "purchase_order": "PO-123",
       "quantity": 100,
       "sample_size": 20,
       "defects": [
           {
               "defect_type_id": 12,
               "coordinate_x": 45.2,
               "coordinate_y": 12.8,
               "image": "base64_or_file...",
               "comment": "Costura abierta en axila derecha"
           }
       ]
   }
   ```
3. El serializador de `Inspection` capturará los `defects` e insertará por cada objeto un registro a la vez con `DefectCount = 1`, preservando las coordenadas para renderizar posteriormente el heat-map.

---

## 4. Endpoints y Analíticas Claves (Consultas Sugeridas)

Para alimentar los Dashboards (reportes ejecutivos interactivos a responder en < 3 segundos según el BRIEF), deberás aprovechar el `ORM` de Django usando `annotate()` y `aggregate()`:

* **Top 5 Defectos Más Frecuentes:**
  ```python
  InspectionDefect.objects.values('DefectType_Id__Name') \
  .annotate(total=Sum('DefectCount')) \
  .order_by('-total')[:5]
  ```
* **Comportamiento y Evolución de Calidad por Lote:** Graficar líneas de tendencia filtrando el parámetro `Week` (Semana) alojado de forma nativa en la tabla de Inspección.
* **Data de Mapa de Calor:**
  ```python
  InspectionDefect.objects.filter(
      Inspection_Id__Style_Id=estilo_id, 
      Coordinate_X__isnull=False
  ).values('Coordinate_X', 'Coordinate_Y', 'DefectType_Id__Name')
  ```

## 5. Próximos pasos a seguir

1. Definir los modelos en los respectivos ficheros `models.py` según el Excalidraw / PlantUML.
2. Ejecutar `python manage.py makemigrations` y `python manage.py migrate`.
3. Crear el script pre-poblador de base de datos (`seed.py` o *management command*) que consuma tu `QA Data report 2025.xlsx` local y genere la data inicial de prueba de los años en curso.
4. Generar la carpeta `serializers.py` en cada lógica para exponer la API REST.
