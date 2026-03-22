-- ============================================================================
-- create_inspector: Creates a new inspector with hashed password
-- ============================================================================

-- Drop old function (PostgreSQL doesn't allow changing parameters in CREATE OR REPLACE)
DROP FUNCTION IF EXISTS lesiv.create_inspector(TEXT, TEXT, TEXT);

CREATE OR REPLACE FUNCTION lesiv.create_inspector(
    p_full_name TEXT,
    p_username TEXT,
    p_password TEXT,
    p_access_level lesiv.access_level DEFAULT 'MODIFY',
    p_allow_all_plants BOOLEAN DEFAULT TRUE
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_inspector_id INTEGER;
BEGIN
    -- Create inspector with access level
    INSERT INTO lesiv.inspector (full_name, username, password_hash, access_level)
    VALUES (
        p_full_name,
        p_username,
        crypt(p_password, gen_salt('bf', 12)),
        p_access_level
    )
    RETURNING id INTO v_inspector_id;
    
    -- Grant access to all plants if requested
    IF p_allow_all_plants THEN
        INSERT INTO lesiv.inspector_plant_access (inspector_id, plant_id)
        SELECT v_inspector_id, id
        FROM lesiv.plant
        WHERE NOT is_deleted;
    END IF;
    
    RETURN v_inspector_id;
END;
$$;
