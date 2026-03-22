-- Grant existing inspectors full access (backward compatibility)
-- Before the permission system, all inspectors could access all plants and perform all operations

-- Set all existing inspectors to MODIFY level
UPDATE lesiv.inspector
SET access_level = 'MODIFY'
WHERE access_level = 'READ';

-- Grant all existing inspectors access to all existing plants
INSERT INTO lesiv.inspector_plant_access (inspector_id, plant_id)
SELECT i.id, p.id
FROM lesiv.inspector i
CROSS JOIN lesiv.plant p
ON CONFLICT (inspector_id, plant_id) DO NOTHING;

COMMENT ON TABLE lesiv.inspector_plant_access IS 'Controls which inspectors can access which plants. New inspectors get access when they create or claim plants.';
