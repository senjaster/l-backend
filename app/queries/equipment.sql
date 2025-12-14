-- name: get_all_equipment
-- Get all equipment (lightweight list)
SELECT id, plant_id, parent_id, name, qr_code, is_container, equipment_type_id, is_deleted
FROM lesiv.equipment
ORDER BY name;

-- name: get_by_plant_id
-- Get all equipment for a plant
SELECT id, plant_id, parent_id, name, qr_code, is_container, equipment_type_id, is_deleted
FROM lesiv.equipment
WHERE plant_id = :plant_id
ORDER BY name;

-- name: get_by_id^
-- Get equipment by ID
SELECT id, plant_id, parent_id, name, qr_code, is_container, equipment_type_id,
       estimated_point_count, is_deleted, server_modified_at
FROM lesiv.equipment
WHERE id = :id;

-- name: get_control_points
-- Get control points for equipment
SELECT id, equipment_id, control_point_type, point_count, sticker_count, 
       sticker_type_id, t_max, t_excess, is_deleted
FROM lesiv.equipment_control_point
WHERE equipment_id = :equipment_id
ORDER BY control_point_type;

-- name: get_control_point_ids
-- Get control point IDs for equipment (for sync)
SELECT id
FROM lesiv.equipment_control_point
WHERE equipment_id = :equipment_id;

-- name: get_control_point_equipment_id^
-- Get the equipment_id for a control point (to check ownership)
SELECT equipment_id
FROM lesiv.equipment_control_point
WHERE id = :control_point_id;

-- name: get_defects
-- Get defects for equipment
SELECT id, equipment_id, unit_name, t_max, t_excess, detected_at, 
       resolved_at, status, is_deleted
FROM lesiv.equipment_defect
WHERE equipment_id = :equipment_id
ORDER BY detected_at DESC;

-- name: get_defect_ids
-- Get defect IDs for equipment (for sync)
SELECT id
FROM lesiv.equipment_defect
WHERE equipment_id = :equipment_id;

-- name: get_defect_equipment_id^
-- Get the equipment_id for a defect (to check ownership)
SELECT equipment_id
FROM lesiv.equipment_defect
WHERE id = :defect_id;

-- name: get_inspection_ids
-- Get inspection IDs for equipment
SELECT id
FROM lesiv.inspection
WHERE equipment_id = :equipment_id AND is_deleted = false
ORDER BY started_at DESC;

-- name: upsert_equipment!
-- Insert or update equipment
INSERT INTO lesiv.equipment (id, plant_id, parent_id, name, qr_code, is_container, 
                             equipment_type_id, estimated_point_count, 
                             is_deleted, server_modified_at)
VALUES (:id, :plant_id, :parent_id, :name, :qr_code, :is_container, 
        :equipment_type_id, :estimated_point_count, 
        :is_deleted, :server_modified_at)
ON CONFLICT (id) DO UPDATE SET
    plant_id = EXCLUDED.plant_id,
    parent_id = EXCLUDED.parent_id,
    name = EXCLUDED.name,
    qr_code = EXCLUDED.qr_code,
    is_container = EXCLUDED.is_container,
    equipment_type_id = EXCLUDED.equipment_type_id,
    estimated_point_count = EXCLUDED.estimated_point_count,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: upsert_control_point!
-- Insert or update control point (match by ID, not by equipment_id + control_point_type)
INSERT INTO lesiv.equipment_control_point (id, equipment_id, control_point_type,
                                           point_count, sticker_count, sticker_type_id,
                                           t_max, t_excess, is_deleted)
VALUES (:id, :equipment_id, :control_point_type,
        :point_count, :sticker_count, :sticker_type_id,
        :t_max, :t_excess, :is_deleted)
ON CONFLICT (id) DO UPDATE SET
    equipment_id = EXCLUDED.equipment_id,
    control_point_type = EXCLUDED.control_point_type,
    point_count = EXCLUDED.point_count,
    sticker_count = EXCLUDED.sticker_count,
    sticker_type_id = EXCLUDED.sticker_type_id,
    t_max = EXCLUDED.t_max,
    t_excess = EXCLUDED.t_excess,
    is_deleted = EXCLUDED.is_deleted;

-- name: upsert_defect!
-- Insert or update defect
INSERT INTO lesiv.equipment_defect (id, equipment_id, unit_name, t_max, t_excess,
                                    detected_at, resolved_at, status, is_deleted)
VALUES (:id, :equipment_id, :unit_name, :t_max, :t_excess,
        :detected_at, :resolved_at, :status, :is_deleted)
ON CONFLICT (id) DO UPDATE SET
    unit_name = EXCLUDED.unit_name,
    t_max = EXCLUDED.t_max,
    t_excess = EXCLUDED.t_excess,
    detected_at = EXCLUDED.detected_at,
    resolved_at = EXCLUDED.resolved_at,
    status = EXCLUDED.status,
    is_deleted = EXCLUDED.is_deleted;

-- name: delete_equipment!
-- Logically delete equipment
UPDATE lesiv.equipment
SET is_deleted = true
WHERE id = :id;

-- name: mark_control_point_deleted!
-- Mark control point as deleted (logical deletion)
UPDATE lesiv.equipment_control_point
SET is_deleted = true
WHERE id = :id;

-- name: mark_defect_deleted!
-- Mark defect as deleted (logical deletion)
UPDATE lesiv.equipment_defect
SET is_deleted = true
WHERE id = :id;