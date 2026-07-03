-- Create work_log and work_log_inspector tables

CREATE TABLE lesiv.work_log (
    id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    installation_percentage DECIMAL(4,1),
    inspector_id INTEGER NOT NULL,
    plant_id UUID NOT NULL,  -- Reference to plant (no FK between aggregates)
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_work_log_inspector
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id)
);

CREATE INDEX idx_work_log_inspector ON lesiv.work_log(inspector_id);
CREATE INDEX idx_work_log_plant ON lesiv.work_log(plant_id);
CREATE INDEX idx_work_log_started_at ON lesiv.work_log(started_at);

CREATE TABLE lesiv.work_log_inspector (
    work_log_id UUID NOT NULL,
    inspector_id INTEGER NOT NULL,
    PRIMARY KEY (work_log_id, inspector_id),
    CONSTRAINT fk_work_log_inspector_work_log
        FOREIGN KEY (work_log_id) REFERENCES lesiv.work_log(id),
    CONSTRAINT fk_work_log_inspector_inspector
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id)
);

CREATE INDEX idx_work_log_inspector_work_log ON lesiv.work_log_inspector(work_log_id);
CREATE INDEX idx_work_log_inspector_inspector ON lesiv.work_log_inspector(inspector_id);
