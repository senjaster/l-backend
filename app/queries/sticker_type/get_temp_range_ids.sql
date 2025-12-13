-- name: get_temp_range_ids
-- Get existing temperature range IDs for a sticker type
SELECT id
FROM lesiv.sticker_temp_range
WHERE sticker_id = :sticker_id;