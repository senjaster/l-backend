-- name: get_all_equipment_types
-- Get all equipment types
SELECT id, name, server_modified_at
FROM lesiv.equipment_type
ORDER BY name;

-- name: get_all_control_point_templates
-- Get all control point templates
SELECT id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id
FROM lesiv.equipment_control_point_template
ORDER BY equipment_type_id, name;