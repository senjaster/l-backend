-- Database Initialization Script
-- This script:
-- 1. Populates sticker types 
-- 2. Populates defect types 
-- 3. Populates equipment types 
-- 4. Populates facility templates 

-- ============================================================================
-- 1. Populate sticker types with all stickers
-- ============================================================================

-- Sticker Type 1: 3T 50-60-70°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (1, '3T 50-60-70°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (1, '50-60', 50, 60, FALSE),
    (1, '60-70', 60, 70, FALSE),
    (1, '> 70', 70, 999, FALSE);

-- Sticker Type 2: 3T 60-80-100°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (2, '3T 60-80-100°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (2, '60-80', 60, 80, FALSE),
    (2, '80-100', 80, 100, FALSE),
    (2, '> 100', 100, 999, FALSE);

-- Sticker Type 3: 3T 70-80-90°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (3, '3T 70-80-90°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (3, '70-80', 70, 80, FALSE),
    (3, '80-90', 80, 90, FALSE),
    (3, '> 90', 90, 999, FALSE);

-- Sticker Type 4: 4T 50-55-60-70°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (4, '4T 50-55-60-70°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (4, '50-55', 50, 55, FALSE),
    (4, '55-60', 55, 60, FALSE),
    (4, '60-70', 60, 70, FALSE),
    (4, '> 70', 70, 999, FALSE);

-- Sticker Type 5: 4T 50-60-70-80°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (5, '4T 50-60-70-80°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (5, '50-60', 50, 60, FALSE),
    (5, '60-70', 60, 70, FALSE),
    (5, '70-80', 70, 80, FALSE),
    (5, '> 80', 80, 999, FALSE);

-- Sticker Type 6: 4T 60-70-80-90°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (6, '4T 60-70-80-90°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (6, '60-70', 60, 70, FALSE),
    (6, '70-80', 70, 80, FALSE),
    (6, '80-90', 80, 90, FALSE),
    (6, '> 90', 90, 999, FALSE);

-- Sticker Type 7: 4T 60-70-75-80°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (7, '4T 60-70-75-80°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (7, '60-70', 60, 70, FALSE),
    (7, '70-75', 70, 75, FALSE),
    (7, '75-80', 75, 80, FALSE),
    (7, '> 80', 80, 999, FALSE);

-- Sticker Type 8: 4T 60-90-100-120°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (8, '4T 60-90-100-120°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (8, '60-90', 60, 90, FALSE),
    (8, '90-100', 90, 100, FALSE),
    (8, '100-120', 100, 120, FALSE),
    (8, '> 120', 120, 999, FALSE);

-- Sticker Type 9: 4T 60-80-100-120°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (9, '4T 60-80-100-120°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (9, '60-80', 60, 80, FALSE),
    (9, '80-100', 80, 100, FALSE),
    (9, '100-120', 100, 120, FALSE),
    (9, '> 120', 120, 999, FALSE);

-- Sticker Type 10: 4T 90-100-110-120°С
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES (10, '4T 90-100-110-120°С', FALSE, CURRENT_TIMESTAMP);

INSERT INTO lesiv.sticker_temp_range (sticker_id, name, t_min, t_max, is_deleted)
VALUES
    (10, '90-100', 90, 100, FALSE),
    (10, '100-110', 100, 110, FALSE),
    (10, '110-120', 110, 120, FALSE),
    (10, '> 120', 120, 999, FALSE);

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
    (2, 1, 'МНС', TRUE, NULL, 1, FALSE),
    (3, 1, 'КРУ 6 кВ', TRUE, NULL, 2, FALSE),
    (4, 1, 'Щит 0,4 кВ', TRUE, NULL, 2, FALSE),
    (5, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 2, FALSE),
    (6, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 2, FALSE),
    (7, 1, 'Другое', TRUE, NULL, 2, FALSE),
    (8, 1, 'Мазутохранилище', TRUE, NULL, 1, FALSE),
    (9, 1, 'КРУ 6 кВ', TRUE, NULL, 8, FALSE),
    (10, 1, 'Щит 0,4 кВ', TRUE, NULL, 8, FALSE),
    (11, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 8, FALSE),
    (12, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 8, FALSE),
    (13, 1, 'Другое', TRUE, NULL, 8, FALSE),
    (14, 1, 'Другое', TRUE, NULL, 1, FALSE),
    (15, 1, 'Маслохозяйство', TRUE, NULL, NULL, FALSE),
    (16, 1, 'Щит 0,4 кВ', TRUE, NULL, 15, FALSE),
    (17, 1, 'Другое', TRUE, NULL, 15, FALSE),
    (18, 1, 'Насосная хозяйства дизельного топлива', TRUE, NULL, NULL, FALSE),
    (19, 1, 'Щит 0,4 кВ', TRUE, NULL, 18, FALSE),
    (20, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 18, FALSE),
    (21, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 18, FALSE),
    (22, 1, 'Другое', TRUE, NULL, 18, FALSE),
    (23, 1, 'Погружные насосы', TRUE, NULL, NULL, FALSE),
    (24, 1, 'Щит 0,4 кВ', TRUE, NULL, 23, FALSE),
    (25, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 23, FALSE),
    (26, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 23, FALSE),
    (27, 1, 'Другое', TRUE, NULL, 23, FALSE),
    (28, 1, 'Флотаторная', TRUE, NULL, NULL, FALSE),
    (29, 1, 'Щит 0,4 кВ', TRUE, NULL, 28, FALSE),
    (30, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 28, FALSE),
    (31, 1, 'Другое', TRUE, NULL, 28, FALSE),
    (32, 1, 'Насосная бакового хозяйства', TRUE, NULL, NULL, FALSE),
    (33, 1, 'Щит 0,4 кВ', TRUE, NULL, 32, FALSE),
    (34, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 32, FALSE),
    (35, 1, 'Другое', TRUE, NULL, 32, FALSE),
    (36, 1, 'Помещение маслонасосной станции ДС и РВП', TRUE, NULL, NULL, FALSE),
    (37, 1, 'Щит 0,4 кВ', TRUE, NULL, 36, FALSE),
    (38, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 36, FALSE),
    (39, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 36, FALSE),
    (40, 1, 'Другое', TRUE, NULL, 36, FALSE),
    (41, 1, 'Насосная теплосети', TRUE, NULL, NULL, FALSE),
    (42, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 41, FALSE),
    (43, 1, 'Другое', TRUE, NULL, 41, FALSE),
    (44, 1, 'Насосная станция замазученных стоков', TRUE, NULL, NULL, FALSE),
    (45, 1, 'Щит 0,4 кВ', TRUE, NULL, 44, FALSE),
    (46, 1, 'Электродвигатели 6 кВ', TRUE, NULL, 44, FALSE),
    (47, 1, 'Электродвигатели 0,4 кВ', TRUE, NULL, 44, FALSE),
    (48, 1, 'Другое', TRUE, NULL, 44, FALSE),
    (49, 1, 'Другое', TRUE, NULL, NULL, FALSE);

-- Facility Template 2: Общестанционное оборудование
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (2, 'Общестанционное оборудование', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 2
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (50, 2, 'Пожарно насосная', TRUE, NULL, NULL, FALSE),
    (51, 2, 'Электродвигатели 6 кВ', TRUE, NULL, 50, FALSE),
    (52, 2, 'Электродвигатели 0,4 кВ', TRUE, NULL, 50, FALSE),
    (53, 2, 'Другое', TRUE, NULL, 50, FALSE),
    (54, 2, 'РУ, ЗРУ 10-110 кВ', TRUE, NULL, NULL, FALSE),
    (55, 2, 'Щит 0,4 кВ', TRUE, NULL, 54, FALSE),
    (56, 2, 'Другое', TRUE, NULL, 54, FALSE),
    (57, 2, 'ГРУ 6-10 кВ', TRUE, NULL, NULL, FALSE),
    (58, 2, 'Электрооборудование', TRUE, NULL, 57, FALSE),
    (59, 2, 'Другое', TRUE, NULL, 57, FALSE),
    (60, 2, 'Дворовая пожарная', TRUE, NULL, NULL, FALSE),
    (61, 2, 'Электродвигатели 6 кВ', TRUE, NULL, 60, FALSE),
    (62, 2, 'Электродвигатели 0,4 кВ', TRUE, NULL, 60, FALSE),
    (63, 2, 'Другое', TRUE, NULL, 60, FALSE),
    (64, 2, 'АБК', TRUE, NULL, NULL, FALSE),
    (65, 2, 'Щит 0,4 кВ', TRUE, NULL, 64, FALSE),
    (66, 2, 'Другое', TRUE, NULL, 64, FALSE),
    (67, 2, 'ГЩУ', TRUE, NULL, NULL, FALSE),
    (68, 2, 'Щит 0,4 кВ', TRUE, NULL, 67, FALSE),
    (69, 2, 'Другое', TRUE, NULL, 67, FALSE),
    (70, 2, 'Другое', TRUE, NULL, NULL, FALSE),
    (71, 2, 'Станция пенного пожаротушения', TRUE, NULL, NULL, FALSE),
    (72, 2, 'Щит 0,4 кВ', TRUE, NULL, 71, FALSE),
    (73, 2, 'Электродвигатели 6 кВ', TRUE, NULL, 71, FALSE),
    (74, 2, 'Электродвигатели 0,4 кВ', TRUE, NULL, 71, FALSE);

-- Facility Template 3: ТГ
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (3, 'ТГ', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 3
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (75, 3, 'Турбинное отделение', TRUE, NULL, NULL, FALSE),
    (76, 3, 'Система возбуждения', TRUE, NULL, 75, FALSE),
    (77, 3, 'Панели', TRUE, NULL, 76, FALSE),
    (78, 3, 'Сборки', TRUE, NULL, 76, FALSE),
    (79, 3, 'Другое', TRUE, NULL, 76, FALSE),
    (80, 3, 'Щит 0,4 кВ', TRUE, NULL, 75, FALSE),
    (81, 3, 'Секция А', TRUE, NULL, 80, FALSE),
    (82, 3, 'Секция Б', TRUE, NULL, 80, FALSE),
    (83, 3, 'Другое', TRUE, NULL, 80, FALSE),
    (84, 3, 'Электродвигатели 6 кВ', TRUE, NULL, 75, FALSE),
    (85, 3, 'Электродвигатели 0,4 кВ', TRUE, NULL, 75, FALSE),
    (86, 3, 'КРУ 6 кВ', TRUE, NULL, NULL, FALSE),
    (87, 3, 'Секция А', TRUE, NULL, 86, FALSE),
    (88, 3, 'Секция Б', TRUE, NULL, 86, FALSE);


-- Facility Template 10: Котел    
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (10, 'Котел', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Это оборудование вынесено из ТГ поэтому нумерация сбивается
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (90, 10, 'Щит 0,4 кВ', TRUE, NULL, NULL, FALSE),
    (91, 10, 'Секция А', TRUE, NULL, 90, FALSE),
    (92, 10, 'Секция Б', TRUE, NULL, 90, FALSE),
    (93, 10, 'Другое', TRUE, NULL, 90, FALSE),
    (94, 10, 'Электродвигатели 6 кВ', TRUE, NULL, NULL, FALSE),
    (95, 10, 'Электродвигатели 0,4 кВ', TRUE, NULL, NULL, FALSE),
    (96, 10, 'Тягодутьевые механизмы', TRUE, NULL, NULL, FALSE),
    (97, 10, 'Электродвигатели 6 кВ', TRUE, NULL, 96, FALSE),
    (98, 10, 'Электродвигатели 0,4 кВ', TRUE, NULL, 96, FALSE),
    (99, 10, 'Другое', TRUE, NULL, NULL, FALSE);


-- Facility Template 4: ПГУ
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (4, 'ПГУ', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 4
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (100, 4, 'Котельное отделение', TRUE, NULL, NULL, FALSE),
    (101, 4, 'Щит 0,4 кВ', TRUE, NULL, 100, FALSE),
    (102, 4, 'Секция А', TRUE, NULL, 101, FALSE),
    (103, 4, 'Секция Б', TRUE, NULL, 101, FALSE),
    (104, 4, 'Другое', TRUE, NULL, 101, FALSE),
    (105, 4, 'Электродвигатели  6 кВ', TRUE, NULL, 100, FALSE),
    (106, 4, 'Электродвигатели 0,4 кВ', TRUE, NULL, 100, FALSE),
    (107, 4, 'Другое', TRUE, NULL, 100, FALSE),
    (108, 4, 'Турбинное отделение', TRUE, NULL, NULL, FALSE),
    (109, 4, 'Система возбуждения', TRUE, NULL, 108, FALSE),
    (110, 4, 'Панели', TRUE, NULL, 109, FALSE),
    (111, 4, 'Сборки', TRUE, NULL, 109, FALSE),
    (112, 4, 'Другое', TRUE, NULL, 109, FALSE),
    (113, 4, 'Щит 0,4 кВ', TRUE, NULL, 108, FALSE),
    (114, 4, 'Секция А', TRUE, NULL, 113, FALSE),
    (115, 4, 'Секция Б', TRUE, NULL, 113, FALSE),
    (116, 4, 'Другое', TRUE, NULL, 113, FALSE),
    (117, 4, 'Электродвигатели 6 кВ', TRUE, NULL, 108, FALSE),
    (118, 4, 'Электродвигатели 0,4 кВ', TRUE, NULL, 108, FALSE),
    (119, 4, 'КРУ 6 кВ', TRUE, NULL, NULL, FALSE),
    (120, 4, 'Секция А', TRUE, NULL, 119, FALSE),
    (121, 4, 'Секция Б', TRUE, NULL, 119, FALSE);

-- Facility Template 5: КРУЭ
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (5, 'КРУЭ', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 5
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (122, 5, 'Щит 0,4 кВ', TRUE, NULL, NULL, FALSE),
    (123, 5, 'Другое', TRUE, NULL, NULL, FALSE);

-- Facility Template 6: Газовое хозяйство
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (6, 'Газовое хозяйство', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 6
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (124, 6, 'Газораспределительный пункт', TRUE, NULL, NULL, FALSE),
    (125, 6, 'Щит 0,4 кВ', TRUE, NULL, 124, FALSE),
    (126, 6, 'Другое', TRUE, NULL, 124, FALSE),
    (127, 6, 'Другое', TRUE, NULL, NULL, FALSE);

-- Facility Template 7: Угольное хозяйство
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (7, 'Угольное хозяйство', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 7
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (128, 7, 'Узлы пересыпки', TRUE, NULL, NULL, FALSE),
    (129, 7, 'Щит 0,4 кВ', TRUE, NULL, 128, FALSE),
    (130, 7, 'Другое', TRUE, NULL, 128, FALSE),
    (131, 7, 'Насосная ГЗУ', TRUE, NULL, NULL, FALSE),
    (132, 7, 'Электродвигатели 6 кВ', TRUE, NULL, 131, FALSE),
    (133, 7, 'Электродвигатели 0,4 кВ', TRUE, NULL, 131, FALSE),
    (134, 7, 'Другое', TRUE, NULL, 131, FALSE),
    (135, 7, 'Топливоподача', TRUE, NULL, NULL, FALSE),
    (136, 7, 'Щит 0,4 кВ', TRUE, NULL, 135, FALSE),
    (137, 7, 'Электродвигатели 0,4 кВ', TRUE, NULL, 135, FALSE),
    (138, 7, 'Электродвигатели 6 кВ', TRUE, NULL, 135, FALSE),
    (139, 7, 'Багерная', TRUE, NULL, NULL, FALSE),
    (140, 7, 'Электродвигатели 6 кВ', TRUE, NULL, 139, FALSE),
    (141, 7, 'Другое', TRUE, NULL, 139, FALSE),
    (142, 7, 'Другое', TRUE, NULL, NULL, FALSE);

-- Facility Template 8: Блок (is_multiple_allowed = true)
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (8, 'Блок', TRUE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 8
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (143, 8, 'Турбинное отделение', TRUE, NULL, NULL, FALSE),
    (144, 8, 'Система возбуждения', TRUE, NULL, 143, FALSE),
    (145, 8, 'Панели', TRUE, NULL, 144, FALSE),
    (146, 8, 'Сборки', TRUE, NULL, 144, FALSE),
    (147, 8, 'Другое', TRUE, NULL, 144, FALSE),
    (148, 8, 'Щит 0,4 кВ', TRUE, NULL, 143, FALSE),
    (149, 8, 'Секция А', TRUE, NULL, 148, FALSE),
    (150, 8, 'Секция Б', TRUE, NULL, 148, FALSE),
    (151, 8, 'Другое', TRUE, NULL, 148, FALSE),
    (152, 8, 'КРУ 6 кВ', TRUE, NULL, 143, FALSE),
    (153, 8, 'Секция А', TRUE, NULL, 152, FALSE),
    (154, 8, 'Секция Б', TRUE, NULL, 152, FALSE),
    (155, 8, 'Электродвигатели 6 кВ', TRUE, NULL, 143, FALSE),
    (156, 8, 'Электродвигатели 0,4 кВ', TRUE, NULL, 143, FALSE),
    (157, 8, 'Другое', TRUE, NULL, 143, FALSE),
    (158, 8, 'Котельное отделение', TRUE, NULL, NULL, FALSE),
    (159, 8, 'Щит 0,4 кВ', TRUE, NULL, 158, FALSE),
    (160, 8, 'Секция А', TRUE, NULL, 159, FALSE),
    (161, 8, 'Секция Б', TRUE, NULL, 159, FALSE),
    (162, 8, 'Другое', TRUE, NULL, 159, FALSE),
    (163, 8, 'Электродвигатели 6 кВ', TRUE, NULL, 158, FALSE),
    (164, 8, 'Электродвигатели 0,4 кВ', TRUE, NULL, 158, FALSE),
    (165, 8, 'Тягодутьевые механизмы', TRUE, NULL, 158, FALSE),
    (166, 8, 'Электродвигатели 6 кВ', TRUE, NULL, 165, FALSE),
    (167, 8, 'Электродвигатели 0,4 кВ', TRUE, NULL, 165, FALSE),
    (168, 8, 'Другое', TRUE, NULL, 158, FALSE);

-- Facility Template 9: Водоподготовка и очистка
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (9, 'Водоподготовка и очистка', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 9
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (169, 9, 'ЗУОНС', TRUE, NULL, NULL, FALSE),
    (170, 9, 'Щит 0,4 кВ', TRUE, NULL, 169, FALSE),
    (171, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 169, FALSE),
    (172, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 169, FALSE),
    (173, 9, 'Другое', TRUE, NULL, 169, FALSE),
    (174, 9, 'Вентиляторная градирня', TRUE, NULL, NULL, FALSE),
    (175, 9, 'Щит 0,4 кВ', TRUE, NULL, 174, FALSE),
    (176, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 174, FALSE),
    (177, 9, 'Другое', TRUE, NULL, 174, FALSE),
    (178, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 174, FALSE),
    (179, 9, 'ХВО', TRUE, NULL, NULL, FALSE),
    (180, 9, 'Щит 0,4 кВ', TRUE, NULL, 179, FALSE),
    (181, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 179, FALSE),
    (182, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 179, FALSE),
    (183, 9, 'Другое', TRUE, NULL, 179, FALSE),
    (184, 9, 'Очистные сооружения', TRUE, NULL, NULL, FALSE),
    (185, 9, 'Щит 0,4 кВ', TRUE, NULL, 184, FALSE),
    (186, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 184, FALSE),
    (187, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 184, FALSE),
    (188, 9, 'Другое', TRUE, NULL, 184, FALSE),
    (189, 9, 'Водонасосная станция', TRUE, NULL, NULL, FALSE),
    (190, 9, 'Щит 0,4 кВ', TRUE, NULL, 189, FALSE),
    (191, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 189, FALSE),
    (192, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 189, FALSE),
    (193, 9, 'Другое', TRUE, NULL, 189, FALSE),
    (194, 9, 'Узел нейтрализации', TRUE, NULL, NULL, FALSE),
    (195, 9, 'Щит 0,4 кВ', TRUE, NULL, 194, FALSE),
    (196, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 194, FALSE),
    (197, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 194, FALSE),
    (198, 9, 'Другое', TRUE, NULL, 194, FALSE),
    (199, 9, 'ПВК', TRUE, NULL, NULL, FALSE),
    (200, 9, 'КРУ 6 кВ', TRUE, NULL, 199, FALSE),
    (201, 9, 'Щит 0,4 кВ', TRUE, NULL, 199, FALSE),
    (202, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 199, FALSE),
    (203, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 199, FALSE),
    (204, 9, 'Другое', TRUE, NULL, 199, FALSE),
    (205, 9, 'Береговая насосная станция', TRUE, NULL, NULL, FALSE),
    (206, 9, 'Щит 0,4 кВ', TRUE, NULL, 205, FALSE),
    (207, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 205, FALSE),
    (208, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 205, FALSE),
    (209, 9, 'Другое', TRUE, NULL, 205, FALSE),
    (210, 9, 'Циркуляционая насосная', TRUE, NULL, NULL, FALSE),
    (211, 9, 'Щит 0,4 кВ', TRUE, NULL, 210, FALSE),
    (212, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 210, FALSE),
    (213, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 210, FALSE),
    (214, 9, 'Другое', TRUE, NULL, 210, FALSE),
    (215, 9, 'РВК', TRUE, NULL, NULL, FALSE),
    (216, 9, 'Щит 0,4 кВ', TRUE, NULL, 215, FALSE),
    (217, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 215, FALSE),
    (218, 9, 'Другое', TRUE, NULL, 215, FALSE),
    (219, 9, 'Электролизная', TRUE, NULL, NULL, FALSE),
    (220, 9, 'Щит 0,4 кВ', TRUE, NULL, 219, FALSE),
    (221, 9, 'Другое', TRUE, NULL, 219, FALSE),
    (222, 9, 'Золошлакоудаление', TRUE, NULL, NULL, FALSE),
    (223, 9, 'Компрессорная', TRUE, NULL, NULL, FALSE),
    (224, 9, 'Щит 0,4 кВ', TRUE, NULL, 223, FALSE),
    (225, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 223, FALSE),
    (226, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 223, FALSE),
    (227, 9, 'Другое', TRUE, NULL, 223, FALSE),
    (228, 9, 'ОСН', TRUE, NULL, NULL, FALSE),
    (229, 9, 'Щит 0,4 кВ', TRUE, NULL, 228, FALSE),
    (230, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 228, FALSE),
    (231, 9, 'Другое', TRUE, NULL, 228, FALSE),
    (232, 9, 'Водогрейная котельная', TRUE, NULL, NULL, FALSE),
    (233, 9, 'КРУ 6 кВ', TRUE, NULL, 232, FALSE),
    (234, 9, 'Секция А', TRUE, NULL, 233, FALSE),
    (235, 9, 'Секция Б', TRUE, NULL, 233, FALSE),
    (236, 9, 'Щит 0,4 кВ', TRUE, NULL, 232, FALSE),
    (237, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 232, FALSE),
    (238, 9, 'Электродвигатели 6 кВ', TRUE, NULL, 232, FALSE),
    (239, 9, 'Другое', TRUE, NULL, 232, FALSE),
    (240, 9, 'Паровая котельная', TRUE, NULL, NULL, FALSE),
    (241, 9, 'Щит 0,4 кВ', TRUE, NULL, 240, FALSE),
    (242, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 240, FALSE),
    (243, 9, 'Другое', TRUE, NULL, 240, FALSE),
    (244, 9, 'Другое', TRUE, NULL, NULL, FALSE),
    (245, 9, 'Насосная станция дождевых стоков', TRUE, NULL, NULL, FALSE),
    (246, 9, 'Щит 0,4 кВ', TRUE, NULL, 245, FALSE),
	(247, 9, 'Электродвигатели 0,4 кВ', TRUE, NULL, 245, FALSE),
	(248, 9, 'Другое', TRUE, NULL, 245, FALSE);

-- Reset sequences for facility templates
SELECT setval('lesiv.facility_template_id_seq', (SELECT COALESCE(MAX(id), 0) FROM lesiv.facility_template));
SELECT setval('lesiv.facility_template_equipment_id_seq', (SELECT COALESCE(MAX(id), 0) FROM lesiv.facility_template_equipment));

---------------------------------------------------------------------------------------------------------

update lesiv.facility_template_equipment
set 
	equipment_type_id = 3
where
	name = 'Электродвигатели 6 кВ';
	

update lesiv.facility_template_equipment
set 
	equipment_type_id = 2
where
	name = 'Электродвигатели 0,4 кВ';

update lesiv.facility_template_equipment
set 
	equipment_type_id = 5
where
	name = 'КРУ 6 кВ';	
	
update lesiv.facility_template_equipment
set 
	equipment_type_id = 6
where
	name = 'Щит 0,4 кВ';

update lesiv.facility_template_equipment
set 
	equipment_type_id = 1
where
	name = 'Система возбуждения';
            
update lesiv.facility_template_equipment as fte
set 
	equipment_type_id = fte_p.equipment_type_id
from
	lesiv.facility_template_equipment fte_p
where
	fte_p.id = fte.parent_id
	and fte.equipment_type_id is null;


update lesiv.facility_template_equipment
set 
	equipment_type_id = 6
where
	name = 'Сборки';





