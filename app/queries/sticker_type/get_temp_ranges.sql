-- name: get_temp_ranges
-- Get temperature ranges for a sticker type
SELECT id, sticker_id, name, t_min, t_max
FROM lesiv.sticker_temp_range
WHERE sticker_id = :sticker_id
ORDER BY t_min;