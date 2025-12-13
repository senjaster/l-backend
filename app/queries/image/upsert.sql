-- name: upsert!
INSERT INTO lesiv.image (
    id,
    equipment_id,
    original_file_name,
    image_type,
    metadata,
    server_modified_at
) VALUES (
    :id,
    :equipment_id,
    :original_file_name,
    :image_type,
    :metadata,
    CURRENT_TIMESTAMP
)
ON CONFLICT (id) DO UPDATE SET
    equipment_id = EXCLUDED.equipment_id,
    original_file_name = EXCLUDED.original_file_name,
    image_type = EXCLUDED.image_type,
    metadata = EXCLUDED.metadata,
    server_modified_at = CURRENT_TIMESTAMP;