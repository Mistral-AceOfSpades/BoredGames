"""Authentication router — GitHub OAuth + JWT."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.models.user import TokenResponse, UserDB, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


def create_jwt(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserDB | None:
    """Optional auth dependency — returns None for unauthenticated requests."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(UserDB).where(UserDB.id == user_id))
        return result.scalar_one_or_none()
    except JWTError:
        return None


async def require_user(
    user: UserDB | None = Depends(get_current_user),
) -> UserDB:
    """Strict auth dependency — raises 401 if not authenticated."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


@router.get("/github")
async def github_login():
    """Return the GitHub OAuth URL for the frontend to redirect to."""
    if not settings.github_client_id:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=read:user"
    )
    return {"url": url}


@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange GitHub OAuth code for a JWT."""
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    # Fetch user info
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()

    github_id = str(user_data["id"])
    username = user_data.get("login", "unknown")
    avatar_url = user_data.get("avatar_url")

    # Upsert user
    result = await db.execute(select(UserDB).where(UserDB.github_id == github_id))
    user = result.scalar_one_or_none()
    if user:
        user.username = username
        user.avatar_url = avatar_url
        user.access_token = access_token
    else:
        user = UserDB(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
            access_token=access_token,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    jwt_token = create_jwt(user.id)
    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse(id=user.id, username=user.username, avatar_url=user.avatar_url),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserDB = Depends(require_user)):
    return UserResponse(id=user.id, username=user.username, avatar_url=user.avatar_url)


@router.post("/dev-token", response_model=TokenResponse)
async def dev_token(db: AsyncSession = Depends(get_db)):
    """Development-only endpoint — creates a test user and returns a JWT."""
    if not settings.debug:
        raise HTTPException(status_code=404)

    result = await db.execute(select(UserDB).where(UserDB.github_id == "dev-user"))
    user = result.scalar_one_or_none()
    if not user:
        user = UserDB(github_id="dev-user", username="Developer", avatar_url=None)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    jwt_token = create_jwt(user.id)
    return TokenResponse(
        access_token=jwt_token,
        user=UserResponse(id=user.id, username=user.username, avatar_url=user.avatar_url),
    )
