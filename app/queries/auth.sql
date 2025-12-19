-- name: create_refresh_token<!
INSERT INTO lesiv.tokens (
    id, inspector_id, device_id, token_hash, 
    expires_at, revoked, created_at
)
VALUES (:id, :inspector_id, :device_id, :token_hash, :expires_at, FALSE, CURRENT_TIMESTAMP)
RETURNING id, inspector_id, device_id, token_hash, expires_at, revoked, replaced_by_id, used_at, created_at;

-- name: get_token_by_hash^
SELECT id, inspector_id, device_id, token_hash, expires_at, revoked, replaced_by_id, used_at, created_at
FROM lesiv.tokens
WHERE token_hash = :token_hash;

-- name: mark_token_used!
UPDATE lesiv.tokens
SET used_at = CURRENT_TIMESTAMP
WHERE id = :id;

-- name: revoke_token!
UPDATE lesiv.tokens
SET revoked = TRUE
WHERE id = :id;

-- name: revoke_and_replace!
UPDATE lesiv.tokens
SET revoked = TRUE, replaced_by_id = :new_token_id
WHERE id = :old_token_id;

-- name: revoke_token_chain!
-- Revoke entire token chain starting from root
WITH RECURSIVE chain AS (
    -- Find the root by following replaced_by_id backwards
    SELECT id, replaced_by_id, 0 as depth
    FROM lesiv.tokens
    WHERE id = :token_id
    
    UNION ALL
    
    -- Follow backwards to find older tokens
    SELECT t.id, t.replaced_by_id, c.depth - 1
    FROM lesiv.tokens t
    JOIN chain c ON t.replaced_by_id = c.id
),
root AS (
    SELECT id FROM chain ORDER BY depth ASC LIMIT 1
),
forward_chain AS (
    -- Start with the root
    SELECT id, replaced_by_id
    FROM lesiv.tokens
    WHERE id = (SELECT id FROM root)
    
    UNION ALL
    
    -- Follow forward through replacements
    SELECT t.id, t.replaced_by_id
    FROM lesiv.tokens t
    JOIN forward_chain fc ON t.id = fc.replaced_by_id
)
UPDATE lesiv.tokens
SET revoked = TRUE
WHERE id IN (SELECT id FROM forward_chain);

-- name: get_inspector_by_username^
SELECT id, full_name, username, password_hash, server_modified_at
FROM lesiv.inspector
WHERE username = :username;

-- name: get_inspector_by_id^
SELECT id, full_name, username, password_hash, server_modified_at
FROM lesiv.inspector
WHERE id = :id;

-- name: update_password^
UPDATE lesiv.inspector
SET password_hash = :new_password_hash, server_modified_at = CURRENT_TIMESTAMP
WHERE id = :id AND password_hash = :old_password_hash
RETURNING id;

-- name: revoke_all_tokens_for_inspector!
UPDATE lesiv.tokens
SET revoked = TRUE
WHERE inspector_id = :inspector_id;