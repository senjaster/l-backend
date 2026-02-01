-- name: get_all_defects(modified_since)
-- Get all defects (lightweight list)
-- :modified_since defaults to 1790-01-01 - only return defects modified after that timestamp
SELECT id, equipment_id, unit_name, defect_type_id, status, is_deleted
FROM lesiv.equipment_defect
WHERE server_modified_at > :modified_since
ORDER BY detected_at DESC;

-- name: get_by_plant_id(plant_id, modified_since)
-- Get all defects for a plant (full data) - joins through equipment and facility
-- :modified_since defaults to 1790-01-01 - only return defects modified after that timestamp
SELECT d.id, d.equipment_id, d.unit_name, d.defect_type_id, d.detected_at,
       d.resolved_at, d.status, d.is_deleted, d.server_modified_at
FROM lesiv.equipment_defect d
JOIN lesiv.equipment e ON d.equipment_id = e.id
JOIN lesiv.facility f ON e.facility_id = f.id
WHERE f.plant_id = :plant_id
  AND d.server_modified_at > :modified_since
ORDER BY d.detected_at DESC;

-- name: get_by_id(id)^
-- Get defect by ID
SELECT id, equipment_id, unit_name, defect_type_id, detected_at,
       resolved_at, status, is_deleted, server_modified_at
FROM lesiv.equipment_defect
WHERE id = :id;

-- name: get_plant_id_for_defect(defect_id)^
-- Get plant_id for a defect (for ownership validation) - joins through equipment and facility
SELECT f.plant_id
FROM lesiv.equipment_defect d
JOIN lesiv.equipment e ON d.equipment_id = e.id
JOIN lesiv.facility f ON e.facility_id = f.id
WHERE d.id = :defect_id;

-- name: get_plant_claim_info_for_defect(defect_id)^
-- Get plant claim info for defect (joins through equipment, facility to plant)
SELECT p.id as plant_id, p.claimed_by_user_id, p.claimed_by_device_id, p.claimed_at,
       i.username as claimed_by_username
FROM lesiv.equipment_defect d
JOIN lesiv.equipment e ON d.equipment_id = e.id
JOIN lesiv.facility f ON e.facility_id = f.id
JOIN lesiv.plant p ON f.plant_id = p.id
LEFT JOIN lesiv.inspector i ON p.claimed_by_user_id = i.id
WHERE d.id = :defect_id;

-- name: upsert_defect(id, equipment_id, unit_name, defect_type_id, detected_at, resolved_at, status, is_deleted, server_modified_at)!
-- Insert or update defect
INSERT INTO lesiv.equipment_defect (id, equipment_id, unit_name, defect_type_id,
                                    detected_at, resolved_at, status, is_deleted, server_modified_at)
VALUES (:id, :equipment_id, :unit_name, :defect_type_id,
        :detected_at, :resolved_at, :status, :is_deleted, :server_modified_at)
ON CONFLICT (id) DO UPDATE SET
    equipment_id = EXCLUDED.equipment_id,
    unit_name = EXCLUDED.unit_name,
    defect_type_id = EXCLUDED.defect_type_id,
    detected_at = EXCLUDED.detected_at,
    resolved_at = EXCLUDED.resolved_at,
    status = EXCLUDED.status,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: delete_defect(id)!
-- Logically delete defect
UPDATE lesiv.equipment_defect
SET is_deleted = true
WHERE id = :id;

