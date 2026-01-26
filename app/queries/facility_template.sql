-- name: get_all_facility_templates(modified_since)
-- Get all facility templates
-- :modified_since defaults to 1790-01-01 - only return facility templates modified after that timestamp
SELECT id, name, is_multiple_allowed, is_deleted, server_modified_at
FROM lesiv.facility_template
WHERE server_modified_at > :modified_since
ORDER BY name;

-- name: get_all_facility_template_equipment()
-- Get all facility template equipment
SELECT id, facility_template_id, name, is_container, equipment_type_id, parent_id, is_deleted
FROM lesiv.facility_template_equipment
ORDER BY facility_template_id, id;
