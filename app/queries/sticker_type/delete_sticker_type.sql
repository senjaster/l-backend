-- name: delete_sticker_type!
-- Logically delete sticker type
UPDATE lesiv.sticker_type
SET is_deleted = true,
    last_modified_at = CURRENT_TIMESTAMP
WHERE id = :id;