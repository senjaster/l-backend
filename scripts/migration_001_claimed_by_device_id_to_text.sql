-- Migration: Change device_id fields from UUID to TEXT
-- Date: 2026-02-06
-- Description: Allow device_id fields to accept any text value instead of only UUID
--              This affects both tokens.device_id and plant.claimed_by_device_id

BEGIN;

-- Change tokens.device_id from UUID to TEXT
ALTER TABLE lesiv.tokens
    ALTER COLUMN device_id TYPE TEXT USING device_id::TEXT;

-- Change plant.claimed_by_device_id from UUID to TEXT
ALTER TABLE lesiv.plant
    ALTER COLUMN claimed_by_device_id TYPE TEXT USING claimed_by_device_id::TEXT;

COMMIT;
