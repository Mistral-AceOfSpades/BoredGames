"""Games router — CRUD for game records and game search."""

from __future__ import annotations

import logging
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import (
    GameCreate,
    GameDB,
    GameResponse,
    GameSessionDB,
    SessionCreate,
)
from backend.services.search_service import search_game_by_name

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/games", tags=["games"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")


@router.post("", response_model=GameResponse)
async def create_game(body: GameCreate, db: AsyncSession = Depends(get_db)):
    """Search for a game by name, structure its rules, and save it."""
    slug = _slugify(body.name)

    # Check if already exists
    result = await db.execute(select(GameDB).where(GameDB.slug == slug))
    existing = result.scalar_one_or_none()
    if existing:
        return GameResponse(
            id=existing.id,
            name=existing.name,
            slug=existing.slug,
            source=existing.source or "search",
            structured_rules=existing.structured_rules,
            house_rules=existing.house_rules or [],
            created_at=existing.created_at,
        )

    # Search for the game rules
    search_result = await search_game_by_name(body.name)

    game = GameDB(
        id=str(uuid4()),
        name=body.name,
        slug=slug,
        source="search",
        structured_rules=search_result.get("structured_rules"),
        house_rules=[],
        metadata_={},
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    return GameResponse(
        id=game.id,
        name=game.name,
        slug=game.slug,
        source=game.source,
        structured_rules=game.structured_rules,
        house_rules=[],
        created_at=game.created_at,
    )


@router.get("", response_model=list[GameResponse])
async def list_games(db: AsyncSession = Depends(get_db)):
    """List all saved games."""
    result = await db.execute(select(GameDB).order_by(GameDB.created_at.desc()))
    games = result.scalars().all()
    return [
        GameResponse(
            id=g.id,
            name=g.name,
            slug=g.slug,
            source=g.source or "search",
            structured_rules=g.structured_rules,
            house_rules=g.house_rules or [],
            created_at=g.created_at,
        )
        for g in games
    ]


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single game by ID."""
    result = await db.execute(select(GameDB).where(GameDB.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameResponse(
        id=game.id,
        name=game.name,
        slug=game.slug,
        source=game.source or "search",
        structured_rules=game.structured_rules,
        house_rules=game.house_rules or [],
        created_at=game.created_at,
    )


@router.delete("/{game_id}")
async def delete_game(game_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a game."""
    result = await db.execute(select(GameDB).where(GameDB.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await db.delete(game)
    await db.commit()
    return {"status": "deleted"}


# ---------- Game Sessions ----------


@router.post("/{game_id}/sessions")
async def create_session(
    game_id: str,
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Start a new game session for moderation."""
    result = await db.execute(select(GameDB).where(GameDB.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    session = GameSessionDB(
        id=str(uuid4()),
        game_id=game_id,
        players=body.players,
        turn_order=body.players,
        current_turn=0,
        game_state={"scores": {p: 0 for p in body.players}, "round": 1},
        status="setup",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "id": session.id,
        "game_id": session.game_id,
        "players": session.players,
        "status": session.status,
        "current_turn": session.current_turn,
        "turn_order": session.turn_order,
        "game_state": session.game_state,
    }


@router.get("/{game_id}/sessions/{session_id}")
async def get_session(
    game_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a game session."""
    result = await db.execute(
        select(GameSessionDB).where(
            GameSessionDB.id == session_id,
            GameSessionDB.game_id == game_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "game_id": session.game_id,
        "players": session.players,
        "status": session.status,
        "current_turn": session.current_turn,
        "turn_order": session.turn_order,
        "game_state": session.game_state,
    }
