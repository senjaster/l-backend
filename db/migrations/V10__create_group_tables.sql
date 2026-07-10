-- Create group table with hierarchical structure (simplified version)

CREATE TABLE lesiv."group" (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    parent_group_id UUID NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_group_parent_group 
        FOREIGN KEY (parent_group_id) 
        REFERENCES lesiv."group"(id)
        ON DELETE SET NULL,
    CONSTRAINT chk_group_not_self_reference 
        CHECK (id != parent_group_id)
);

-- Create indexes
CREATE INDEX idx_group_parent_group ON lesiv."group"(parent_group_id);
CREATE INDEX idx_group_name ON lesiv."group"(name);

-- Create junction table for group-plant relationship
CREATE TABLE lesiv.group_plant (
    group_id UUID NOT NULL,
    plant_id UUID NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, plant_id),
    CONSTRAINT fk_group_plant_group 
        FOREIGN KEY (group_id) 
        REFERENCES lesiv."group"(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_group_plant_plant 
        FOREIGN KEY (plant_id) 
        REFERENCES lesiv.plant(id)
        ON DELETE CASCADE
);

-- Create indexes for junction table
CREATE INDEX idx_group_plant_group ON lesiv.group_plant(group_id);
CREATE INDEX idx_group_plant_plant ON lesiv.group_plant(plant_id);

-- Comments
COMMENT ON TABLE lesiv."group" IS 'Hierarchical groups for organizing plants';
COMMENT ON TABLE lesiv.group_plant IS 'Junction table linking groups to plants';

