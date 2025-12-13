-- name: get_by_id^
-- Get sticker type by ID
SELECT id, name, is_deleted, server_modified_at
FROM lesiv.sticker_type
WHERE id = :id;