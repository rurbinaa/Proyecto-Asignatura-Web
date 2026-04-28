# Lógica Técnica del Proceso de Validación y Prevención de Duplicados

Este documento explica la lógica técnica implementada para validar datos y prevenir la inserción de duplicados en la base de datos durante el proceso de importación de archivos Excel.

## Arquitectura General

El sistema utiliza un enfoque de "inserción incremental" para evitar duplicados. En lugar de verificar cada fila individualmente contra la base de datos (lo cual sería ineficiente para grandes volúmenes de datos), el sistema asume que:

1. Los datos en el Excel están ordenados cronológicamente
2. Las nuevas filas se agregan al final del archivo
3. No se modifican filas existentes en el medio del archivo

## Función `_get_incremental_rows`

### Ubicación
`backend/quality_data/views.py`, líneas 35-42

### Código
```python
def _get_incremental_rows(df, model_class, **filters):
    db_rows = model_class.objects.filter(**filters).count()
    df_rows = len(df)
    rows_to_insert = max(df_rows - db_rows, 0)

    if rows_to_insert == 0:
        return df.iloc[0:0]

    return df.tail(rows_to_insert).copy()
```

### Lógica de Funcionamiento

1. **Conteo de Filas Existentes**: Se cuenta el número de registros existentes en la base de datos para el modelo específico, aplicando filtros opcionales (ej. `table_type="QFA"` para distinguir entre QC FA Plant y QC FA Customer).

2. **Cálculo de Filas Nuevas**: Se calcula la diferencia entre el número de filas en el DataFrame (`df_rows`) y el número de filas en la base de datos (`db_rows`).

3. **Selección de Filas**: Si hay más filas en el DataFrame que en la base de datos, se seleccionan las últimas `rows_to_insert` filas usando `df.tail(rows_to_insert)`.

4. **Caso de No Inserción**: Si `rows_to_insert` es 0 o negativo, se devuelve un DataFrame vacío.

### Ejemplo de Funcionamiento

**Escenario Inicial:**
- Base de datos: 100 filas para QC FA Plant
- Excel: 120 filas para QC FA Plant
- Resultado: Se insertan las últimas 20 filas (filas 101-120)

**Escenario de Re-importación del Mismo Archivo:**
- Base de datos: 120 filas para QC FA Plant
- Excel: 120 filas para QC FA Plant
- Resultado: No se inserta nada (DataFrame vacío)

## Aplicación por Tabla

### QualityQcFa (QC FA Plant y QC FA Customer)
- **Filtro**: `table_type="QFA"` para Plant, `table_type="QFC"` para Customer
- **Razón**: Ambas tablas usan el mismo modelo pero se distinguen por el tipo de tabla

### SecondsA4, SecondsGeneral, Container
- **Filtro**: Ninguno (conteo total de filas)
- **Razón**: Cada modelo es único y no requiere distinción adicional

## Ventajas de Este Enfoque

1. **Eficiencia**: Evita consultas individuales por fila, reduciendo significativamente el tiempo de procesamiento para grandes datasets.

2. **Simplicidad**: No requiere índices únicos complejos en la base de datos.

3. **Asunción Realista**: En entornos de producción, los datos de calidad típicamente se agregan cronológicamente sin modificaciones retroactivas.

## Limitaciones y Consideraciones

1. **Asunción de Orden**: Si se insertan filas en posiciones intermedias del Excel, podrían crearse duplicados.

2. **No Detecta Modificaciones**: Si se modifican valores en filas existentes, no se actualizarán en la base de datos.

3. **Dependencia de Conteo**: El método depende de que el conteo de filas en la DB sea preciso y no haya eliminaciones intermedias.

## Validación Adicional

### Truncamiento de Campos de Texto
- **Función**: `_truncate_charfields` en `handler_service.py`
- **Propósito**: Previene errores de `DataError` al truncar strings que exceden la longitud máxima de campos VARCHAR.
- **Lógica**: Para cada campo CharField con `max_length`, trunca el valor si es un string.

### Limpieza de Datos
- **Función**: `load_and_clean` en `handler_service.py`
- **Validaciones**:
  - Conversión de tipos (numéricos a float/int, texto a string)
  - Relleno de valores nulos (0 para numéricos, "UNKNOWN" para texto)
  - Normalización de campos específicos (ej. "pass_or_fail" a "Pass"/"Fail")
  - Filtrado de filas inválidas (ej. PO != 0)

## Recomendaciones para Futuros Desarrolladores

1. **Monitoreo**: Implementar logging detallado para rastrear cuántas filas se insertan en cada importación.

2. **Backup**: Realizar backups antes de importaciones masivas.

3. **Validación Manual**: Para casos críticos, considerar validación manual de las primeras importaciones.

4. **Índices**: Agregar índices en campos frecuentemente filtrados para mejorar rendimiento del conteo.

5. **Alternativas**: Si el orden de los datos no puede garantizarse, considerar implementar verificación por hash o campos únicos específicos.</content>
<parameter name="filePath">/home/frandev/Documentos/Proyecto-Asignatura-Web/docs/validation_logic.md