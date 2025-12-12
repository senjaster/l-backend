-- name: get_by_id^
SELECT
    id,
    equipment_id,
    original_file_name,
    image_type,
    metadata,
    last_modified_at
FROM lesiv.image
WHERE id = :id;