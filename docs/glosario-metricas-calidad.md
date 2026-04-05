# Glosario de Métricas de Calidad (KPIs)

Este documento define formalmente la lógica de cálculo de cada Key Performance Indicator (KPI) utilizado en el Dashboard de Calidad, con el objetivo de evitar ambigüedades durante las auditorías y estandarizar los criterios de evaluación.

---

## 1. Métricas de AQL (Acceptable Quality Limit)

### Tasa de Defectos Global (Defect Rate)
- **Definición**: Porcentaje total de defectos sobre la muestra auditada en el período o filtro seleccionado.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `(Σ Total Defectos / Σ Muestra) * 100`

### AQL por Estilo
- **Definición**: Nivel de calidad agrupado por el estilo del producto.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `(Σ Total Defectos del Estilo / Σ Muestra del Estilo) * 100`

### Evolución Semanal de AQL
- **Definición**: Comportamiento histórico del AQL semana a semana, con cálculo de línea de tendencia interpolada.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `(Σ Total Defectos por Semana / Σ Muestra por Semana) * 100`

### Piezas Auditadas
- **Definición**: Volumen de producción sujeto a revisión de calidad por semana.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `Σ Muestra (Sample)` agrupado por semana.

---

## 2. Rendimiento Operativo (Performance)

### Rendimiento por Cliente (Performance by Customer)
- **Definición**: Tasa de aceptación de las piezas auditadas por cliente. Se excluyen del cálculo los clientes con muestra igual a cero.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `(Σ Piezas Aceptadas / Σ Muestra) * 100`

### Rendimiento por Línea (Performance by Line)
- **Definición**: Tasa de aceptación agrupada por línea de producción (team).
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `(Σ Piezas Aceptadas por Equipo / Σ Muestra por Equipo) * 100`

### Tasa de Aceptación / Rechazo por Línea
- **Definición**: Volumen absoluto de lotes o corridas que fueron Aprobadas (PASS) o Rechazadas (REJECT), discriminadas por línea.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: Conteo absoluto de registros `COUNT` agrupados por `Team` (Línea) y Estado (`pass_or_fail`).

### Segundas por Reproceso (Costuras vs Tela)
- **Definición**: Tiempo en segundos invertido en reprocesar prendas por defectos, separado por origen del defecto (Costura vs Tela).
- **Origen de datos**: Hoja "Seconds A4" (Tabla `SecondsA4`).
- **Fórmula de Cálculo**: `Σ Segundos por Costura` vs `Σ Segundos por Tela` agrupado por semana.

---

## 3. Análisis de Defectos y Rechazos

### Top 10 Defectos
- **Definición**: Los defectos más recurrentes en términos de cantidad absoluta de piezas afectadas.
- **Origen de datos**: Hoja "QC FA Plant" (campos numéricos de defectos) y Tabla `InspectionDefect`.
- **Fórmula de Cálculo**: Sumatoria simple de la cantidad reportada para cada categoría de defecto. Ordenado de mayor a menor.

### Defectos por Estilo y Tipo (Heatmap)
- **Definición**: Mapa de calor que cruza el volumen de los "Top 5 Estilos" con los "Top 5 Tipos de Defectos".
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa` y `InspectionDefect`).
- **Fórmula de Cálculo**: Sumatoria de la cantidad de defectos `(Σ Amount)` cruzando las variables Estilo (Eje X) y Tipo de Defecto (Eje Y).

### Evolución de Rechazos
- **Definición**: Evolución temporal del volumen absoluto de piezas rechazadas por semana.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: `Σ Piezas Rechazadas (Rejected)` agrupadas por semana.

### Distribución Aprobado / Rechazado
- **Definición**: Distribución porcentual global de los lotes en estado PASS vs REJECT.
- **Origen de datos**: Hoja "QC FA Plant" (Tabla `QualityQcFa`).
- **Fórmula de Cálculo**: Conteo porcentual de registros agrupado por estado final.

### Defectos de Tela (Fabric Defects)
- **Definición**: Distribución de las principales fallas de origen textil (Corrido, Barre, Degradación, Bordados, Otros).
- **Origen de datos**: Hoja "Seconds General" (Tabla `SecondsGeneral` / Pivots del Excel).
- **Fórmula de Cálculo**: Sumatorias por color de cada categoría de falla textil.

---

## 4. Contenedores

### Contenedores por Estado (Porcentaje de Pase)
- **Definición**: Segmentación del estado de calidad general de los contenedores según su porcentaje histórico de aprobación.
- **Origen de datos**: Hoja "Container" (Tabla `Container`).
- **Agrupación (Rangos)**:
  - < 80% (Crítico)
  - 80% - 90% (Riesgo)
  - 90% - 95% (Aceptable)
  - > 95% (Óptimo)
- **Fórmula de Cálculo**: Conteo absoluto de contenedores cuyo `percentage_pass` entra en cada rango.