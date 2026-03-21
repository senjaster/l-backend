-- Access level control for inspectors
-- Defines three levels: READ, INSPECT, and MODIFY

-- Create access level enum
CREATE TYPE lesiv.access_level AS ENUM ('READ', 'INSPECT', 'MODIFY');

-- Add access_level column to inspector table
ALTER TABLE lesiv.inspector
ADD COLUMN access_level lesiv.access_level NOT NULL DEFAULT 'READ';

-- Index for filtering by access level
CREATE INDEX idx_inspector_access_level ON lesiv.inspector(access_level);

COMMENT ON TYPE lesiv.access_level IS 'Access level for inspectors: READ (GET only), INSPECT (GET + inspections/defects), MODIFY (all operations)';
COMMENT ON COLUMN lesiv.inspector.access_level IS 'Access level determining what operations the inspector can perform';
