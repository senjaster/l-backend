-- ============================================================================
-- change_password: Changes password for an existing inspector
-- ============================================================================
CREATE OR REPLACE FUNCTION lesiv.change_password(
    p_username TEXT,
    p_password TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_rows_affected INTEGER;
BEGIN
    UPDATE lesiv.inspector
    SET password_hash = crypt(p_password, gen_salt('bf', 12)),
        server_modified_at = CURRENT_TIMESTAMP
    WHERE username = p_username
      AND is_deleted = FALSE;
    
    GET DIAGNOSTICS v_rows_affected = ROW_COUNT;
    
    RETURN v_rows_affected > 0;
END;
$$;
