-- name: get_by_id(id)^
-- Get group by ID
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE id = :id;

-- name: get_by_id_active(id)^
-- Get active (not deleted) group by ID
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE id = :id AND is_deleted = false;

-- name: get_parent_id(id)
-- Get parent group ID
SELECT parent_group_id
FROM lesiv."group"
WHERE id = :id;

-- name: get_by_id_with_children(id)^
-- Get group by ID with immediate children count
SELECT g.id, g.name, g.parent_group_id, g.is_deleted, g.server_modified_at,
       COUNT(c.id) as children_count
FROM lesiv."group" g
LEFT JOIN lesiv."group" c ON c.parent_group_id = g.id AND c.is_deleted = false
WHERE g.id = :id
GROUP BY g.id;

-- name: get_children(group_id)
-- Get immediate children of a group
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE parent_group_id = :group_id AND is_deleted = false
ORDER BY name;

-- name: get_all_children_recursive(group_id)
-- Get all descendants of a group (recursive CTE)
WITH RECURSIVE group_tree AS (
    SELECT id, name, parent_group_id, is_deleted, server_modified_at
    FROM lesiv."group"
    WHERE id = :group_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.id, g.name, g.parent_group_id, g.is_deleted, g.server_modified_at
    FROM lesiv."group" g
    INNER JOIN group_tree gt ON g.parent_group_id = gt.id
    WHERE g.is_deleted = false
)
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM group_tree
WHERE id != :group_id;  -- Exclude the root itself

-- name: get_root_groups()
-- Get all root groups (no parent)
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE parent_group_id IS NULL AND is_deleted = false
ORDER BY name;

-- name: get_group_path(group_id)
-- Get the full path from root to group
WITH RECURSIVE path AS (
    SELECT id, name, parent_group_id, is_deleted, server_modified_at, 1 as depth
    FROM lesiv."group"
    WHERE id = :group_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.id, g.name, g.parent_group_id, g.is_deleted, g.server_modified_at, p.depth + 1
    FROM lesiv."group" g
    INNER JOIN path p ON g.id = p.parent_group_id
    WHERE g.is_deleted = false
)
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM path
ORDER BY depth DESC;

-- name: get_group_tree(root_id)
-- Get full tree starting from root group
WITH RECURSIVE group_tree AS (
    SELECT id, name, parent_group_id, is_deleted, server_modified_at, 0 as depth,
           ARRAY[id] as path
    FROM lesiv."group"
    WHERE id = :root_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.id, g.name, g.parent_group_id, g.is_deleted, g.server_modified_at,
           gt.depth + 1, gt.path || g.id
    FROM lesiv."group" g
    INNER JOIN group_tree gt ON g.parent_group_id = gt.id
    WHERE g.is_deleted = false
)
SELECT id, name, parent_group_id, is_deleted, server_modified_at, depth, path
FROM group_tree
ORDER BY depth, name;

-- name: get_plant_ids_by_group(group_id)
-- Get plant IDs directly in a group
SELECT plant_id
FROM lesiv.group_plant
WHERE group_id = :group_id AND is_deleted = false
ORDER BY plant_id;

-- name: get_plant_ids_by_group_recursive(group_id)
-- Get all plant IDs in a group and all its descendants
WITH RECURSIVE group_tree AS (
    SELECT id
    FROM lesiv."group"
    WHERE id = :group_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.id
    FROM lesiv."group" g
    INNER JOIN group_tree gt ON g.parent_group_id = gt.id
    WHERE g.is_deleted = false
)
SELECT DISTINCT gp.plant_id
FROM lesiv.group_plant gp
INNER JOIN group_tree gt ON gp.group_id = gt.id
WHERE gp.is_deleted = false
ORDER BY gp.plant_id;

-- name: get_plants_by_group(group_id)
-- Get full plant objects directly in a group
SELECT p.id, p.name, p.claimed_by_device_id, p.claimed_by_user_id, 
       p.claimed_at, p.is_deleted, p.server_modified_at
FROM lesiv.plant p
INNER JOIN lesiv.group_plant gp ON gp.plant_id = p.id
WHERE gp.group_id = :group_id 
  AND gp.is_deleted = false
  AND p.is_deleted = false
ORDER BY p.name;

-- name: check_plants_exist(plant_ids)
-- Check which plants exist
SELECT id
FROM lesiv.plant
WHERE id = ANY(:plant_ids::UUID[]) AND is_deleted = false;

-- name: get_all_groups(modified_since)
-- Get all groups (lightweight list)
-- :modified_since defaults to 1790-01-01 - only return groups modified after that timestamp
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE server_modified_at > :modified_since
ORDER BY server_modified_at;

-- name: get_groups_by_parent(parent_id)
-- Get groups by parent ID (including deleted)
SELECT id, name, parent_group_id, is_deleted, server_modified_at
FROM lesiv."group"
WHERE parent_group_id = :parent_id
ORDER BY name;

--- name: check_cyclic_dependency(group_id, new_parent_id)^
-- Check if moving a group would create a cyclic dependency
WITH RECURSIVE ancestors AS (
    SELECT parent_group_id
    FROM lesiv."group"
    WHERE id = :new_parent_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.parent_group_id
    FROM lesiv."group" g
    INNER JOIN ancestors a ON g.id = a.parent_group_id
    WHERE g.is_deleted = false
)
SELECT EXISTS (
    SELECT 1 FROM ancestors WHERE parent_group_id = :group_id
) as would_create_cycle;

-- name: upsert_group(id, name, parent_group_id, is_deleted, server_modified_at)!
-- Insert or update group
INSERT INTO lesiv."group" (id, name, parent_group_id, is_deleted, server_modified_at)
VALUES (:id, :name, :parent_group_id, :is_deleted, :server_modified_at)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    parent_group_id = EXCLUDED.parent_group_id,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: delete_group(id)!
-- Logically delete group (soft delete)
UPDATE lesiv."group"
SET is_deleted = true,
    server_modified_at = CURRENT_TIMESTAMP
WHERE id = :id;

-- name: delete_group_hard(id)!
-- Permanently delete group (hard delete) - cascades to group_plant via FK
DELETE FROM lesiv."group"
WHERE id = :id;

-- name: soft_delete_subgroups(parent_id)!
-- Recursively soft delete all subgroups
WITH RECURSIVE subgroups AS (
    SELECT id
    FROM lesiv."group"
    WHERE id = :parent_id AND is_deleted = false
    
    UNION ALL
    
    SELECT g.id
    FROM lesiv."group" g
    INNER JOIN subgroups s ON g.parent_group_id = s.id
    WHERE g.is_deleted = false
)
UPDATE lesiv."group"
SET is_deleted = true,
    server_modified_at = CURRENT_TIMESTAMP
WHERE id IN (SELECT id FROM subgroups);

-- name: add_plant_to_group(group_id, plant_id)!
-- Add plant to group
INSERT INTO lesiv.group_plant (group_id, plant_id, is_deleted, server_modified_at)
VALUES (:group_id, :plant_id, false, CURRENT_TIMESTAMP)
ON CONFLICT (group_id, plant_id) DO UPDATE SET
    is_deleted = false,
    server_modified_at = CURRENT_TIMESTAMP;

-- name: remove_plant_from_group(group_id, plant_id)!
-- Soft remove plant from group
UPDATE lesiv.group_plant
SET is_deleted = true,
    server_modified_at = CURRENT_TIMESTAMP
WHERE group_id = :group_id AND plant_id = :plant_id;

-- name: remove_plant_from_group_hard(group_id, plant_id)!
-- Permanently remove plant from group
DELETE FROM lesiv.group_plant
WHERE group_id = :group_id AND plant_id = :plant_id;

-- name: remove_all_plants_from_group(group_id)!
-- Soft remove all plants from group
UPDATE lesiv.group_plant
SET is_deleted = true,
    server_modified_at = CURRENT_TIMESTAMP
WHERE group_id = :group_id AND is_deleted = false;

-- name: remove_all_plants_from_group_hard(group_id)!
-- Permanently remove all plants from group
DELETE FROM lesiv.group_plant
WHERE group_id = :group_id;

-- name: check_group_has_plants(group_id)^
-- Check if group has any plants (directly)
SELECT EXISTS (
    SELECT 1
    FROM lesiv.group_plant
    WHERE group_id = :group_id AND is_deleted = false
) as has_plants;

-- name: check_group_has_children(group_id)^
-- Check if group has any children
SELECT EXISTS (
    SELECT 1
    FROM lesiv."group"
    WHERE parent_group_id = :group_id AND is_deleted = false
) as has_children;

-- name: move_group(group_id, new_parent_id)!
-- Move group to a new parent
UPDATE lesiv."group"
SET parent_group_id = :new_parent_id,
    server_modified_at = CURRENT_TIMESTAMP
WHERE id = :group_id;

-- name: bulk_add_plants_to_group(group_id, plant_ids)!
-- Bulk add plants to group
INSERT INTO lesiv.group_plant (group_id, plant_id, is_deleted, server_modified_at)
SELECT :group_id, plant_id, false, CURRENT_TIMESTAMP
FROM unnest(CAST(:plant_ids AS UUID[])) AS plant_id
ON CONFLICT (group_id, plant_id) DO UPDATE SET
    is_deleted = false,
    server_modified_at = CURRENT_TIMESTAMP;

-- name: bulk_remove_plants_from_group(group_id, plant_ids)!
-- Bulk soft remove plants from group
UPDATE lesiv.group_plant
SET is_deleted = true,
    server_modified_at = CURRENT_TIMESTAMP
WHERE group_id = :group_id 
AND plant_id = ANY(:plant_ids)
AND is_deleted = false;

-- name: get_groups_by_plant(plant_id)
-- Get all groups containing a plant
SELECT g.id, g.name, g.parent_group_id, g.is_deleted, g.server_modified_at
FROM lesiv."group" g
INNER JOIN lesiv.group_plant gp ON gp.group_id = g.id
WHERE gp.plant_id = :plant_id 
AND gp.is_deleted = false
AND g.is_deleted = false
ORDER BY g.name;

-- name: get_group_plant_count(group_id)^
-- Get count of plants in a group (direct only)
SELECT COUNT(*) as plant_count
FROM lesiv.group_plant
WHERE group_id = :group_id AND is_deleted = false;

-- name: get_all_plant_ids_by_group(group_id)
-- Get plant IDs directly in a group (return as array)
SELECT ARRAY(
    SELECT plant_id
    FROM lesiv.group_plant
    WHERE group_id = :group_id AND is_deleted = false
    ORDER BY plant_id
) as plant_ids;

-- name: get_group_hierarchy_depth(group_id)^
-- Get the depth of a group in the hierarchy
WITH RECURSIVE ancestors AS (
    SELECT id, parent_group_id, 0 as depth
    FROM lesiv."group"
    WHERE id = :group_id
    
    UNION ALL
    
    SELECT g.id, g.parent_group_id, a.depth + 1
    FROM lesiv."group" g
    INNER JOIN ancestors a ON g.id = a.parent_group_id
    WHERE g.id = a.parent_group_id
)
SELECT MAX(depth) as hierarchy_depth
FROM ancestors;