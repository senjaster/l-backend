-- Image aggregate queries
-- Following API design principles with optimistic concurrency control

-- name: get_by_id^
SELECT
    id,
    equipment_id,
    original_file_name,
    image_type,
    metadata,
    is_deleted,
    server_modified_at
FROM lesiv.image
WHERE id = :id;

-- name: get_by_plant_id
SELECT
    i.id,
    i.equipment_id,
    i.original_file_name,
    i.image_type,
    i.metadata,
    i.is_deleted,
    i.server_modified_at
FROM lesiv.image i
INNER JOIN lesiv.equipment e ON i.equipment_id = e.id
INNER JOIN lesiv.facility f ON e.facility_id = f.id
WHERE f.plant_id = :plant_id
ORDER BY i.server_modified_at DESC;

-- name: upsert!
INSERT INTO lesiv.image (
    id,
    equipment_id,
    original_file_name,
    image_type,
    metadata,
    is_deleted,
    server_modified_at
) VALUES (
    :id,
    :equipment_id,
    :original_file_name,
    :image_type,
    :metadata,
    :is_deleted,
    :server_modified_at
)
ON CONFLICT (id) DO UPDATE SET
    equipment_id = EXCLUDED.equipment_id,
    original_file_name = EXCLUDED.original_file_name,
    image_type = EXCLUDED.image_type,
    metadata = EXCLUDED.metadata,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: delete!
DELETE FROM lesiv.image
WHERE id = :id;