-- name: get_all_inspectors
-- Get all inspectors (without password_hash for security)
SELECT
    id,
    full_name,
    username,
    server_modified_at
FROM lesiv.inspector
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