-- name: get_control_point_templates
-- Get control point templates for an equipment type
SELECT id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id
FROM lesiv.equipment_control_point_template
WHERE equipment_type_id = :equipment_type_id
ORDER BY name;