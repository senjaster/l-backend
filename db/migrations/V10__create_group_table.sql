CREATE TABLE lesiv."group" (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    parent_group_id UUID NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_group_parent_group 
        FOREIGN KEY (parent_group_id) 
        REFERENCES lesiv."group"(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_group_parent_group ON lesiv."group"(parent_group_id);
CREATE INDEX idx_group_name ON lesiv."group"(name);

ALTER TABLE lesiv.plant 
ADD COLUMN group_id UUID NULL;

CREATE INDEX idx_plant_group ON lesiv.plant(group_id);
