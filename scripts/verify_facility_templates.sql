-- ============================================================================
-- Verify Facility Templates Hierarchy
-- This query reconstructs the indented structure from the database
-- to verify that the hierarchy matches the original Шаблон.txt file
-- ============================================================================


WITH RECURSIVE hierarchy AS (
    
    -- Add equipment at root level (parent_id IS NULL)
    SELECT 
        fte.id::text || '_equipment' as unique_id,
        fte.name,
        FALSE as is_multiple_allowed,
        1 as level,
        fte.facility_template_id as template_id,
        fte.id as equipment_id,
		fte.name as path
    FROM lesiv.facility_template_equipment fte
    WHERE fte.parent_id IS NULL
        AND fte.is_deleted = FALSE
    
    UNION ALL
    
    -- Add child equipment recursively
    SELECT 
        fte.id::text || '_equipment' as unique_id,
        fte.name,
        FALSE as is_multiple_allowed,
        h.level + 1 as level,
        fte.facility_template_id as template_id,
        fte.id as equipment_id,
        h.path || ' > ' || fte.name as path
    FROM lesiv.facility_template_equipment fte
    JOIN hierarchy h ON h.equipment_id = fte.parent_id
    WHERE fte.is_deleted = FALSE
),
with_facilites as (
    SELECT 
        ft.id::text || '_template' as unique_id,
        ft.name,
        ft.is_multiple_allowed,
        0 as level,
        ft.id as template_id,
        0 as equipment_id,
        ft.name as path
    FROM lesiv.facility_template ft
    WHERE ft.is_deleted = FALSE    
    
    UNION all
    
    select * from hierarchy
)
SELECT 
    REPEAT('    ', level) || name as indented_structure
--    level,
--    template_id,
--    equipment_id,
--    CASE WHEN is_multiple_allowed THEN ' is_multiple_allowed = true' ELSE '' END as flags
FROM with_facilites
ORDER BY template_id, equipment_id;

