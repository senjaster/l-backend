-- PostgreSQL DDL Script
-- Generated from dbschema.md
-- Foreign keys for UUIDs are only created within aggregates, not between them

CREATE SCHEMA if not exists lesiv;

-- ============================================================================
-- Inspector Aggregate
-- ============================================================================

CREATE TABLE lesiv.inspector (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inspector_username ON lesiv.inspector(username);

-- Refresh tokens table for authentication
CREATE TABLE lesiv.tokens (
    id UUID PRIMARY KEY,
    inspector_id INTEGER NOT NULL,
    device_id UUID NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    replaced_by_id UUID,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tokens_inspector
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id),
    CONSTRAINT fk_tokens_replaced_by
        FOREIGN KEY (replaced_by_id) REFERENCES lesiv.tokens(id)
);

CREATE INDEX idx_tokens_inspector ON lesiv.tokens(inspector_id);
CREATE INDEX idx_tokens_device ON lesiv.tokens(device_id);
CREATE INDEX idx_tokens_hash ON lesiv.tokens(token_hash);
CREATE UNIQUE INDEX idx_tokens_hash_unique ON lesiv.tokens(token_hash) WHERE NOT revoked;

-- ============================================================================
-- StickerType Aggregate
-- ============================================================================

CREATE TABLE lesiv.sticker_type (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lesiv.sticker_temp_range (
    id SERIAL PRIMARY KEY,
    sticker_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    t_min INTEGER NOT NULL,
    t_max INTEGER NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_sticker_temp_range_sticker 
        FOREIGN KEY (sticker_id) REFERENCES lesiv.sticker_type(id)
);

CREATE INDEX idx_sticker_temp_range_sticker ON lesiv.sticker_temp_range(sticker_id);

-- ============================================================================
-- Equipment Type Aggregate
-- ============================================================================

CREATE TABLE lesiv.equipment_type (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lesiv.equipment_control_point_template (
    id SERIAL PRIMARY KEY,
    equipment_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,  -- Abbreviation
    default_sticker_id INTEGER,  -- Reference to sticker_type (no FK between aggregates)
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_control_point_template_equipment_type
        FOREIGN KEY (equipment_type_id) REFERENCES lesiv.equipment_type(id)
);

CREATE INDEX idx_control_point_template_equipment_type ON lesiv.equipment_control_point_template(equipment_type_id);

-- ============================================================================
-- Facility Template Aggregate
-- ============================================================================

CREATE TABLE lesiv.facility_template (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    is_multiple_allowed BOOLEAN NOT NULL DEFAULT FALSE,  -- true = facility based on this template can be added multiple times
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lesiv.facility_template_equipment (
    id SERIAL PRIMARY KEY,
    facility_template_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    is_container BOOLEAN NOT NULL DEFAULT FALSE,  -- true = may have child equipment, but no control_points and defects
    equipment_type_id INTEGER,
    parent_id INTEGER,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_ft_eq_template
        FOREIGN KEY (facility_template_id) REFERENCES lesiv.facility_template(id),
    CONSTRAINT fk_ft_eq_type
        FOREIGN KEY (equipment_type_id) REFERENCES lesiv.equipment_type(id),
    CONSTRAINT fk_ft_eq_parent
        FOREIGN KEY (parent_id) REFERENCES lesiv.facility_template_equipment(id)
);

CREATE INDEX idx_ft_eq_template ON lesiv.facility_template_equipment(facility_template_id);

-- ============================================================================
-- Defect Type Aggregate
-- ============================================================================

CREATE TABLE lesiv.defect_type (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    t_max INTEGER NOT NULL,
    t_excess INTEGER,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Log
-- ============================================================================

CREATE TYPE lesiv.log_entity_type AS ENUM ('INSPECTOR', 'PLANT', 'FACILITY', 'EQUIPMENT', 'INSPECTION', 'IMAGE');
CREATE TYPE lesiv.log_operation AS ENUM ('CREATE', 'UPDATE', 'DELETE');

CREATE TABLE lesiv.log (
    id SERIAL PRIMARY KEY,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    plant_id UUID,  -- Reference to plant (no FK between aggregates)
    inspector_id INTEGER NOT NULL,
    CONSTRAINT fk_log_employee
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id),
    entity_id TEXT NOT NULL,  -- Can be UUID or integer depending on entity_type
    entity_type lesiv.log_entity_type NOT NULL,
    op lesiv.log_operation NOT NULL,
    data JSONB,
    message TEXT NOT NULL
);

CREATE INDEX idx_log_logged_at ON lesiv.log(logged_at);
CREATE INDEX idx_log_plant_id ON lesiv.log(plant_id);
CREATE INDEX idx_log_entity ON lesiv.log(entity_type, entity_id);
CREATE INDEX idx_log_employee ON lesiv.log(inspector_id);

-- ============================================================================
-- Plant Aggregate
-- ============================================================================

CREATE TABLE lesiv.plant (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    claimed_by_device_id UUID,
    claimed_by_user_id INTEGER,
    claimed_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plant_claimed_by_user
        FOREIGN KEY (claimed_by_user_id) REFERENCES lesiv.inspector(id),
    CONSTRAINT chk_claim_fields_consistency
        CHECK (
            (claimed_by_device_id IS NULL AND claimed_by_user_id IS NULL AND claimed_at IS NULL) OR
            (claimed_by_device_id IS NOT NULL AND claimed_by_user_id IS NOT NULL AND claimed_at IS NOT NULL)
        )
);

CREATE INDEX idx_plant_name ON lesiv.plant(name);
CREATE INDEX idx_plant_claimed_by_user ON lesiv.plant(claimed_by_user_id);

CREATE TABLE lesiv.facility (
    id UUID PRIMARY KEY,
    plant_id UUID NOT NULL,
    name TEXT NOT NULL,
    facility_template_id INTEGER,  -- Optional reference to facility_template
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_facility_plant
        FOREIGN KEY (plant_id) REFERENCES lesiv.plant(id),
    CONSTRAINT fk_facility_template
        FOREIGN KEY (facility_template_id) REFERENCES lesiv.facility_template(id)
);

CREATE INDEX idx_facility_plant ON lesiv.facility(plant_id);

-- ============================================================================
-- Equipment Aggregate
-- ============================================================================

CREATE TYPE lesiv.defect_status AS ENUM ('DETECTED', 'RESOLVED');

CREATE TABLE lesiv.equipment (
    id UUID PRIMARY KEY,
    facility_id UUID NOT NULL,  -- Reference to facility (no FK between aggregates)
    parent_id UUID,  -- Reference to facility OR equipment (polymorphic, no FK)
    name TEXT NOT NULL,
    qr_code TEXT,
    is_container BOOLEAN NOT NULL DEFAULT FALSE,  -- true = may have child equipment, but no control_points and defects
    equipment_type_id INTEGER,
    facility_template_equipment_id INTEGER,  -- Optional reference to facility_template_equipment
    estimated_point_count INTEGER,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_equipment_type
        FOREIGN KEY (equipment_type_id) REFERENCES lesiv.equipment_type(id),
    CONSTRAINT fk_equipment_facility_template_equipment
        FOREIGN KEY (facility_template_equipment_id) REFERENCES lesiv.facility_template_equipment(id)
);

CREATE INDEX idx_equipment_plant ON lesiv.equipment(facility_id);
CREATE INDEX idx_equipment_parent ON lesiv.equipment(parent_id);
CREATE INDEX idx_equipment_type ON lesiv.equipment(equipment_type_id);

CREATE TABLE lesiv.equipment_control_point (
    id UUID NOT NULL,  -- alternative key, needed only for logging
    equipment_id UUID NOT NULL,
    control_point_type TEXT NOT NULL,
    point_count INTEGER NOT NULL,
    sticker_count INTEGER NOT NULL,  -- less than or equal to point_count
    sticker_type_id INTEGER,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (id),
    UNIQUE (equipment_id, control_point_type),
    CONSTRAINT fk_control_point_equipment
        FOREIGN KEY (equipment_id) REFERENCES lesiv.equipment(id),
    CONSTRAINT fk_control_point_sticker_type
        FOREIGN KEY (sticker_type_id) REFERENCES lesiv.sticker_type(id)
);

CREATE INDEX idx_equipment_control_point_sticker_type ON lesiv.equipment_control_point(sticker_type_id);

CREATE TABLE lesiv.equipment_defect (
    id UUID PRIMARY KEY,
    equipment_id UUID NOT NULL,
    unit_name TEXT NOT NULL,  -- Specific unit name, e.g., "верхний БКС фаза В"
    t_max INTEGER,
    t_excess INTEGER,
    detected_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    status lesiv.defect_status NOT NULL DEFAULT 'DETECTED',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_defect_equipment 
        FOREIGN KEY (equipment_id) REFERENCES lesiv.equipment(id)
);

CREATE INDEX idx_equipment_defect_equipment ON lesiv.equipment_defect(equipment_id);
CREATE INDEX idx_equipment_defect_status ON lesiv.equipment_defect(status);

-- ============================================================================
-- Inspection Aggregate
-- ============================================================================

CREATE TYPE lesiv.inspection_status AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED');
CREATE TYPE lesiv.inspection_step_type AS ENUM ('GENERAL_INSPECTION', 'DEFECT_REPORT', 'DEFECT_FOLLOW_UP', 'DEFECT_UNDECIDED');
CREATE TYPE lesiv.defect_severity AS ENUM ('CRITICAL', 'EMERGENCY', 'DEVELOPING');
CREATE TYPE lesiv.step_status AS ENUM ('IN_PROGRESS', 'COMPLETED', 'FORCE_COMPLETED');

CREATE TABLE lesiv.inspection (
    id UUID PRIMARY KEY,
    equipment_id UUID NOT NULL,  -- Reference to equipment (no FK between aggregates)
    inspector_id INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status lesiv.inspection_status NOT NULL DEFAULT 'PLANNED',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inspection_inspector
        FOREIGN KEY (inspector_id) REFERENCES lesiv.inspector(id)
);

CREATE INDEX idx_inspection_equipment ON lesiv.inspection(equipment_id);
CREATE INDEX idx_inspection_inspector ON lesiv.inspection(inspector_id);
CREATE INDEX idx_inspection_status ON lesiv.inspection(status);
CREATE INDEX idx_inspection_started_at ON lesiv.inspection(started_at);

CREATE TABLE lesiv.inspection_step (
    id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    inspection_id UUID NOT NULL,
    step_number INTEGER NOT NULL,  -- for sorting
    step_type lesiv.inspection_step_type NOT NULL,
    defect_id UUID,  -- Reference to equipment_defect (no FK between aggregates)
    description TEXT,
    -- Manual thermal/electrical measurements:
    is_resolved BOOLEAN,  -- for DEFECT_FOLLOW_UP
    sticker_type_id INTEGER,
    t_sticker TEXT,
    t_environment DECIMAL(5,1),
    t_similar_unit DECIMAL(5,1),
    epsilon DECIMAL(3,2) NOT NULL DEFAULT 0.95,
    t_observed DECIMAL(5,1),
    measured_current INTEGER,
    nominal_current INTEGER,
    defect_type_id INTEGER,  -- Reference to defect_type (no FK between aggregates)
    is_sticker_present BOOLEAN,
    is_test_ready BOOLEAN,
    is_attention_required BOOLEAN NOT NULL DEFAULT FALSE,
    step_status lesiv.step_status,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_inspection_step_inspection
        FOREIGN KEY (inspection_id) REFERENCES lesiv.inspection(id),
    CONSTRAINT fk_inspection_step_sticker_type
        FOREIGN KEY (sticker_type_id) REFERENCES lesiv.sticker_type(id),
    CONSTRAINT chk_t_environment_range CHECK (t_environment IS NULL OR (t_environment >= -273.15 AND t_environment <= 9999.9)),
    CONSTRAINT chk_t_similar_unit_range CHECK (t_similar_unit IS NULL OR (t_similar_unit >= -273.15 AND t_similar_unit <= 9999.9)),
    CONSTRAINT chk_epsilon_range CHECK (epsilon >= 0 AND epsilon <= 1)
);

CREATE INDEX idx_inspection_step_inspection ON lesiv.inspection_step(inspection_id);
CREATE INDEX idx_inspection_step_number ON lesiv.inspection_step(inspection_id, step_number);
CREATE INDEX idx_inspection_step_defect ON lesiv.inspection_step(defect_id);
CREATE INDEX idx_inspection_step_sticker_type ON lesiv.inspection_step(sticker_type_id);

CREATE TABLE lesiv.inspection_image_link (
    image_id UUID NOT NULL,  -- Reference to image (no FK between aggregates)
    inspection_step_id UUID NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (image_id, inspection_step_id),
    CONSTRAINT fk_inspection_image_link_step
        FOREIGN KEY (inspection_step_id) REFERENCES lesiv.inspection_step(id)
);

CREATE INDEX idx_inspection_image_link_step ON lesiv.inspection_image_link(inspection_step_id);

-- ============================================================================
-- Image Aggregate
-- ============================================================================

CREATE TYPE lesiv.image_type AS ENUM ('VISUAL', 'THERMAL');

CREATE TABLE lesiv.image (
    id UUID PRIMARY KEY,
    plant_id UUID NOT NULL,  -- Reference to plant (no FK between aggregates), Always known
    original_file_name TEXT NOT NULL,
    image_type lesiv.image_type NOT NULL,
    metadata JSONB,
    is_deleted BOOL DEFAULT false,
    server_modified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_image_plant ON lesiv.image(plant_id);
CREATE INDEX idx_image_type ON lesiv.image(image_type);


