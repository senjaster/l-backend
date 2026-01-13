-- Database Initialization Script
-- This script:
-- 1. Clears all tables including inspectors
-- 2. Populates equipment types according to plans/eq-type.md
-- 3. Populates sticker types with 3 sample types
-- 4. Creates 10 plants (ТЭЦ-1 to ТЭЦ-10)
-- 5. Creates test inspectors with known credentials

-- ============================================================================
-- 1. Clear all tables including inspectors
-- ============================================================================

-- Clear in order respecting foreign key constraints

-- Clear inspection aggregate
DELETE FROM lesiv.inspection_image_link;
DELETE FROM lesiv.inspection_step;
DELETE FROM lesiv.inspection;

-- Clear image aggregate
DELETE FROM lesiv.image;

-- Clear equipment aggregate
DELETE FROM lesiv.equipment_defect;
DELETE FROM lesiv.equipment_control_point;
DELETE FROM lesiv.equipment;

-- Clear plant aggregate
DELETE FROM lesiv.facility;
DELETE FROM lesiv.plant;

-- Clear logs
DELETE FROM lesiv.log;

-- Clear equipment type aggregate
DELETE FROM lesiv.equipment_control_point_template;
DELETE FROM lesiv.equipment_type;

-- Clear sticker type aggregate
DELETE FROM lesiv.sticker_temp_range;
DELETE FROM lesiv.sticker_type;

-- Clear tokens
DELETE FROM lesiv.tokens;

-- Clear inspectors
DELETE FROM lesiv.inspector;

-- ============================================================================
-- 2. Populate sticker types with 3 types
-- ============================================================================

-- Sticker Type 1: ТИН 60-80-100
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (1, 'ТИН 60-80-100', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (1, '< 60', 0, 60, FALSE),
    (1, '60-80', 60, 80, FALSE),
    (1, '80-100', 80, 100, FALSE),
    (1, '> 100', 100, 999, FALSE);

-- Sticker Type 2: ТИН 60-70-80-100
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (2, 'ТИН 60-70-80-100', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (2, '< 60', 0, 60, FALSE),
    (2, '60-70', 60, 70, FALSE),
    (2, '70-80', 70, 80, FALSE),
    (2, '80-100', 80, 100, FALSE),
    (2, '> 100', 100, 999, FALSE);

-- Sticker Type 3: ТИН 60-80-100-120
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (3, 'ТИН 60-80-100-120', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (3, '< 60', 0, 60, FALSE),
    (3, '60-80', 60, 80, FALSE),
    (3, '80-100', 80, 100, FALSE),
    (3, '100-120', 100, 120, FALSE),
    (3, '> 120', 120, 999, FALSE);

-- Reset sequence for sticker_type
SELECT setval('lesiv.sticker_type_id_seq', (SELECT MAX(id) FROM lesiv.sticker_type));

-- ============================================================================
-- 3. Populate equipment types and control point templates
-- ============================================================================

-- Equipment Type 1: Электродвигатель 0,4 кВ - подшипник качения
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (1, 'Электродвигатель 0,4 кВ - подшипник качения', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (1, 'Передний подшипник', 'ПП', 100, 60, 3, FALSE),
    (1, 'Задний подшипник', 'ЗП', 100, 60, 3, FALSE),
    (1, 'Корпус', 'Корпус', 100, 60, 2, FALSE),
    (1, 'Блок распределения начала обмоток', 'БРНО', 100, 60, 2, FALSE);

-- Equipment Type 2: Электродвигатель 0,4 кВ - подшипник скольжения
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (2, 'Электродвигатель 0,4 кВ - подшипник скольжения', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (2, 'Передний подшипник', 'ПП', 100, 60, 3, FALSE),
    (2, 'Задний подшипник', 'ЗП', 100, 60, 3, FALSE),
    (2, 'Корпус', 'Корпус', 100, 60, 2, FALSE),
    (2, 'Блок распределения начала обмоток', 'БРНО', 100, 60, 2, FALSE);

-- Equipment Type 3: Электродвигатель 6-10 кВ - подшипник качения
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (3, 'Электродвигатель 6-10 кВ - подшипник качения', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (3, 'Передний подшипник', 'ПП', 100, 60, 3, FALSE),
    (3, 'Задний подшипник', 'ЗП', 100, 60, 3, FALSE),
    (3, 'Корпус', 'Корпус', 100, 60, 2, FALSE),
    (3, 'Блок распределения начала обмоток', 'БРНО', 100, 60, 2, FALSE);

-- Equipment Type 4: Электродвигатель 6-10 кВ - подшипник скольжения
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (4, 'Электродвигатель 6-10 кВ - подшипник скольжения', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (4, 'Передний подшипник', 'ПП', 100, 60, 3, FALSE),
    (4, 'Задний подшипник', 'ЗП', 100, 60, 3, FALSE),
    (4, 'Корпус', 'Корпус', 100, 60, 2, FALSE),
    (4, 'Блок распределения начала обмоток', 'БРНО', 100, 60, 2, FALSE);

-- Equipment Type 5: Ячейка КРУ 6-10 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (5, 'Ячейка КРУ 6-10 кВ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (5, 'Болтовое контактное соединение', 'БКС', 100, 60, 1, FALSE),
    (5, 'Втычной контакт', 'Втычной контакт', 100, 60, 1, FALSE),
    (5, 'Кабельный наконечник', 'Кабельный наконечник', 100, 60, 1, FALSE),
    (5, 'Разделка кабельной муфты', 'Разделка кабельной муфты', 100, 60, 1, FALSE);

-- Equipment Type 6: Щит 0,4 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (6, 'Щит 0,4 кВ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id, is_deleted)
VALUES 
    (6, 'Болтовое контактное соединение', 'БКС', 100, 60, 1, FALSE),
    (6, 'Втычной контакт', 'Втычной контакт', 100, 60, 1, FALSE),
    (6, 'Кабельный наконечник', 'Кабельный наконечник', 100, 60, 1, FALSE);

-- Reset sequence for equipment_type
SELECT setval('lesiv.equipment_type_id_seq', (SELECT MAX(id) FROM lesiv.equipment_type));

-- ============================================================================
-- 4. Create 10 plants (ТЭЦ-1 to ТЭЦ-10)
-- ============================================================================

INSERT INTO lesiv.plant (id, name, locked_by_device_id, locked_by_user_id, locked_at, is_deleted, server_modified_at)
VALUES 
    (gen_random_uuid(), 'ТЭЦ-1', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-2', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-3', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-4', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-5', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-6', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-7', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-8', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-9', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-10', NULL, NULL, NULL, FALSE, CURRENT_TIMESTAMP);

-- ============================================================================
-- 5. Create test inspectors with known credentials
-- ============================================================================

-- Insert test inspectors with bcrypt hashed passwords
-- Passwords are documented in plans/passwords.md
INSERT INTO lesiv.inspector (id, full_name, username, password_hash, server_modified_at)
VALUES
    (100, 'Test Inspector', 'test_user', '$2b$12$.Ka2kYiM7M9s0riJw6Afb.lCxPg.4.3XVl3pJ9MiTmf6Ragk3PhfC', CURRENT_TIMESTAMP),
    (101, 'Вася Пупкин', 'vpupkin', '$2b$12$HwXpgvzRi9C4vHYcnSZE3.YNFoqqj7qcb0i8F/uGT7s57anKxb8Zy', CURRENT_TIMESTAMP),
    (102, 'Евлампия Иннокеньтевна', 'evinok', '$2b$12$ZhZN0Yce0R4fAcSpbVT1zOIH3ML26IfPFcHTxqQova84S2MerskBe', CURRENT_TIMESTAMP);

-- Reset sequence for inspector
SELECT setval('lesiv.inspector_id_seq', (SELECT MAX(id) FROM lesiv.inspector));

-- ============================================================================
-- Initialization Complete
-- ============================================================================

-- Display summary
SELECT 'Equipment Types Created:' as summary, COUNT(*) as count FROM lesiv.equipment_type
UNION ALL
SELECT 'Control Point Templates Created:', COUNT(*) FROM lesiv.equipment_control_point_template
UNION ALL
SELECT 'Sticker Types Created:', COUNT(*) FROM lesiv.sticker_type
UNION ALL
SELECT 'Sticker Temperature Ranges Created:', COUNT(*) FROM lesiv.sticker_temp_range
UNION ALL
SELECT 'Plants Created:', COUNT(*) FROM lesiv.plant
UNION ALL
SELECT 'Inspectors Created:', COUNT(*) FROM lesiv.inspector;
