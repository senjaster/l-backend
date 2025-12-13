-- name: delete_template!
-- Delete control point template by ID
DELETE FROM lesiv.equipment_control_point_template
WHERE id = :id;