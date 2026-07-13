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

CREATE INDEX idx_group_parent_group ON lesiv."group"(parent_group_id);
CREATE INDEX idx_group_name ON lesiv."group"(name);

ALTER TABLE lesiv.plant 
ADD COLUMN group_id UUID NULL;

ALTER TABLE lesiv.plant 
ADD CONSTRAINT fk_plant_group 
FOREIGN KEY (group_id) 
REFERENCES lesiv."group"(id) 
ON DELETE SET NULL;

CREATE INDEX idx_plant_group ON lesiv.plant(group_id);
