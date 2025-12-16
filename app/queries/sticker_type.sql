-- name: get_sticker_types
SELECT id, name, is_deleted, server_modified_at
FROM lesiv.sticker_type

-- name: get_temp_ranges
SELECT id, sticker_id, name, t_min, t_max
FROM lesiv.sticker_temp_range
ORDER BY sticker_id, coalesce(t_min, -100);