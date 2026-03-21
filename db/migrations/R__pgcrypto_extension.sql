-- Enable pgcrypto extension for password hashing
-- Required by stored procedures that handle password operations

CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA public;
