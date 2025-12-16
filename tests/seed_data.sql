-- This file is loaded in conftest.py to pre-populate the database with test data

-- Seed inspectors
INSERT INTO lesiv.inspector (id, full_name, username, password_hash, server_modified_at)
VALUES
    (1, 'Test Inspector', 'test', 'hash', CURRENT_TIMESTAMP),
    (2, 'John Smith', 'jsmith', 'hash2', CURRENT_TIMESTAMP),
    (3, 'Jane Doe', 'jdoe', 'hash3', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Seed sticker types for testing

-- Insert sticker types
INSERT INTO lesiv.sticker_type (id, name, is_deleted, server_modified_at)
VALUES 
    (1, 'Low Temperature Sticker', false, '2024-01-01T00:00:00Z'),
    (2, 'High Temperature Sticker', false, '2024-01-01T00:00:00Z'),
    (3, 'Deleted Sticker', true, '2024-01-01T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- Insert temperature ranges for sticker type 1 (Low Temperature)
INSERT INTO lesiv.sticker_temp_range (id, sticker_id, name, t_min, t_max)
VALUES 
    (1, 1, 'Low', 0, 50),
    (2, 1, 'Medium', 51, 100)
ON CONFLICT (id) DO NOTHING;

-- Insert temperature ranges for sticker type 2 (High Temperature)
INSERT INTO lesiv.sticker_temp_range (id, sticker_id, name, t_min, t_max)
VALUES 
    (3, 2, 'High', 101, 150),
    (4, 2, 'Very High', 151, 200),
    (5, 2, 'Extreme', 201, 250)
ON CONFLICT (id) DO NOTHING;

-- Insert temperature range for deleted sticker type 3
INSERT INTO lesiv.sticker_temp_range (id, sticker_id, name, t_min, t_max)
VALUES
    (6, 3, 'Obsolete Range', 0, 100)
ON CONFLICT (id) DO NOTHING;

-- Seed equipment types for testing

-- Insert equipment types
INSERT INTO lesiv.equipment_type (id, name, server_modified_at)
VALUES
    (1, 'Electric Motor', '2024-01-01T00:00:00Z'),
    (2, 'Transformer', '2024-01-01T00:00:00Z'),
    (3, 'Circuit Breaker', '2024-01-01T00:00:00Z')
ON CONFLICT (id) DO NOTHING;

-- Insert control point templates for equipment type 1 (Electric Motor)
INSERT INTO lesiv.equipment_control_point_template (id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id)
VALUES
    (1, 1, 'Bearing', 'BRG', 80, 40, 1),
    (2, 1, 'Winding', 'WND', 100, 50, 2)
ON CONFLICT (id) DO NOTHING;

-- Insert control point templates for equipment type 2 (Transformer)
INSERT INTO lesiv.equipment_control_point_template (id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id)
VALUES
    (3, 2, 'Core', 'CORE', 90, 45, 1),
    (4, 2, 'Winding Primary', 'WND1', 110, 55, 2),
    (5, 2, 'Winding Secondary', 'WND2', 110, 55, 2)
ON CONFLICT (id) DO NOTHING;

-- Insert control point template for equipment type 3 (Circuit Breaker)
INSERT INTO lesiv.equipment_control_point_template (id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id)
VALUES
    (6, 3, 'Contact', 'CNT', 70, 35, 1)
ON CONFLICT (id) DO NOTHING;