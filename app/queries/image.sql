-- Image aggregate queries
-- Following API design principles with optimistic concurrency control

-- name: get_by_id(id)^
SELECT
    id,
    plant_id,
    original_file_name,
    image_type,
    metadata,
    is_deleted,
    server_modified_at
FROM lesiv.image
WHERE id = :id;

-- name: get_by_plant_id(plant_id, modified_since)
-- :modified_since defaults to 1790-01-01 - only return images modified after that timestamp
SELECT
    i.id,
    i.plant_id,
    i.original_file_name,
    i.image_type,
    i.metadata,
    i.is_deleted,
    i.server_modified_at
FROM lesiv.image i
WHERE i.plant_id = :plant_id
  AND i.server_modified_at > :modified_since
ORDER BY i.server_modified_at DESC;

-- name: upsert(id, plant_id, original_file_name, image_type, metadata, is_deleted, server_modified_at)!
INSERT INTO lesiv.image (
    id,
    plant_id,
    original_file_name,
    image_type,
    metadata,
    is_deleted,
    server_modified_at
) VALUES (
    :id,
    :plant_id,
    :original_file_name,
    :image_type,
    :metadata,
    :is_deleted,
    :server_modified_at
)
ON CONFLICT (id) DO UPDATE SET
    plant_id = EXCLUDED.plant_id,
    original_file_name = EXCLUDED.original_file_name,
    image_type = EXCLUDED.image_type,
    metadata = EXCLUDED.metadata,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: delete(id)!
DELETE FROM lesiv.image
WHERE id = :id;

-- name: plant_exists(plant_id)^
SELECT EXISTS(SELECT 1 FROM lesiv.plant WHERE id = :plant_id);