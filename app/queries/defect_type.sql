-- name: get_all_defect_types(modified_since)
-- Get all defect types
-- :modified_since defaults to 1790-01-01 - only return defect types modified after that timestamp
SELECT id, name, short_name, t_max, t_excess, is_deleted, server_modified_at
FROM lesiv.defect_type
WHERE server_modified_at > :modified_since
ORDER BY server_modified_at;
