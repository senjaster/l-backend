-- Database Initialization Script
-- This script:
-- 1. Clears all tables including inspectors
-- 2. Populates sticker types with 3 sample types
-- 3. Populates defect types from scripts/defect_types.txt
-- 4. Populates equipment types according to plans/eq-type.md
-- 5. Populates facility templates from scripts/Элеткрооборудование.txt
-- 6. Creates 10 plants (ТЭЦ-1 to ТЭЦ-10)
-- 7. Creates test inspectors with known credentials

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

-- Clear facility templates
DELETE FROM lesiv.facility_template_equipment;
DELETE FROM lesiv.facility_template;

-- Clear logs
DELETE FROM lesiv.log;

-- Clear equipment type aggregate
DELETE FROM lesiv.equipment_control_point_template;
DELETE FROM lesiv.equipment_type;

-- Clear sticker type aggregate
DELETE FROM lesiv.sticker_temp_range;
DELETE FROM lesiv.sticker_type;

-- Clear defect type aggregate
DELETE FROM lesiv.defect_type;

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
-- 3. Populate defect types
-- ============================================================================

INSERT INTO lesiv.defect_type (id, name, short_name, t_max, t_excess, is_deleted, server_modified_at)
VALUES
    (1, 'Неизолированная и не соприкасающаяся с изоляционным материалом токоведущая часть', 'Ток.вед часть (Неизол)', 120, 80, FALSE, CURRENT_TIMESTAMP),
    (2, 'Изолированная или соприкасающаяся с изоляционным материалом токоведущая часть классом нагревостойкости по ГОСТ 8865-93: Y', 'Ток.вед часть (Изол Y)', 90, 50, FALSE, CURRENT_TIMESTAMP),
    (3, 'Изолированная или соприкасающаяся с изоляционным материалом токоведущая часть классом нагревостойкости по ГОСТ 8865-93: A', 'Ток.вед часть (Изол A)', 100, 60, FALSE, CURRENT_TIMESTAMP),
    (4, 'Изолированная или соприкасающаяся с изоляционным материалом токоведущая часть классом нагревостойкости по ГОСТ 8865-93: E', 'Ток.вед часть (Изол E)', 120, 80, FALSE, CURRENT_TIMESTAMP),
    (5, 'Контакт из меди или сплавов меди без покрытия, на воздухе', 'Контакт (Cu)', 75, 35, FALSE, CURRENT_TIMESTAMP),
    (6, 'Аппаратный вывод из меди, алюминия и их сплавов без покрытия', 'Аппарат. Вывод', 90, 50, FALSE, CURRENT_TIMESTAMP),
    (7, 'Болтовое контактное соединение из меди без покрытия, в воздухе', 'БКС (Cu)', 90, 50, FALSE, CURRENT_TIMESTAMP),
    (8, 'Болтовое контактное соединение из алюминия без покрытия, в воздухе', 'БКС (Al)', 90, 50, FALSE, CURRENT_TIMESTAMP),
    (9, 'Токоведущая жила силового кабеля из поливинилхлоридного пластика и полиэтилена', 'Каб. нак. (ПВХ)', 70, 30, FALSE, CURRENT_TIMESTAMP),
    (10, 'Токоведущая жила силового кабеля из вулканизирующегося полиэтилена', 'Каб. нак. (ПЭ)', 90, 50, FALSE, CURRENT_TIMESTAMP),
    (11, 'Токоведущая жила силового кабеля из резины', 'Каб. нак. (Резина)', 65, 25, FALSE, CURRENT_TIMESTAMP),
    (12, 'Подшипник скольжения', 'Скольжение', 80, NULL, FALSE, CURRENT_TIMESTAMP),
    (13, 'Подшипник качения', 'Качение', 100, NULL, FALSE, CURRENT_TIMESTAMP);

-- Reset sequence for defect_type
SELECT setval('lesiv.defect_type_id_seq', (SELECT MAX(id) FROM lesiv.defect_type));

-- ============================================================================
-- 4. Populate equipment types and control point templates
-- ============================================================================

-- Equipment Type 1: Электродвигатель 0,4 кВ - подшипник качения
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (1, 'Система возбуждения', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, default_sticker_id, is_deleted)
VALUES
    (1, 'Контакт рубильника', 'Контакт рубильника', 3, FALSE),
    (1, 'Болтовое контактное соединение', 'БКС', 3, FALSE),
    (1, 'Кабельный наконечник', 'Кабельный наконечник', 2, FALSE);
 
-- Equipment Type 2: Электродвигатель 0,4 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (2, 'Электродвигатель 0,4 кВ ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, default_sticker_id, is_deleted)
VALUES
    (2, 'Передний подшипник', 'ПП', 3, FALSE),
    (2, 'Задний подшипник', 'ЗП', 3, FALSE),
    (2, 'Корпус', 'Корпус', 2, FALSE),
    (2, 'Блок распределения начала обмоток', 'БРНО', 2, FALSE);

-- Equipment Type 3: Электродвигатель 6-10 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (3, 'Электродвигатель 6-10 кВ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, default_sticker_id, is_deleted)
VALUES
    (3, 'Передний подшипник', 'ПП', 3, FALSE),
    (3, 'Задний подшипник', 'ЗП', 3, FALSE),
    (3, 'Корпус', 'Корпус', 2, FALSE),
    (3, 'Блок распределения начала обмоток', 'БРНО', 2, FALSE);

-- Equipment Type 5: Ячейка КРУ 6-10 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (5, 'Ячейка КРУ 6-10 кВ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, default_sticker_id, is_deleted)
VALUES
    (5, 'Болтовое контактное соединение', 'БКС', 1, FALSE),
    (5, 'Втычной контакт', 'Втычной контакт', 1, FALSE),
    (5, 'Кабельный наконечник', 'Кабельный наконечник', 1, FALSE),
    (5, 'Разделка кабельной муфты', 'Разделка кабельной муфты', 1, FALSE);

-- Equipment Type 6: Щит 0,4 кВ
INSERT INTO lesiv.equipment_type (id, name, is_deleted, server_modified_at)
VALUES (6, 'Щит 0,4 кВ', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.equipment_control_point_template (equipment_type_id, name, short_name, default_sticker_id, is_deleted)
VALUES
    (6, 'Болтовое контактное соединение', 'БКС', 1, FALSE),
    (6, 'Втычной контакт', 'Втычной контакт', 1, FALSE),
    (6, 'Кабельный наконечник', 'Кабельный наконечник', 1, FALSE);

-- Reset sequence for equipment_type
SELECT setval('lesiv.equipment_type_id_seq', (SELECT MAX(id) FROM lesiv.equipment_type));

-- ============================================================================
-- 5. Populate facility templates
-- ============================================================================

-- Facility Template 1: Хозяйство резервного топлива
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (1, 'Хозяйство резервного топлива', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 1
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (1, 1, 'Мазутное хозяйство', TRUE, NULL, NULL, FALSE),
    (2, 1, 'МНС - может повторяться', TRUE, NULL, 1, FALSE),
    (3, 1, 'Масло хозяйство', TRUE, NULL, NULL, FALSE),
    (4, 1, 'Насосная хозяйства дизельного топлива', TRUE, NULL, NULL, FALSE),
    (5, 1, 'Погружные насосы', TRUE, NULL, NULL, FALSE);

-- Facility Template 2: Общестанционное оборудование
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (2, 'Общестанционное оборудование', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 2
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (6, 2, 'Вентиляторная градирня', TRUE, NULL, NULL, FALSE),
    (7, 2, 'Щит 0,4 кВ', TRUE, 6, 6, FALSE),
    (8, 2, 'Двигатели 0,4 кВ', TRUE, 2, 6, FALSE),
    (9, 2, 'Пожарно насосная', TRUE, NULL, NULL, FALSE),
    (10, 2, 'Двигатели 6 кВ', TRUE, 3, 9, FALSE),
    (11, 2, 'Двигатели 0,4 кВ', TRUE, 2, 9, FALSE),
    (12, 2, 'РУ, ЗРУ 10-110 кВ', TRUE, NULL, NULL, FALSE),
    (13, 2, 'ГРУ 6-10 кВ', TRUE, NULL, NULL, FALSE),
    (14, 2, 'Дворовая пожарная', TRUE, NULL, NULL, FALSE),
    (15, 2, 'АБК', TRUE, NULL, NULL, FALSE),
    (16, 2, 'Компресорная', TRUE, NULL, NULL, FALSE),
    (17, 2, 'ГЩУ', TRUE, NULL, NULL, FALSE),
    (18, 2, 'Другое', TRUE, NULL, NULL, FALSE);

-- Facility Template 3: ПГУ (может повторятся)
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (3, 'ПГУ (может повторятся)', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 3
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (19, 3, 'Котельное отделение', TRUE, NULL, NULL, FALSE),
    (20, 3, 'Турбинное отделение', TRUE, NULL, NULL, FALSE);

-- Facility Template 4: ТГ (может повторятся)
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (4, 'ТГ (может повторятся)', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 4
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (21, 4, 'Турбинное отделение', TRUE, NULL, NULL, FALSE),
    (22, 4, 'Система возбуждения', TRUE, 1, 21, FALSE),
    (23, 4, 'Панели', TRUE, NULL, 22, FALSE),
    (24, 4, 'Сборки в помещении', TRUE, NULL, 22, FALSE),
    (25, 4, 'Другое', TRUE, NULL, 22, FALSE),
    (26, 4, 'Щит 0,4 кВ', TRUE, 6, 21, FALSE),
    (27, 4, 'Секция А', TRUE, NULL, 26, FALSE),
    (28, 4, 'Секция Б', TRUE, NULL, 26, FALSE);

-- Reset sequences for facility templates
SELECT setval('lesiv.facility_template_id_seq', (SELECT MAX(id) FROM lesiv.facility_template));
SELECT setval('lesiv.facility_template_equipment_id_seq', (SELECT MAX(id) FROM lesiv.facility_template_equipment));

-- ============================================================================
-- 6. Create 10 plants (ТЭЦ-1 to ТЭЦ-10)
-- ============================================================================

INSERT INTO lesiv.plant (id, name, is_deleted, server_modified_at)
VALUES
    (gen_random_uuid(), 'ТЭЦ-1', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-2', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-3', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-4', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-5', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-6', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-7', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-8', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-9', FALSE, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'ТЭЦ-10', FALSE, CURRENT_TIMESTAMP);

-- ============================================================================
-- 7. Create test inspectors with known credentials
-- ============================================================================

-- Insert test inspectors with bcrypt hashed passwords
-- Passwords are documented in plans/passwords.md
INSERT INTO lesiv.inspector (id, full_name, username, password_hash, server_modified_at)
VALUES
    (1, 'Test Inspector', 'test_user', '$2b$12$.Ka2kYiM7M9s0riJw6Afb.lCxPg.4.3XVl3pJ9MiTmf6Ragk3PhfC', CURRENT_TIMESTAMP),
    (2, 'Вася Пупкин', 'vpupkin', '$2b$12$HwXpgvzRi9C4vHYcnSZE3.YNFoqqj7qcb0i8F/uGT7s57anKxb8Zy', CURRENT_TIMESTAMP),
    (3, 'Евлампия Иннокеньтевна', 'evinok', '$2b$12$ZhZN0Yce0R4fAcSpbVT1zOIH3ML26IfPFcHTxqQova84S2MerskBe', CURRENT_TIMESTAMP);

-- Reset sequence for inspector
SELECT setval('lesiv.inspector_id_seq', (SELECT MAX(id) FROM lesiv.inspector));

-- ============================================================================
-- Initialization Complete
-- ============================================================================

-- Display summary
SELECT 'Sticker Types Created:' as summary, COUNT(*) as count FROM lesiv.sticker_type
UNION ALL
SELECT 'Sticker Temperature Ranges Created:', COUNT(*) FROM lesiv.sticker_temp_range
UNION ALL
SELECT 'Defect Types Created:', COUNT(*) FROM lesiv.defect_type
UNION ALL
SELECT 'Equipment Types Created:', COUNT(*) FROM lesiv.equipment_type
UNION ALL
SELECT 'Control Point Templates Created:', COUNT(*) FROM lesiv.equipment_control_point_template
UNION ALL
SELECT 'Facility Templates Created:', COUNT(*) FROM lesiv.facility_template
UNION ALL
SELECT 'Facility Template Equipment Created:', COUNT(*) FROM lesiv.facility_template_equipment
UNION ALL
SELECT 'Plants Created:', COUNT(*) FROM lesiv.plant
UNION ALL
SELECT 'Inspectors Created:', COUNT(*) FROM lesiv.inspector;
