-- name: delete_temp_range!
-- Delete temperature range by ID
DELETE FROM lesiv.sticker_temp_range
WHERE id = :id;