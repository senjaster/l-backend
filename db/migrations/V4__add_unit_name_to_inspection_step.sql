-- Add unit_name field to inspection_step table
-- This field will store the specific unit name (e.g., "верхний БКС фаза В")

-- Add the column
ALTER TABLE lesiv.inspection_step
ADD COLUMN unit_name TEXT;

-- Copy unit_name values from related defect records
-- Only update steps that have a defect_id reference
UPDATE lesiv.inspection_step s
SET unit_name = d.unit_name
FROM lesiv.equipment_defect d
WHERE s.defect_id = d.id
  AND s.defect_id IS NOT NULL;
