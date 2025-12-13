-- name: upsert_equipment_type!
-- Insert or update equipment type
INSERT INTO lesiv.equipment_type (id, name, last_modified_at)
VALUES (:id, :name, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    last_modified_at = CURRENT_TIMESTAMP;