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
-- StickerType Aggregate - Test Seeding (init_db.sql)
-- ============================================================================

-- Allow DELETE and INSERT on sticker_type for init_db.sql
GRANT DELETE, INSERT ON lesiv.sticker_type TO l_app_user;

-- Allow DELETE and INSERT on sticker_temp_range for init_db.sql
GRANT DELETE, INSERT ON lesiv.sticker_temp_range TO l_app_user;

-- ============================================================================
-- Equipment Type Aggregate - Test Seeding (init_db.sql)
-- ============================================================================

-- Allow DELETE and INSERT on equipment_type for init_db.sql
GRANT DELETE, INSERT ON lesiv.equipment_type TO l_app_user;

-- Allow DELETE and INSERT on equipment_control_point_template for init_db.sql
GRANT DELETE, INSERT ON lesiv.equipment_control_point_template TO l_app_user;

-- ============================================================================
-- Plant Aggregate - Test Seeding (init_db.sql)
-- ============================================================================

-- Allow DELETE and INSERT on plant for init_db.sql
GRANT DELETE, INSERT ON lesiv.plant TO l_app_user;

-- Allow DELETE and INSERT on facility for init_db.sql
GRANT DELETE, INSERT ON lesiv.facility TO l_app_user;

-- ============================================================================
-- Equipment Aggregate - Test Cleanup (init_db.sql)
-- ============================================================================

-- Allow DELETE on equipment aggregate for init_db.sql cleanup
GRANT DELETE ON lesiv.equipment_defect TO l_app_user;
GRANT DELETE ON lesiv.equipment_control_point TO l_app_user;
GRANT DELETE ON lesiv.equipment TO l_app_user;

-- ============================================================================
-- Image Aggregate - Test Cleanup (init_db.sql)
-- ============================================================================

-- Allow DELETE on image for init_db.sql cleanup
GRANT DELETE ON lesiv.image TO l_app_user;

-- ============================================================================
-- Inspection Aggregate - Test Cleanup (init_db.sql)
-- ============================================================================

-- Allow DELETE on inspection aggregate for init_db.sql cleanup
GRANT DELETE ON lesiv.inspection_image_link TO l_app_user;
GRANT DELETE ON lesiv.inspection_step TO l_app_user;
GRANT DELETE ON lesiv.inspection TO l_app_user;

-- ============================================================================
-- Log Table - Test Cleanup (init_db.sql)
-- ============================================================================

-- Allow DELETE on log for init_db.sql cleanup
GRANT DELETE ON lesiv.log TO l_app_user;

-- ============================================================================
-- Tokens - Test Cleanup
-- ============================================================================

-- Allow DELETE on tokens for auth fixture and init_db.sql
GRANT DELETE ON lesiv.tokens TO l_app_user;

-- ============================================================================
-- Sequences - Required for setval() in init_db.sql
-- ============================================================================

-- Grant USAGE on sequences so init_db.sql can reset them with setval()
GRANT USAGE, UPDATE ON SEQUENCE lesiv.sticker_type_id_seq TO l_app_user;
GRANT USAGE, UPDATE ON SEQUENCE lesiv.equipment_type_id_seq TO l_app_user;
GRANT USAGE, UPDATE ON SEQUENCE lesiv.inspector_id_seq TO l_app_user;

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
