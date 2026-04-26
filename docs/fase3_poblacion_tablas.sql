-- ==============================================================================
-- Rift Analytics - Fase 3: Población de Tablas (Script SQL)
-- ==============================================================================
-- Este script puebla todas las tablas con datos de prueba realistas e interrelacionados.
-- Ejecutar en orden: primero tablas independientes, luego dependientes.
-- ==============================================================================

SET CONSTRAINTS ALL DEFERRED;

-- ------------------------------------------------------------------------------
-- 1. TABLAS DE DOMINIO BASE (sin dependencias)
-- ------------------------------------------------------------------------------

-- Colores utilizados en la fábrica
INSERT INTO quality_data_color (name, is_active) VALUES
    ('Negro', true),
    ('Blanco', true),
    ('Azul Marino', true),
    ('Rojo', true),
    ('Verde Bosque', true),
    ('Gris Oxford', true),
    ('Beige', true),
    ('Azul Cielo', true),
    ('Rosa', true),
    ('Negro/Blanco', true);

-- Tipos de defectos para inspección de calidad (QC FA)
INSERT INTO quality_data_defecttype (name, is_active) VALUES
    ('Hilo faltante', true),
    ('Costura abierta', true),
    ('Mancha', true),
    ('Tela defectuosa', true),
    ('Medida fuera de tolerancia', true),
    ('Color incorrecto', true),
    ('Etiqueta faltante', true),
    ('Botón faltante', true),
    ('Zip defectuoso', true),
    ('Agujeta', true),
    ('Deshilachado', true),
    ('Arrugado', true),
    ('Pegado incorrecto', true),
    ('Bordado defectuoso', true),
    ('Otro', true);

-- Tipos de defectos para contenedores
INSERT INTO quality_data_containerdefecttype (name, is_active) VALUES
    ('Caja dañada', true),
    ('Humedad', true),
    ('Etiqueta incorrecta', true),
    ('Cantidad incorrecta', true),
    ('Producto MIX', true),
    ('Expired', true),
    ('Contaminación', true),
    ('Embalaje deficiente', true),
    ('Otro', true);

-- ------------------------------------------------------------------------------
-- 2. USUARIOS DE PRUEBA (requerido por media_data.InspectionData)
-- ------------------------------------------------------------------------------

INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
    (1, 'pbkdf2_sha256$870000$test$hashedpassword1', NULL, true, 'admin', 'Admin', 'User', 'admin@rift.com', true, true, '2026-01-01 00:00:00'),
    (2, 'pbkdf2_sha256$870000$test$hashedpassword2', NULL, false, 'inspector1', 'Juan', 'Pérez', 'juan@rift.com', false, true, '2026-01-15 00:00:00'),
    (3, 'pbkdf2_sha256$870000$test$hashedpassword3', NULL, false, 'inspector2', 'María', 'García', 'maria@rift.com', false, true, '2026-01-20 00:00:00'),
    (4, 'pbkdf2_sha256$870000$test$hashedpassword4', NULL, false, 'supervisor', 'Carlos', 'López', 'carlos@rift.com', false, true, '2026-02-01 00:00:00');

-- ------------------------------------------------------------------------------
-- 3. CALENDARIO BASE (Semanas del año 2026)
-- ------------------------------------------------------------------------------

-- Tabla SecondsGeneral: datos semanales de telares
INSERT INTO quality_data_secondsgeneral (date, week, corrido_2, barre, otros_3, degradacion, bordados, total_de_tela) VALUES
    ('2026-01-06', 2, 1200, 350, 80, 45, 20, 1695),
    ('2026-01-13', 3, 1350, 420, 95, 50, 25, 1940),
    ('2026-01-20', 4, 1100, 380, 70, 40, 18, 1608),
    ('2026-01-27', 5, 1450, 400, 110, 55, 30, 2045),
    ('2026-02-03', 6, 1300, 390, 85, 48, 22, 1845),
    ('2026-02-10', 7, 1250, 410, 90, 52, 24, 1826),
    ('2026-02-17', 8, 1400, 430, 100, 58, 28, 2016),
    ('2026-02-24', 9, 1150, 370, 75, 42, 19, 1656),
    ('2026-03-03', 10, 1380, 405, 92, 54, 26, 1957),
    ('2026-03-10', 11, 1420, 415, 105, 56, 27, 2023),
    ('2026-03-17', 12, 1280, 385, 88, 49, 23, 1825),
    ('2026-03-24', 13, 1350, 400, 95, 51, 25, 1921),
    ('2026-03-31', 14, 1220, 375, 82, 46, 21, 1744),
    ('2026-04-07', 15, 1400, 420, 98, 55, 27, 2000);

-- ------------------------------------------------------------------------------
-- 4. CALIDAD QC FA (Plant y Customer)
-- ------------------------------------------------------------------------------

-- QC FA Plant - Inspecciones en planta
INSERT INTO quality_data_qualityqcfa 
    (table_type, date_1, week, customer, team, coord, date_2, po, style, batch, color_id, qty, seconds, accepted, rejected, sample, defects_total, aql, pass_or_fail) VALUES
    ('QFA', '2026-01-15', 3, 'Nike', 1, 'COORD-001', '2026-01-16', 45001, 'T-SHIRT-BASIC', 101, 1, 500, 1800, 485, 15, 125, 15, 0.65, 'PASS'),
    ('QFA', '2026-01-15', 3, 'Nike', 1, 'COORD-001', '2026-01-16', 45001, 'T-SHIRT-BASIC', 101, 2, 500, 1800, 490, 10, 125, 10, 0.65, 'PASS'),
    ('QFA', '2026-01-16', 3, 'Nike', 2, 'COORD-002', '2026-01-17', 45002, 'HOODIE-PREM', 102, 3, 300, 2100, 285, 15, 80, 18, 0.65, 'FAIL'),
    ('QFA', '2026-01-20', 4, 'Adidas', 1, 'COORD-003', '2026-01-21', 55001, 'POLO-CLASSIC', 201, 4, 400, 1650, 380, 20, 100, 22, 0.65, 'FAIL'),
    ('QFA', '2026-01-20', 4, 'Adidas', 2, 'COORD-004', '2026-01-21', 55002, 'POLO-CLASSIC', 202, 1, 400, 1650, 395, 5, 100, 5, 0.65, 'PASS'),
    ('QFA', '2026-01-22', 5, 'Puma', 1, 'COORD-005', '2026-01-23', 65001, 'JACKET-EXEC', 301, 5, 250, 2400, 240, 10, 65, 12, 0.65, 'PASS'),
    ('QFA', '2026-01-27', 5, 'Puma', 2, 'COORD-005', '2026-01-28', 65002, 'JACKET-EXEC', 302, 6, 250, 2400, 235, 15, 65, 18, 0.65, 'FAIL'),
    ('QFA', '2026-02-03', 6, 'Under Armour', 1, 'COORD-006', '2026-02-04', 75001, 'SHORT-SPORT', 401, 7, 600, 1500, 570, 30, 150, 32, 0.65, 'FAIL'),
    ('QFA', '2026-02-05', 6, 'Under Armour', 2, 'COORD-006', '2026-02-06', 75002, 'SHORT-SPORT', 402, 8, 600, 1500, 590, 10, 150, 10, 0.65, 'PASS'),
    ('QFA', '2026-02-10', 7, 'Nike', 1, 'COORD-001', '2026-02-11', 45003, 'T-SHIRT-BASIC', 103, 9, 550, 1750, 530, 20, 135, 25, 0.65, 'FAIL');

-- QC FA Customer - Inspecciones en cliente
INSERT INTO quality_data_qualityqcfa 
    (table_type, date_1, week, customer, team, coord, date_2, po, style, batch, color_id, qty, seconds, accepted, rejected, sample, defects_total, aql, pass_or_fail) VALUES
    ('QFC', '2026-01-18', 3, 'Nike', 3, 'COORD-010', '2026-01-20', 45011, 'T-SHIRT-BASIC', 111, 1, 480, 1780, 460, 20, 120, 22, 0.65, 'FAIL'),
    ('QFC', '2026-01-23', 4, 'Adidas', 3, 'COORD-011', '2026-01-25', 55011, 'POLO-CLASSIC', 211, 3, 380, 1620, 365, 15, 95, 18, 0.65, 'FAIL'),
    ('QFC', '2026-01-28', 5, 'Puma', 3, 'COORD-012', '2026-01-30', 65011, 'JACKET-EXEC', 311, 5, 240, 2350, 230, 10, 60, 12, 0.65, 'PASS'),
    ('QFC', '2026-02-04', 6, 'Under Armour', 3, 'COORD-013', '2026-02-06', 75011, 'SHORT-SPORT', 411, 7, 580, 1480, 560, 20, 145, 22, 0.65, 'FAIL'),
    ('QFC', '2026-02-12', 7, 'Nike', 3, 'COORD-010', '2026-02-14', 45012, 'T-SHIRT-BASIC', 112, 10, 520, 1720, 505, 15, 130, 18, 0.65, 'PASS'),
    ('QFC', '2026-02-18', 8, 'Adidas', 3, 'COORD-011', '2026-02-20', 55012, 'POLO-CLASSIC', 212, 2, 390, 1600, 375, 15, 98, 17, 0.65, 'FAIL'),
    ('QFC', '2026-02-25', 9, 'Puma', 3, 'COORD-012', '2026-02-27', 65012, 'JACKET-EXEC', 312, 4, 245, 2380, 238, 7, 62, 8, 0.65, 'PASS'),
    ('QFC', '2026-03-04', 10, 'Under Armour', 3, 'COORD-013', '2026-03-06', 75012, 'SHORT-SPORT', 412, 8, 590, 1510, 575, 15, 148, 18, 0.65, 'PASS'),
    ('QFC', '2026-03-11', 11, 'Nike', 3, 'COORD-010', '2026-03-13', 45013, 'T-SHIRT-BASIC', 113, 9, 540, 1740, 525, 15, 135, 15, 0.65, 'PASS'),
    ('QFC', '2026-03-18', 12, 'Adidas', 3, 'COORD-011', '2026-03-20', 55013, 'POLO-CLASSIC', 213, 6, 385, 1630, 370, 15, 96, 16, 0.65, 'FAIL');

-- Tabla intermedia: InspectionDefect (defectos por inspección QC FA)
INSERT INTO quality_data_inspectiondefect (inspection_id, defect_type_id, amount) VALUES
    -- Inspecciones QFA (ids 1-10)
    (1, 1, 3), (1, 2, 5), (1, 3, 7),
    (2, 1, 2), (2, 4, 8),
    (3, 2, 4), (3, 5, 6), (3, 6, 8),
    (4, 1, 5), (4, 3, 10), (4, 7, 7),
    (5, 1, 2), (5, 2, 3),
    (6, 4, 4), (6, 8, 5), (6, 9, 3),
    (7, 2, 6), (7, 5, 7), (7, 10, 5),
    (8, 1, 8), (8, 3, 12), (8, 11, 6), (8, 12, 6),
    (9, 1, 2), (9, 7, 8),
    (10, 3, 10), (10, 6, 8), (10, 13, 7),
    -- Inspecciones QFC (ids 11-20)
    (11, 2, 5), (11, 4, 10), (11, 7, 7),
    (12, 1, 3), (12, 5, 8), (12, 8, 7),
    (13, 4, 4), (13, 9, 5), (13, 10, 3),
    (14, 1, 6), (14, 3, 9), (14, 11, 7),
    (15, 1, 3), (15, 6, 6), (15, 14, 9),
    (16, 2, 4), (16, 5, 6), (16, 7, 6),
    (17, 3, 3), (17, 8, 2), (17, 10, 3),
    (18, 1, 5), (18, 9, 8), (18, 12, 5),
    (19, 2, 4), (19, 4, 6), (19, 15, 5),
    (20, 1, 4), (20, 6, 5), (20, 7, 7);

-- ------------------------------------------------------------------------------
-- 5. SECONDS A4 (Producción por corte)
-- ------------------------------------------------------------------------------

INSERT INTO quality_data_secondsa4 
    (year, week, date, cut_num, style, cut_qty, color_id, first_quality_qty_sewing, sample, pass_field, fail_field, sew_def, fab_def, accepted, rejected, total_of_2ds, percentage_of_2ds, line, seconds_by_sew, seconds_by_fab, seconds_sew_a4, seconds_fab_a4) VALUES
    (2026, 3, '2026-01-15', 1, 'T-SHIRT-BASIC', 500, 1, 480, 125, 460, 20, 15, 5, 455, 45, 40, 8.0, 'LINEA-1', 1800, 450, 2250, 562),
    (2026, 3, '2026-01-16', 2, 'T-SHIRT-BASIC', 500, 2, 485, 125, 470, 15, 12, 3, 467, 33, 33, 6.6, 'LINEA-1', 1820, 440, 2275, 550),
    (2026, 4, '2026-01-20', 3, 'POLO-CLASSIC', 400, 3, 385, 100, 375, 10, 8, 2, 373, 27, 27, 6.75, 'LINEA-2', 1650, 410, 2062, 515),
    (2026, 4, '2026-01-21', 4, 'POLO-CLASSIC', 400, 4, 390, 100, 380, 10, 7, 3, 377, 23, 23, 5.75, 'LINEA-2', 1660, 405, 2075, 506),
    (2026, 5, '2026-01-27', 5, 'JACKET-EXEC', 250, 5, 240, 65, 230, 10, 6, 4, 234, 16, 16, 6.4, 'LINEA-3', 2400, 600, 3000, 750),
    (2026, 5, '2026-01-28', 6, 'JACKET-EXEC', 250, 6, 238, 65, 228, 10, 5, 5, 233, 17, 17, 6.8, 'LINEA-3', 2380, 595, 2975, 743),
    (2026, 6, '2026-02-03', 7, 'SHORT-SPORT', 600, 7, 570, 150, 550, 20, 18, 2, 568, 32, 32, 5.33, 'LINEA-1', 1500, 375, 1875, 468),
    (2026, 6, '2026-02-04', 8, 'SHORT-SPORT', 600, 8, 580, 150, 560, 20, 16, 4, 576, 24, 24, 4.0, 'LINEA-1', 1520, 380, 1900, 475),
    (2026, 7, '2026-02-10', 9, 'T-SHIRT-BASIC', 550, 9, 525, 135, 510, 15, 14, 1, 524, 26, 26, 4.72, 'LINEA-2', 1750, 437, 2187, 546),
    (2026, 7, '2026-02-11', 10, 'T-SHIRT-BASIC', 550, 10, 530, 135, 515, 15, 13, 2, 529, 21, 21, 3.81, 'LINEA-2', 1760, 440, 2200, 550),
    (2026, 8, '2026-02-17', 11, 'POLO-CLASSIC', 420, 1, 400, 105, 390, 10, 9, 1, 399, 21, 21, 5.0, 'LINEA-3', 1620, 405, 2025, 506),
    (2026, 8, '2026-02-18', 12, 'POLO-CLASSIC', 420, 2, 405, 105, 395, 10, 8, 2, 403, 17, 17, 4.04, 'LINEA-3', 1630, 407, 2037, 509),
    (2026, 9, '2026-02-24', 13, 'JACKET-EXEC', 260, 3, 250, 70, 240, 10, 7, 3, 247, 13, 13, 5.0, 'LINEA-1', 2350, 587, 2937, 734),
    (2026, 10, '2026-03-03', 14, 'SHORT-SPORT', 580, 4, 555, 145, 540, 15, 13, 2, 553, 27, 27, 4.65, 'LINEA-2', 1480, 370, 1850, 462),
    (2026, 11, '2026-03-10', 15, 'T-SHIRT-BASIC', 540, 5, 515, 130, 500, 15, 12, 3, 517, 23, 23, 4.25, 'LINEA-3', 1710, 427, 2137, 534),
    (2026, 12, '2026-03-17', 16, 'POLO-CLASSIC', 390, 6, 375, 98, 365, 10, 8, 2, 373, 17, 17, 4.35, 'LINEA-1', 1600, 400, 2000, 500),
    (2026, 13, '2026-03-24', 17, 'JACKET-EXEC', 255, 7, 245, 68, 235, 10, 6, 4, 249, 6, 6, 2.35, 'LINEA-2', 2370, 592, 2962, 740),
    (2026, 14, '2026-03-31', 18, 'SHORT-SPORT', 590, 8, 565, 148, 550, 15, 14, 1, 569, 21, 21, 3.55, 'LINEA-3', 1490, 372, 1862, 465),
    (2026, 15, '2026-04-07', 19, 'T-SHIRT-BASIC', 560, 9, 540, 140, 525, 15, 13, 2, 538, 22, 22, 3.92, 'LINEA-1', 1740, 435, 2175, 543),
    (2026, 15, '2026-04-08', 20, 'POLO-CLASSIC', 410, 10, 395, 103, 385, 10, 9, 1, 394, 16, 16, 3.9, 'LINEA-2', 1610, 402, 2012, 503);

-- ------------------------------------------------------------------------------
-- 6. CONTENEDORES (Exportación)
-- ------------------------------------------------------------------------------

INSERT INTO quality_data_container 
    (container_number, customer, transfer_of_container, total_palette, total_palette_pass, total_palette_rejected, percentage_pass, percentage_reject) VALUES
    (101, 'Nike', 1, 1200, 1140, 60, 95.0, 5.0),
    (102, 'Nike', 2, 1150, 1100, 50, 95.65, 4.35),
    (103, 'Adidas', 1, 980, 931, 49, 95.0, 5.0),
    (104, 'Adidas', 2, 1050, 997, 53, 94.95, 5.05),
    (105, 'Puma', 1, 800, 760, 40, 95.0, 5.0),
    (106, 'Puma', 2, 820, 784, 36, 95.61, 4.39),
    (107, 'Under Armour', 1, 1400, 1330, 70, 95.0, 5.0),
    (108, 'Under Armour', 2, 1380, 1311, 69, 95.0, 5.0),
    (109, 'Nike', 3, 1180, 1121, 59, 95.0, 5.0),
    (110, 'Adidas', 3, 1020, 969, 51, 95.0, 5.0),
    (111, 'Puma', 3, 850, 807, 43, 95.0, 5.0),
    (112, 'Under Armour', 4, 1350, 1282, 68, 95.0, 5.0),
    (113, 'Nike', 4, 1220, 1159, 61, 95.0, 5.0),
    (114, 'Adidas', 4, 990, 940, 50, 94.95, 5.05),
    (115, 'Puma', 4, 780, 741, 39, 95.0, 5.0);

-- Tabla intermedia: ContainerInspectionDefect (defectos por contenedor)
-- NOTA: container_id referencia container.id (SERIAL 1-15), NO container_number (101-115)
INSERT INTO quality_data_containerinspectiondefect (container_id, defect_type_id, amount) VALUES
    (1, 1, 15), (1, 2, 10), (1, 5, 35),
    (2, 1, 12), (2, 3, 8), (2, 4, 30),
    (3, 2, 14), (3, 4, 35),
    (4, 1, 18), (4, 6, 35),
    (5, 3, 12), (5, 7, 28),
    (6, 2, 10), (6, 5, 26),
    (7, 1, 20), (7, 4, 50),
    (8, 2, 22), (8, 3, 15), (8, 8, 32),
    (9, 1, 16), (9, 5, 43),
    (10, 3, 14), (10, 4, 37),
    (11, 2, 11), (11, 6, 32),
    (12, 1, 18), (12, 4, 50),
    (13, 2, 20), (13, 5, 41),
    (14, 3, 15), (14, 7, 35),
    (15, 1, 10), (15, 2, 8), (15, 4, 21);

-- ------------------------------------------------------------------------------
-- 7. MEDIA DATA (Touch Capture - Inspecciones visuales)
-- ------------------------------------------------------------------------------

-- Mockups: plantillas de prendas para captura táctil
INSERT INTO media_data_mockup (id, name, side, image, width, height) VALUES
    (1, 'T-SHIRT-BASIC', 'FRONT', 'mockups/tshirt_basic_front.png', 1024, 768),
    (2, 'T-SHIRT-BASIC', 'BACK', 'mockups/tshirt_basic_back.png', 1024, 768),
    (3, 'HOODIE-PREM', 'FRONT', 'mockups/hoodie_prem_front.png', 1024, 768),
    (4, 'HOODIE-PREM', 'BACK', 'mockups/hoodie_prem_back.png', 1024, 768),
    (5, 'POLO-CLASSIC', 'FRONT', 'mockups/polo_classic_front.png', 1024, 768),
    (6, 'POLO-CLASSIC', 'BACK', 'mockups/polo_classic_back.png', 1024, 768),
    (7, 'JACKET-EXEC', 'FRONT', 'mockups/jacket_exec_front.png', 1024, 768),
    (8, 'JACKET-EXEC', 'BACK', 'mockups/jacket_exec_back.png', 1024, 768),
    (9, 'SHORT-SPORT', 'FRONT', 'mockups/short_sport_front.png', 1024, 768),
    (10, 'SHORT-SPORT', 'BACK', 'mockups/short_sport_back.png', 1024, 768);

-- InspectionData: sesiones de inspección
INSERT INTO media_data_inspectiondata 
    (inspector_id, date, created_at, week, style, size, lot, color_id, is_closed, status, closed_at) VALUES
    (2, '2026-01-15', '08:30:00', 3, 'T-SHIRT-BASIC', 'M', 'LOT-2026-001', 1, true, 'PASS', '2026-01-15 09:15:00'),
    (2, '2026-01-15', '09:30:00', 3, 'T-SHIRT-BASIC', 'L', 'LOT-2026-002', 2, true, 'PASS', '2026-01-15 10:45:00'),
    (3, '2026-01-16', '08:00:00', 3, 'HOODIE-PREM', 'XL', 'LOT-2026-003', 3, true, 'REJECT', '2026-01-16 09:30:00'),
    (3, '2026-01-16', '10:00:00', 3, 'HOODIE-PREM', 'L', 'LOT-2026-004', 4, true, 'PASS', '2026-01-16 11:20:00'),
    (4, '2026-01-20', '08:15:00', 4, 'POLO-CLASSIC', 'S', 'LOT-2026-005', 5, false, 'OPEN', NULL),
    (2, '2026-01-20', '09:00:00', 4, 'POLO-CLASSIC', 'M', 'LOT-2026-006', 1, true, 'PASS', '2026-01-20 10:00:00'),
    (3, '2026-01-21', '08:30:00', 4, 'JACKET-EXEC', 'L', 'LOT-2026-007', 5, true, 'PASS', '2026-01-21 09:45:00'),
    (4, '2026-01-21', '10:00:00', 4, 'JACKET-EXEC', 'M', 'LOT-2026-008', 6, true, 'REJECT', '2026-01-21 11:30:00'),
    (2, '2026-01-22', '08:00:00', 5, 'SHORT-SPORT', 'M', 'LOT-2026-009', 7, true, 'PASS', '2026-01-22 08:45:00'),
    (3, '2026-01-22', '09:00:00', 5, 'SHORT-SPORT', 'L', 'LOT-2026-010', 8, false, 'OPEN', NULL),
    (4, '2026-01-23', '08:30:00', 5, 'T-SHIRT-BASIC', 'S', 'LOT-2026-011', 9, true, 'PASS', '2026-01-23 09:20:00'),
    (2, '2026-01-23', '10:00:00', 5, 'T-SHIRT-BASIC', 'XL', 'LOT-2026-012', 10, true, 'PASS', '2026-01-23 10:45:00'),
    (3, '2026-01-27', '08:00:00', 5, 'POLO-CLASSIC', 'M', 'LOT-2026-013', 3, true, 'PASS', '2026-01-27 08:50:00'),
    (4, '2026-01-27', '09:00:00', 5, 'POLO-CLASSIC', 'L', 'LOT-2026-014', 4, true, 'PASS', '2026-01-27 09:55:00'),
    (2, '2026-01-28', '08:15:00', 5, 'JACKET-EXEC', 'S', 'LOT-2026-015', 5, true, 'PASS', '2026-01-28 09:00:00'),
    (3, '2026-01-28', '09:30:00', 5, 'JACKET-EXEC', 'M', 'LOT-2026-016', 6, true, 'REJECT', '2026-01-28 10:30:00'),
    (4, '2026-01-29', '08:00:00', 5, 'SHORT-SPORT', 'S', 'LOT-2026-017', 7, true, 'PASS', '2026-01-29 08:40:00'),
    (2, '2026-01-29', '09:00:00', 5, 'SHORT-SPORT', 'M', 'LOT-2026-018', 8, true, 'PASS', '2026-01-29 09:50:00'),
    (3, '2026-01-30', '08:30:00', 5, 'T-SHIRT-BASIC', 'L', 'LOT-2026-019', 9, true, 'PASS', '2026-01-30 09:15:00'),
    (4, '2026-01-30', '10:00:00', 5, 'T-SHIRT-BASIC', 'XL', 'LOT-2026-020', 10, true, 'PASS', '2026-01-30 10:45:00');

-- RevisionDefect: defectos encontrados durante inspección
-- Se incluyen defectos para inspecciones con status REJECT y PASS para demostrar
-- la integridad referencial con inspection_data, auth_user y defect_type.
INSERT INTO media_data_revisiondefect 
    (inspection_id, inspector_id, defect_type_id, defect_size, notes, defect_count, timestamp, coordinates_x, coordinates_y) VALUES
    -- Inspección #3 (REJECT - HOODIE-PREM, inspector María)
    (3, 3, 1, 'Pequeño', 'Hilo faltante en costuras laterales', 2, '2026-01-16 08:15:00', '[120, 350]', '[200, 450]'),
    (3, 3, 4, 'Mediano', 'Tela con defectación en manga izquierda', 1, '2026-01-16 08:45:00', '[80]', '[300]'),
    -- Inspección #1 (PASS - T-SHIRT-BASIC, inspector Juan)
    (1, 2, 2, 'Pequeño', 'Costura ligeramente abierta en hombro', 1, '2026-01-15 08:45:00', '[200]', '[150]'),
    -- Inspección #5 (OPEN - POLO-CLASSIC, supervisor Carlos)
    (5, 4, 5, 'Grande', 'Medida fuera de tolerancia en largo', 1, '2026-01-20 08:30:00', '[100, 300]', '[400, 600]'),
    (5, 4, 6, 'Mediano', 'Color inconsistente en cuello', 2, '2026-01-20 08:40:00', '[150, 250]', '[100, 200]'),
    -- Inspección #8 (REJECT - JACKET-EXEC, supervisor Carlos)
    (8, 4, 2, 'Grande', 'Costura abierta en bolsillo', 1, '2026-01-21 10:15:00', '[150]', '[220]'),
    (8, 4, 7, 'Pequeño', 'Etiqueta mal posicionada', 1, '2026-01-21 10:30:00', '[200]', '[100]'),
    (8, 4, 3, 'Pequeño', 'Mancha de tinta en forro interior', 1, '2026-01-21 10:45:00', '[280]', '[380]'),
    -- Inspección #10 (OPEN - SHORT-SPORT, inspectora María)
    (10, 3, 1, 'Mediano', 'Hilo suelto en pretina', 2, '2026-01-22 09:15:00', '[90, 180]', '[250, 350]'),
    -- Inspección #16 (REJECT - JACKET-EXEC, inspectora María)
    (16, 3, 3, 'Mediano', 'Mancha de aceite en espalda', 1, '2026-01-28 09:45:00', '[180]', '[350]'),
    (16, 3, 9, 'Pequeño', 'Zip atascado', 1, '2026-01-28 10:00:00', '[100]', '[250]'),
    -- Inspección #19 (PASS - T-SHIRT-BASIC, inspectora María)
    (19, 3, 11, 'Pequeño', 'Deshilachado menor en bastilla', 1, '2026-01-30 08:45:00', '[160]', '[500]');

-- ------------------------------------------------------------------------------
-- 8. VERIFICACIÓN DE INTEGRIDAD
-- ------------------------------------------------------------------------------

-- Verificar que las foreign keys funcionan correctamente
-- Esta consulta muestra cuántas inspecciones tienen defectos asociados
SELECT 
    'QualityQcFa (QFA)' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT q.id) as records_with_defects
FROM quality_data_qualityqcfa q
LEFT JOIN quality_data_inspectiondefect i ON q.id = i.inspection_id
WHERE q.table_type = 'QFA';

SELECT 
    'QualityQcFa (QFC)' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT q.id) as records_with_defects
FROM quality_data_qualityqcfa q
LEFT JOIN quality_data_inspectiondefect i ON q.id = i.inspection_id
WHERE q.table_type = 'QFC';

SELECT 
    'Container' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT c.id) as records_with_defects
FROM quality_data_container c
LEFT JOIN quality_data_containerinspectiondefect i ON c.id = i.container_id;

-- Verificar datos de inspección por estado
SELECT 
    status,
    COUNT(*) as total,
    COUNT(CASE WHEN is_closed = true THEN 1 END) as closed
FROM media_data_inspectiondata
GROUP BY status;

-- Resumen de defectos por tipo (top 10)
SELECT 
    dt.name as defect_type,
    COUNT(*) as occurrences,
    SUM(rd.defect_count) as total_defects
FROM media_data_revisiondefect rd
JOIN quality_data_defecttype dt ON rd.defect_type_id = dt.id
GROUP BY dt.name
ORDER BY total_defects DESC
LIMIT 10;

-- ------------------------------------------------------------------------------
-- 9. EXCEL SYNC SESSION (sesión de importación de prueba)
-- ------------------------------------------------------------------------------

-- Sesión de sincronización completada con datos de preview
INSERT INTO quality_data_excelsyncsession 
    (status, created_at, qc_fa_plant_data, qc_fa_customer_data, seconds_a4_data, seconds_general_data, container_data, qc_fa_plant_preview, qc_fa_customer_preview, seconds_a4_preview, seconds_general_preview, container_preview, warnings) VALUES
    ('confirmed', '2026-01-15 07:00:00',
     '[{"date_1": "2026-01-15", "customer": "Nike", "style": "T-SHIRT-BASIC"}]',
     '[{"date_1": "2026-01-18", "customer": "Nike", "style": "T-SHIRT-BASIC"}]',
     '[{"date": "2026-01-15", "style": "T-SHIRT-BASIC", "cut_num": 1}]',
     '[{"date": "2026-01-06", "week": 2, "total_de_tela": 1695}]',
     '[{"container_number": 101, "customer": "Nike"}]',
     '{"new": 10, "updated": 0, "deleted": 0}',
     '{"new": 10, "updated": 0, "deleted": 0}',
     '{"new": 20, "updated": 0, "deleted": 0}',
     '{"new": 14, "updated": 0, "deleted": 0}',
     '{"new": 15, "updated": 0, "deleted": 0}',
     '[]'),
    ('pending', '2026-04-05 12:00:00',
     '[{"date_1": "2026-04-10", "customer": "Nike", "style": "T-SHIRT-V2"}]',
     '[]',
     '[{"date": "2026-04-10", "style": "T-SHIRT-V2", "cut_num": 21}]',
     '[{"date": "2026-04-07", "week": 15, "total_de_tela": 2000}]',
     '[]',
     '{"new": 5, "updated": 2, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '{"new": 3, "updated": 1, "deleted": 0}',
     '{"new": 1, "updated": 0, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '["Advertencia: 2 registros de SecondsA4 serán actualizados"]'),
    ('rejected', '2026-03-20 09:30:00',
     '[]', '[]', '[]', '[]', '[]',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '{"new": 0, "updated": 0, "deleted": 0}',
     '["Error: archivo Excel vacío o con formato incorrecto"]');

-- ------------------------------------------------------------------------------
-- 10. RESET SECUENCIAS (para que los próximos INSERT no colisionen)
-- ------------------------------------------------------------------------------

SELECT setval('quality_data_color_id_seq', (SELECT MAX(id) FROM quality_data_color));
SELECT setval('quality_data_defecttype_id_seq', (SELECT MAX(id) FROM quality_data_defecttype));
SELECT setval('quality_data_containerdefecttype_id_seq', (SELECT MAX(id) FROM quality_data_containerdefecttype));
SELECT setval('quality_data_qualityqcfa_id_seq', (SELECT MAX(id) FROM quality_data_qualityqcfa));
SELECT setval('quality_data_inspectiondefect_id_seq', (SELECT MAX(id) FROM quality_data_inspectiondefect));
SELECT setval('quality_data_secondsa4_id_seq', (SELECT MAX(id) FROM quality_data_secondsa4));
SELECT setval('quality_data_secondsgeneral_id_seq', (SELECT MAX(id) FROM quality_data_secondsgeneral));
SELECT setval('quality_data_container_id_seq', (SELECT MAX(id) FROM quality_data_container));
SELECT setval('quality_data_containerinspectiondefect_id_seq', (SELECT MAX(id) FROM quality_data_containerinspectiondefect));
SELECT setval('media_data_mockup_id_seq', (SELECT MAX(id) FROM media_data_mockup));
SELECT setval('media_data_inspectiondata_id_seq', (SELECT MAX(id) FROM media_data_inspectiondata));
SELECT setval('media_data_revisiondefect_id_seq', (SELECT MAX(id) FROM media_data_revisiondefect));
SELECT setval('auth_user_id_seq', (SELECT MAX(id) FROM auth_user));
SELECT setval('quality_data_excelsyncsession_id_seq', (SELECT MAX(id) FROM quality_data_excelsyncsession));

-- ==============================================================================
-- FIN DEL SCRIPT
-- ==============================================================================
