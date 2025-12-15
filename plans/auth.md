At a high level, you implement three things in FastAPI: login endpoint, refresh endpoint, and dependency that verifies the access token on each request. Access token is short-lived JWT; refresh token is long-lived, stored in DB and rotated.

Use RS256

## Data model and config

- Create a DB table lesiv.tokens for refresh tokens:
  - id (UUID)
  - inspector_id ( FK to inspectors table )
  - device_id ( tokens are per-device! )
  - token_hash (hash of refresh token string)
  - expires_at
  - revoked (bool)
  - replaced_by_id (for rotation chains) 
  - used_at (for reuse window)
Add it to ddl.sql

- App settings (environment):
  - ACCESS_TOKEN_LIFETIME_MIN=15
  - REFRESH_TOKEN_LIFETIME_DAYS=7
  - REUSE_LIFETIME_MIN=1

## Login endpoint (POST /auth/login)

1. Verify user credentials (password) using table lesiv.inspectors
2. Generate access token (JWT) with:
   - sub = user id
   - exp = now + 15 minutes
   - other claims: device_id.
3. Generate a random opaque refresh token string (e.g., 256-bit), do not make it a JWT.
4. Hash the refresh token and save a row in DB with user id, expiry, not revoked.
5. Return tokens to client in response body

## Protected routes (access token dependency)

- Create a FastAPI dependency get_current_user:
  - Read Authorization: Bearer <access_token>.
  - Decode and verify JWT (signature, expiration, issuer, audience).
  - Load user from DB using sub claim.
  - If anything fails, raise 401
- Use this dependency in any route that needs authentication.

## Refresh endpoint (POST /auth/refresh)

This is where rotation happens.

1. Client sends current refresh token (e.g., in JSON body { "refresh_token": "..." }).
2. Look up token row by hash:
   - If no row, revoked, or expired → 401.
3. If valid:
   - Create a new access JWT (like login).
   - Generate a new refresh token string R2.
   - Hash R2, insert new DB row; mark the old row as revoked and set replaced_by_id to the new row [9][2].
4. Return new access and refresh tokens.
5. On any attempt to use an already revoked refresh token, treat it as theft (optional: revoke whole chain and force user re-login).

## Handling race conditions

- When two refresh requests happen close together:
  - Use DB transaction + unique constraints so only one rotation succeeds; others see the old token as already revoked and fail cleanly 
  - Allow a small grace window by marking old token as “used_at” and accepting reuse in a narrow time window. 


This structure gives you short-lived JWTs for API calls, robust refresh with rotation and theft detection, and a clean FastAPI separation between login, refresh, and protected resources