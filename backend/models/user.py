"""User model for authentication."""

from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from backend.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    github_id = Column(String, unique=True, nullable=False)
    username = Column(String(128), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    access_token = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class UserResponse(BaseModel):
    id: str
    username: str
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
