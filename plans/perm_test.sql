-- PostgreSQL Additional Test Permissions Script
-- Grants additional permissions to l_app_user for test environments
-- These permissions allow test fixtures to seed reference data
-- 
-- Usage: Run this script AFTER perm.sql in test environments only
-- DO NOT run this in production environments

-- ============================================================================
-- Inspector Aggregate - Test Seeding
-- ============================================================================

-- Allow all on inspector for test data seeding (conftest.py and seed_data.sql)
GRANT INSERT, UPDATE, DELETE ON lesiv.inspector TO l_app_user;

-- ============================================================================
-- StickerType Aggregate - Test Seeding
-- ============================================================================

-- Allow INSERT on sticker_type for test data seeding (seed_data.sql)
GRANT INSERT ON lesiv.sticker_type TO l_app_user;

-- Allow INSERT on sticker_temp_range for test data seeding (seed_data.sql)
GRANT INSERT ON lesiv.sticker_temp_range TO l_app_user;

-- ============================================================================
-- Equipment Type Aggregate - Test Seeding
-- ============================================================================

-- Allow INSERT on equipment_type for test data seeding (seed_data.sql)
GRANT INSERT ON lesiv.equipment_type TO l_app_user;

-- Allow INSERT on equipment_control_point_template for test data seeding (seed_data.sql)
GRANT INSERT ON lesiv.equipment_control_point_template TO l_app_user;

-- Allow DELETE on tokens for auth fixture 
GRANT DELETE ON lesiv.tokens TO l_app_user;


-- ============================================================================
-- Note on Test vs Production
-- ============================================================================

-- In production environments:
-- - Reference data (sticker_type, equipment_type, inspector) should be managed
--   by database administrators or migration scripts with elevated privileges
-- - The l_app_user should only have SELECT access to these tables
--
-- In test environments:
-- - Test fixtures need to seed reference data for consistent test execution
-- - These additional INSERT permissions enable automated test data setup
