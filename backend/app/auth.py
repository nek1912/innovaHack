import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.hash import bcrypt
from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.owner import Agent, Owner


def _auth_error(status_code: int, error: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": error, "message": message},
    )


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    return f"af_{secrets.token_urlsafe(32)}"


def create_owner_token(owner_id: uuid.UUID) -> str:
    payload = {
        "sub": str(owner_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_owner_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise _auth_error(401, "token_expired", "Authentication token has expired")
    except (jwt.InvalidTokenError, KeyError):
        raise _auth_error(401, "invalid_token", "Invalid authentication token")


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)


async def get_current_owner(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Owner:
    if not authorization or not authorization.startswith("Bearer "):
        raise _auth_error(401, "missing_token", "Authorization token is required")
    token = authorization.removeprefix("Bearer ")
    owner_id = decode_owner_token(token)
    owner = await db.get(Owner, owner_id)
    if not owner:
        raise _auth_error(401, "owner_not_found", "Owner account not found")
    return owner


async def get_agent_from_key(
    x_api_key: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    if not x_api_key:
        raise _auth_error(401, "missing_api_key", "X-Api-Key header is required")
    key_hash = hash_api_key(x_api_key)
    result = await db.execute(select(Agent).where(Agent.api_key_hash == key_hash))
    agent = result.scalar_one_or_none()
    if not agent:
        raise _auth_error(401, "invalid_api_key", "Invalid API key")
    if agent.status == "frozen":
        raise _auth_error(403, "agent_frozen", "Agent is frozen")
    return agent
