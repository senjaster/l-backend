-- name: get_by_id^
-- Get equipment type by ID
SELECT id, name, server_modified_at
FROM lesiv.equipment_type
WHERE id = :id;