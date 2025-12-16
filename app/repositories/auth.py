"""Authentication repository for token operations"""
from typing import Optional
from uuid import UUID
import aiosql
from app.models.auth import Token, InspectorWithPassword

# Load queries from SQL file
queries = aiosql.from_path("app/queries/auth.sql", "asyncpg")


class AuthRepository:
    """Repository for authentication token operations"""
    
    async def create_refresh_token(
        self,
        conn,
        token_id: UUID,
        inspector_id: int,
        device_id: UUID,
        token_hash: str,
        expires_at
    ) -> Token:
        """Create a new refresh token in the database"""
        row = await queries.create_refresh_token(
            conn,
            id=token_id,
            inspector_id=inspector_id,
            device_id=device_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        return Token(**row)
    
    async def get_token_by_hash(self, conn, token_hash: str) -> Optional[Token]:
        """Get a refresh token by its hash"""
        row = await queries.get_token_by_hash(conn, token_hash=token_hash)
        if row:
            return Token(**row)
        return None
    
    async def mark_token_used(self, conn, token_id: UUID) -> None:
        """Mark a token as used (for reuse detection)"""
        await queries.mark_token_used(conn, id=token_id)
    
    async def revoke_token(self, conn, token_id: UUID) -> None:
        """Revoke a single token"""
        await queries.revoke_token(conn, id=token_id)
    
    async def revoke_and_replace(self, conn, old_token_id: UUID, new_token_id: UUID) -> None:
        """Revoke old token and link to new one"""
        await queries.revoke_and_replace(
            conn,
            old_token_id=old_token_id,
            new_token_id=new_token_id
        )
    
    async def revoke_token_chain(self, conn, token_id: UUID) -> None:
        """Revoke entire token chain (for theft detection)"""
        await queries.revoke_token_chain(conn, token_id=token_id)
    
    async def get_inspector_by_username(self, conn, username: str) -> Optional[InspectorWithPassword]:
        """Get inspector by username (with password hash for authentication)"""
        row = await queries.get_inspector_by_username(conn, username=username)
        if row:
            return InspectorWithPassword(**row)
        return None
    
    async def get_inspector_by_id(self, conn, inspector_id: int) -> Optional[InspectorWithPassword]:
        """Get inspector by ID (with password hash for authentication)"""
        row = await queries.get_inspector_by_id(conn, id=inspector_id)
        if row:
            return InspectorWithPassword(**row)
        return None