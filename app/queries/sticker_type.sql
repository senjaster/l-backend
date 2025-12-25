-- name: get_sticker_types
-- :modified_since defaults to 1790-01-01 - only return sticker types modified after that timestamp
SELECT id, name, is_deleted, server_modified_at
FROM lesiv.sticker_type
WHERE server_modified_at > :modified_since

-- name: get_temp_ranges
SELECT id, sticker_id, name, t_min, t_max, is_deleted
FROM lesiv.sticker_temp_range
ORDER BY sticker_id, coalesce(t_min, -100);