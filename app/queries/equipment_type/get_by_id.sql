-- name: get_by_id^
-- Get equipment type by ID
SELECT id, name, last_modified_at
FROM lesiv.equipment_type
WHERE id = :id;