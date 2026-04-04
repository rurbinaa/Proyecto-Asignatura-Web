# Manual de Usuario: Dashboard de Calidad para Gerencia

Este manual detalla cómo utilizar e interpretar las visualizaciones del nuevo Dashboard Interactivo para la toma rápida de decisiones en Planta.

---

## 1. Modos de Acceso al Dashboard

El sistema cuenta con dos formas de acceder a la información de los KPIs, diseñadas para distintas necesidades operativas.

### Modo En Vivo (Dashboard Central)
- **Acceso:** Desde el menú lateral izquierdo haciendo clic en **"Dashboard"**.
- **Función:** Muestra los datos históricos y consolidados almacenados en la base de datos de la planta (Live DB).
- **Ideal para:** Reuniones mensuales, auditorías y generación de reportes consolidados.

### Modo Rápido (Volátil In-Memory)
- **Acceso:** Desde el menú **"Import Batches"** (Subir Excel). Una vez que seleccione su archivo de inspección de calidad (Excel), haga clic en el botón **"Ver Dashboard (Modo Rápido)"**.
- **Función:** Procesa inmediatamente el archivo Excel en la memoria del navegador y genera el Dashboard al instante, sin guardar los datos en el sistema.
- **Ideal para:** Revisión inmediata del lote de producción actual, validación visual de un archivo antes de autorizar su carga, o reportes rápidos "On the fly".

---

## 2. Cómo Utilizar los Filtros

En la parte superior del Dashboard encontrará la Barra de Filtros interactiva. Estos filtros permiten aislar el origen de un problema específico:

1. **Rango de Fechas**: Permite visualizar un bloque temporal específico.
2. **Semana (Week)**: Seleccione semanas calendario de producción.
3. **Línea (Team)**: Aísla el rendimiento de una línea de ensamblaje o equipo particular.
4. **Estilo (Style)** y **Color**: Útiles para detectar problemas en referencias específicas de producción.
5. **Cliente (Customer)**: Permite observar el rendimiento o tasa de rechazo asociado a un comprador.
6. **Lote (Batch)**: Seguimiento granular.

**Nota**: Todos los gráficos se actualizarán **automáticamente** al aplicar o remover un filtro. El Título del Dashboard cambiará para indicar qué filtros están activos actualmente.

---

## 3. Interpretación Rápida de los Gráficos

El Dashboard agrupa la información en cuatro secciones o grupos estratégicos:

### Grupo 1: KPIs AQL (Acceptable Quality Limit)
- **AQL Semanal (Líneas y Tendencia)**: Muestra dos líneas; la línea continua representa la tasa de defectos de la semana (AQL) y la punteada (Trend) predice la tendencia direccional (si los defectos van en alza o baja). **Meta:** Mantener el valor AQL lo más cercano a 0%.
- **Piezas Auditadas (Barras)**: Sirve como contexto volumétrico. Una semana con alto AQL es más crítica si el volumen auditado también fue alto.

### Grupo 2: KPIs de Rendimiento (Performance)
- **Rendimiento por Cliente / Línea (Barras Horizontales)**: Cuanto más extensa sea la barra, mayor será la tasa de aceptación. **Meta:** Lograr barras superiores al 95%.
- **Segundas por Reproceso (Líneas)**: Separa los minutos invertidos en rehacer prendas por errores de Tela (Fabric) vs errores de Costura (Sewing). Una brecha grande entre ambas indica en qué área del proceso se debe invertir en capacitación.

### Grupo 3: KPIs de Defectos (Identificación de Causa Raíz)
- **Top 10 Defectos (Barras Horizontales)**: El gráfico más crítico para acción correctiva inmediata (Pareto). Los 3 primeros defectos suelen representar el 80% de los problemas de calidad.
- **Defectos de Tela (Donut / Anillo)**: Distribución del tipo de falla en materia prima.
- **Defectos por Estilo y Tipo (Heatmap / Mapa de Calor)**: Cruza el estilo de la prenda con el tipo de defecto. **Cómo leerlo:** Los cuadros más oscuros (azul intenso) representan la intersección más problemática. Ej: "El Estilo X siempre falla por Hilo Suelto".

### Grupo 4: KPIs Operativos
- **Contenedores por Estado (Anillo)**: Provee una radiografía del inventario despachable.
  - **Verde**: > 95% (Saludable)
  - **Amarillo/Naranja**: 80-95% (Alerta de revisión)
  - **Rojo**: < 80% (Cuarentena)
- **Tasa de Defectos (Defect Rate)**: El KPI "Norte" global. Resume en un único porcentaje la salud de la planta para la selección actual de filtros.

---

## 4. Tip de Gerencia (Generación de Reportes Visuales)

Si necesita exportar este análisis para una presentación ejecutiva:
1. Filtre la información utilizando la barra superior (ej. `Semana: 12`, `Línea: 4`).
2. Espere a que el título confirme "Filtros Activos".
3. Tome una captura de pantalla del "Grupo 3" (Top Defectos + Heatmap) para justificar acciones correctivas en piso, y del "Grupo 2" (Rendimiento por Línea) para justificar reconocimientos a equipos de trabajo.