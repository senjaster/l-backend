-- name: get_by_id^
SELECT
    id,
    full_name,
    username,
    password_hash,
    last_modified_at
FROM lesiv.inspector
WHERE id = :id;