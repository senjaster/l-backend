-- ============================================================================
-- create_inspector: Creates a new inspector with hashed password
-- ============================================================================
CREATE OR REPLACE FUNCTION lesiv.create_inspector(
    p_full_name TEXT,
    p_username TEXT,
    p_password TEXT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_inspector_id INTEGER;
BEGIN
    INSERT INTO lesiv.inspector (full_name, username, password_hash)
    VALUES (
        p_full_name,
        p_username,
        crypt(p_password, gen_salt('bf', 12))
    )
    RETURNING id INTO v_inspector_id;
    
    RETURN v_inspector_id;
END;
$$;
