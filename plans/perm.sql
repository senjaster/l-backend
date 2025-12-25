-- PostgreSQL Permissions Script
-- Grants minimal required permissions to l_app_user for the lesiv schema
-- Based on queries in app/queries folder

-- Grant usage on schema
GRANT USAGE ON SCHEMA lesiv TO l_app_user;

-- Grant usage on custom types
GRANT USAGE ON TYPE lesiv.log_entity_type TO l_app_user;
GRANT USAGE ON TYPE lesiv.log_operation TO l_app_user;
GRANT USAGE ON TYPE lesiv.defect_status TO l_app_user;
GRANT USAGE ON TYPE lesiv.inspection_status TO l_app_user;
GRANT USAGE ON TYPE lesiv.inspection_step_type TO l_app_user;
GRANT USAGE ON TYPE lesiv.defect_severity TO l_app_user;
GRANT USAGE ON TYPE lesiv.image_type TO l_app_user;

-- ============================================================================
-- Inspector Aggregate
-- ============================================================================

-- inspector: SELECT (auth queries), UPDATE (password change)
GRANT SELECT, UPDATE ON lesiv.inspector TO l_app_user;

-- tokens: SELECT, INSERT, UPDATE (auth operations)
GRANT SELECT, INSERT, UPDATE ON lesiv.tokens TO l_app_user;

-- ============================================================================
-- StickerType Aggregate
-- ============================================================================

-- sticker_type: SELECT only (read-only reference data)
GRANT SELECT ON lesiv.sticker_type TO l_app_user;

-- sticker_temp_range: SELECT only (read-only reference data)
GRANT SELECT ON lesiv.sticker_temp_range TO l_app_user;

-- ============================================================================
-- Equipment Type Aggregate
-- ============================================================================

-- equipment_type: SELECT only (read-only reference data)
GRANT SELECT ON lesiv.equipment_type TO l_app_user;

-- equipment_control_point_template: SELECT only (read-only reference data)
GRANT SELECT ON lesiv.equipment_control_point_template TO l_app_user;

-- ============================================================================
-- Log
-- ============================================================================

-- log: INSERT only (write-only audit log)
GRANT INSERT ON lesiv.log TO l_app_user;

-- Grant usage on log.id sequence for INSERT operations
GRANT USAGE ON SEQUENCE lesiv.log_id_seq TO l_app_user;

-- ============================================================================
-- Plant Aggregate
-- ============================================================================

-- plant: SELECT, INSERT, UPDATE (full CRUD via upsert, logical delete)
GRANT SELECT, INSERT, UPDATE ON lesiv.plant TO l_app_user;

-- facility: SELECT, INSERT, UPDATE (full CRUD via upsert, logical delete)
GRANT SELECT, INSERT, UPDATE ON lesiv.facility TO l_app_user;

-- ============================================================================
-- Equipment Aggregate
-- ============================================================================

-- equipment: SELECT, INSERT, UPDATE (full CRUD via upsert, logical delete)
GRANT SELECT, INSERT, UPDATE ON lesiv.equipment TO l_app_user;

-- equipment_control_point: SELECT, INSERT, UPDATE (full CRUD via upsert, logical delete)
GRANT SELECT, INSERT, UPDATE ON lesiv.equipment_control_point TO l_app_user;

-- equipment_defect: SELECT, INSERT, UPDATE (full CRUD via upsert, logical delete)
GRANT SELECT, INSERT, UPDATE ON lesiv.equipment_defect TO l_app_user;

-- ============================================================================
-- Inspection Aggregate
-- ============================================================================

-- inspection: SELECT only (referenced in equipment queries)
GRANT SELECT ON lesiv.inspection TO l_app_user;

-- inspection_step: SELECT only (may be needed for future queries)
GRANT SELECT ON lesiv.inspection_step TO l_app_user;

-- inspection_image_link: SELECT only (may be needed for future queries)
GRANT SELECT ON lesiv.inspection_image_link TO l_app_user;

-- ============================================================================
-- Image Aggregate
-- ============================================================================

-- image: SELECT, INSERT, UPDATE, DELETE (full CRUD including hard delete)
GRANT SELECT, INSERT, UPDATE, DELETE ON lesiv.image TO l_app_user;

-- ============================================================================
-- Sequences
-- ============================================================================

-- Grant usage on sequences for SERIAL columns that need INSERT
GRANT USAGE ON SEQUENCE lesiv.inspector_id_seq TO l_app_user;
GRANT USAGE ON SEQUENCE lesiv.sticker_type_id_seq TO l_app_user;
GRANT USAGE ON SEQUENCE lesiv.sticker_temp_range_id_seq TO l_app_user;
GRANT USAGE ON SEQUENCE lesiv.equipment_type_id_seq TO l_app_user;
GRANT USAGE ON SEQUENCE lesiv.equipment_control_point_template_id_seq TO l_app_user;

-- Note: UUID-based tables (plant, facility, equipment, equipment_defect, 
-- inspection, inspection_step, image, tokens) don't need sequence permissions
