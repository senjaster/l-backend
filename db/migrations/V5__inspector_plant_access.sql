-- Inspector-Plant access control table
-- Plants are only visible to inspectors listed in this table

CREATE TABLE lesiv.inspector_plant_access (
    inspector_id INTEGER NOT NULL,
    plant_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inspector_id, plant_id),
    CONSTRAINT fk_inspector_plant_access_inspector
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id),
    CONSTRAINT fk_inspector_plant_access_plant
        FOREIGN KEY (plant_id) REFERENCES lesiv.plant(id)
);

CREATE INDEX idx_inspector_plant_access_plant ON lesiv.inspector_plant_access(plant_id);
CREATE INDEX idx_inspector_plant_access_inspector ON lesiv.inspector_plant_access(inspector_id);

COMMENT ON TABLE lesiv.inspector_plant_access IS 'Junction table controlling which inspectors can access which plants';
COMMENT ON COLUMN lesiv.inspector_plant_access.inspector_id IS 'Inspector who has access';
COMMENT ON COLUMN lesiv.inspector_plant_access.plant_id IS 'Plant that is accessible';
