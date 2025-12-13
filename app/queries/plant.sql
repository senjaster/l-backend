-- name: get_by_id^
-- Get plant by ID
SELECT id, name, locked_by_device_id, locked_by_user_id, locked_at, is_deleted, last_modified_at
FROM lesiv.plant
WHERE id = :id;

-- name: get_facilities
-- Get facilities for a plant
SELECT id, name, is_deleted
FROM lesiv.facility
WHERE plant_id = :plant_id
ORDER BY name;

-- name: get_facility_ids
-- Get facility IDs for a plant
SELECT id
FROM lesiv.facility
WHERE plant_id = :plant_id;

-- name: get_equipment_ids_by_facility
-- Get equipment IDs for a facility
SELECT id
FROM lesiv.equipment
WHERE parent_id = :facility_id AND is_deleted = false;

-- name: get_facility_plant_id^
-- Get the plant_id for a facility (to check ownership)
SELECT plant_id
FROM lesiv.facility
WHERE id = :facility_id;

-- name: get_all_plants
-- Get all plants (lightweight list)
SELECT id, name, is_deleted, locked_by_device_id, locked_by_user_id, locked_at
FROM lesiv.plant
ORDER BY name;

-- name: upsert_plant!
-- Insert or update plant
INSERT INTO lesiv.plant (id, name, locked_by_device_id, locked_by_user_id, locked_at, is_deleted, last_modified_at)
VALUES (:id, :name, :locked_by_device_id, :locked_by_user_id, :locked_at, :is_deleted, :last_modified_at)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    locked_by_device_id = EXCLUDED.locked_by_device_id,
    locked_by_user_id = EXCLUDED.locked_by_user_id,
    locked_at = EXCLUDED.locked_at,
    is_deleted = EXCLUDED.is_deleted,
    last_modified_at = EXCLUDED.last_modified_at;

-- name: upsert_facility!
-- Insert or update facility
INSERT INTO lesiv.facility (id, plant_id, name, is_deleted)
VALUES (:id, :plant_id, :name, :is_deleted)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    is_deleted = EXCLUDED.is_deleted;

-- name: delete_plant!
-- Logically delete plant
UPDATE lesiv.plant
SET is_deleted = true
WHERE id = :id;

-- name: mark_facility_deleted!
-- Mark facility as deleted (logical deletion)
UPDATE lesiv.facility
SET is_deleted = true
WHERE id = :id;

-- name: lock_plant!
-- Lock plant for editing
UPDATE lesiv.plant
SET locked_by_device_id = :device_id,
    locked_by_user_id = :user_id,
    locked_at = :locked_at
WHERE id = :id;

-- name: unlock_plant!
-- Unlock plant
UPDATE lesiv.plant
SET locked_by_device_id = NULL,
    locked_by_user_id = NULL,
    locked_at = NULL
WHERE id = :id;