-- name: get_template_ids
-- Get existing control point template IDs for an equipment type
SELECT id
FROM lesiv.equipment_control_point_template
WHERE equipment_type_id = :equipment_type_id;