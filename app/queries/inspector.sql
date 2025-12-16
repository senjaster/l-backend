-- name: get_all_inspectors
-- Get all inspectors (without password_hash for security)
-- :modified_since defaults to 1790-01-01 - only return inspectors modified after that timestamp
SELECT
    id,
    full_name,
    username,
    server_modified_at
FROM lesiv.inspector
WHERE server_modified_at > :modified_since
ORDER BY full_name;

-- name: get_by_id^
SELECT
    id,
    full_name,
    username,
    password_hash,
    server_modified_at
FROM lesiv.inspector
WHERE id = :id;