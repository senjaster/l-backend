-- name: delete_equipment_type!
-- Delete equipment type (no is_deleted flag for equipment_type)
DELETE FROM lesiv.equipment_type
WHERE id = :id;