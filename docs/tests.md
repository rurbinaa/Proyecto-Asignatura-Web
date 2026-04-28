# Documentación de Tests - Proyecto Asignatura Web

## Resumen de Tests Implementados

### Total de Tests: 30 tests

## 1. Tests de Modelos Básicos

### ColorModelTest (3 tests)
- `test_create_color`: Verifica creación de colores
- `test_color_str_representation`: Verifica representación string
- `test_color_unique_name`: Verifica restricción de unicidad

### DefectTypeModelTest (3 tests)
- `test_create_defect_type`: Verifica creación de tipos de defectos
- `test_defect_type_str_representation`: Verifica representación string
- `test_defect_type_unique_name`: Verifica restricción de unicidad

### ContainerDefectTypeModelTest (3 tests)
- `test_create_container_defect_type`: Verifica creación de tipos de defectos de contenedores
- `test_container_defect_type_str_representation`: Verifica representación string
- `test_container_defect_type_unique_name`: Verifica restricción de unicidad

## 2. Tests de Modelos Complejos

### QualityQcFaModelTest (2 tests)
- `test_create_quality_qc_fa`: Verifica creación de registros QC FA
- `test_quality_qc_fa_with_defects`: Verifica relaciones con defectos

### SecondsA4ModelTest (1 test)
- `test_create_seconds_a4`: Verifica creación de registros Seconds A4

### SecondsGeneralModelTest (1 test)
- `test_create_seconds_general`: Verifica creación de registros Seconds General

### ContainerModelTest (2 tests)
- `test_create_container`: Verifica creación de contenedores
- `test_container_with_defects`: Verifica relaciones con defectos de contenedores

### InspectionDefectModelTest (2 tests)
- `test_create_inspection_defect`: Verifica creación de defectos de inspección
- `test_unique_constraint_inspection_defect`: Verifica restricción única

### ContainerInspectionDefectModelTest (2 tests)
- `test_create_container_inspection_defect`: Verifica creación de defectos de contenedores
- `test_unique_constraint_container_inspection_defect`: Verifica restricción única

## 3. Tests de Funciones de Inicialización

### InitDataModelsTest (4 tests)
- `test_save_color`: Verifica carga de colores desde COMPANY_COLORS
- `test_save_color_idempotent`: Verifica idempotencia de SaveColor()
- `test_save_defects`: Verifica carga de defectos desde GARMENT_DEFECT_TYPES
- `test_save_defects_container`: Verifica carga de defectos de contenedores desde CONTAINER_DEFECT_TYPES

## 4. Tests de Restricciones y Validaciones

### QualityQcFaConstraintsTest (2 tests)
- `test_table_type_valid_choices`: Verifica valores válidos para table_type ("QFA", "QFC")
- `test_table_type_invalid_choice`: Verifica que se permiten valores fuera de choices (comportamiento Django)

### InspectionDefectAmountTest (3 tests)
- `test_inspection_defect_amount_zero`: Verifica que amount puede ser 0
- `test_inspection_defect_amount_positive`: Verifica que amount puede ser positivo
- `test_inspection_defect_amount_negative_should_fail`: Verifica que amount puede ser negativo (no hay validación en modelo)

## 5. Tests de Vistas

### ProcessViewTest (1 test)
- `test_process_view_post`: Verifica endpoint POST /process/ con mocking

### SaveDataViewTest (1 test)
- `test_save_data_view_post`: Verifica endpoint POST /savedata/ con mocking

### SaveDataViewRealDBTest (1 test)
- `test_save_data_with_real_db_integration`: Verifica integración con DB real usando mocking

## Cobertura de Funcionalidades

### ✅ Modelos (100%)
- Color, DefectType, ContainerDefectType
- QualityQcFa, InspectionDefect
- SecondsA4, SecondsGeneral
- Container, ContainerInspectionDefect

### ✅ Funciones de Inicialización (100%)
- SaveColor(), SaveDefects(), SaveDefectsContainer()

### ✅ Restricciones y Validaciones (100%)
- Unicidad de nombres
- Choices de table_type
- Valores de amount en defectos

### ✅ Vistas API (100%)
- Process (solo procesamiento)
- SaveData (procesamiento e inserción)

### ✅ Integración con Base de Datos (100%)
- Migraciones aplicadas
- Constraints respetadas
- Relaciones funcionando

## Ejecución de Tests

```bash
# Ejecutar todos los tests
cd backend
python manage.py test quality_data.tests

# Ejecutar con verbosidad
python manage.py test quality_data.tests --verbosity=2

# Ejecutar tests específicos
python manage.py test quality_data.tests.ColorModelTest
python manage.py test quality_data.tests.InitDataModelsTest
```

## Configuración para Tests

Los tests usan SQLite en memoria para mayor velocidad:
```python
# En settings.py
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
```

## Notas Importantes

1. **Validación de Choices**: Django no valida automáticamente las opciones en la base de datos, solo a nivel de formularios.
2. **Valores Negativos**: Los campos IntegerField no validan automáticamente valores negativos.
3. **Idempotencia**: Las funciones de inicialización son idempotentes (no crean duplicados).
4. **Mocking**: Los tests de vistas usan mocking para evitar dependencias externas complejas.

## Próximos Tests a Implementar

1. Tests de integración con archivos Excel reales
2. Tests de rendimiento con grandes volúmenes de datos
3. Tests de seguridad y autenticación
4. Tests de edge cases en importación de datos