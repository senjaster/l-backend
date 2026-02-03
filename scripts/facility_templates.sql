-- ============================================================================
-- Complete Facility Templates from Шаблон.txt
-- ============================================================================

-- Clear existing facility templates
DELETE FROM lesiv.facility_template_equipment;
DELETE FROM lesiv.facility_template;

-- Facility Template 1: Хозяйство резервного топлива
INSERT INTO lesiv.facility_template (id, name, is_multiple_allowed, is_deleted, server_modified_at)
VALUES (1, 'Хозяйство резервного топлива', FALSE, FALSE, CURRENT_TIMESTAMP);

-- Equipment for Facility Template 1
INSERT INTO lesiv.facility_template_equipment (id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted)
VALUES
    (1, 1, 'Мазутноехозяйство', TRUE, NULL, NULL, FALSE),
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
    (26, 1, 'Электродвигатель 0,4 кВ', TRUE, NULL, 23, FALSE),
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
    (88, 3, 'Секция Б', TRUE, NULL, 86, FALSE),
    (89, 3, 'Котельное отделение', TRUE, NULL, NULL, FALSE),
    (90, 3, 'Щит 0,4 кВ', TRUE, NULL, 89, FALSE),
    (91, 3, 'Секция А', TRUE, NULL, 90, FALSE),
    (92, 3, 'Секция Б', TRUE, NULL, 90, FALSE),
    (93, 3, 'Другое', TRUE, NULL, 90, FALSE),
    (94, 3, 'Электродвигатели 6 кВ', TRUE, NULL, 89, FALSE),
    (95, 3, 'Электродвигатели 0,4 кВ', TRUE, NULL, 89, FALSE),
    (96, 3, 'Тягодутьевые механизмы', TRUE, NULL, 89, FALSE),
    (97, 3, 'Двигатели 6 кВ', TRUE, NULL, 96, FALSE),
    (98, 3, 'Двигатели 0,4 кВ', TRUE, NULL, 96, FALSE),
    (99, 3, 'Другое', TRUE, NULL, 89, FALSE);

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
    (230, 9, 'Электродвигатели 4 кВ', TRUE, NULL, 228, FALSE),
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
	(248, 9, 'Другое', TRUE, NULL, 245, FALSE)
    
