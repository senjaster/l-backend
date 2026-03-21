-- Test Data Initialization Script
-- This script is run during test setup to populate test-only data
-- Note: Dictionary data (sticker types, defect types, equipment types, facility templates)
-- is already loaded by V3__init_dictionaries.sql migration

-- ============================================================================
-- Create test inspectors with known credentials
-- ============================================================================

-- Insert test inspectors with bcrypt hashed passwords
-- Password for all test users: "password123"
-- Hash generated with: bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=12))

INSERT INTO lesiv.inspector (id, full_name, username, password_hash, server_modified_at)
VALUES
    (1, 'Test Inspector', 'test_user', '$2b$12$.Ka2kYiM7M9s0riJw6Afb.lCxPg.4.3XVl3pJ9MiTmf6Ragk3PhfC', CURRENT_TIMESTAMP),
    (2, 'Вася Пупкин', 'vpupkin', '$2b$12$HwXpgvzRi9C4vHYcnSZE3.YNFoqqj7qcb0i8F/uGT7s57anKxb8Zy', CURRENT_TIMESTAMP),
    (3, 'Евлампия Иннокеньтевна', 'evinok', '$2b$12$ZhZN0Yce0R4fAcSpbVT1zOIH3ML26IfPFcHTxqQova84S2MerskBe', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Reset sequence for inspector to ensure new inspectors get IDs starting from 4
SELECT setval('lesiv.inspector_id_seq', (SELECT MAX(id) FROM lesiv.inspector));
