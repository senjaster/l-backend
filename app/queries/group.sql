-- name: get_by_id(id)^
-- Get group by ID
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE id = :id;

-- name: get_all_groups(modified_since)
-- Get all groups (lightweight list)
-- :modified_since defaults to 1790-01-01 - only return groups modified after that timestamp
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE server_modified_at > :modified_since
ORDER BY server_modified_at;

-- name: check_cyclic_dependency(group_id, new_parent_id)^
-- Check if moving a group would create a cyclic dependency.
-- Traverses all ancestors of new_parent_id; if group_id appears among them,
-- moving group_id under new_parent_id would create a cycle.
WITH RECURSIVE ancestors AS
    (
        SELECT id, parent_group_id
    FROM lesiv."group"
    WHERE id = :new_parent_id

UNION ALL

    SELECT g.id, g.parent_group_id
    FROM lesiv."group" g
        INNER JOIN ancestors a ON g.id = a.parent_group_id
    )
SELECT EXISTS
(
    SELECT 1
FROM ancestors
WHERE id = :group_id
)
AS would_create_cycle;

-- name: upsert_group(id, name, parent_group_id, is_deleted, server_modified_at)!
-- Insert or update group
INSERT INTO lesiv."group"
    (id, name, parent_group_id, is_deleted, server_modified_at)
VALUES
    (:id, :name, :parent_group_id, :is_deleted, :server_modified_at)
ON CONFLICT
(id) DO
UPDATE SET
    name = EXCLUDED.name,
    parent_group_id = EXCLUDED.parent_group_id,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;
