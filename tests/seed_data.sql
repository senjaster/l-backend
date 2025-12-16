-- This file is loaded in conftest.py to pre-populate the database with test data

-- Seed inspector
INSERT INTO lesiv.inspector (id, full_name, username, password_hash, server_modified_at)
VALUES (1, 'Test Inspector', 'test', 'hash', CURRENT_TIMESTAMP)
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