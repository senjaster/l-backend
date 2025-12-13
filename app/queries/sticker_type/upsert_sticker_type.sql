-- name: upsert_sticker_type!
-- Insert or update sticker type
INSERT INTO lesiv.sticker_type (id, name, is_deleted, last_modified_at)
VALUES (:id, :name, :is_deleted, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    is_deleted = EXCLUDED.is_deleted,
    last_modified_at = CURRENT_TIMESTAMP;