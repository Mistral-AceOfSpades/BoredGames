"""Moderate router — game session moderation, turn management, dispute resolution."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import DisputeRequest, GameDB, GameSessionDB, TurnAction
from backend.services.moderation_service import (
    check_win_condition,
    get_turn_guidance,
    resolve_dispute,
    validate_move,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moderate", tags=["moderate"])


@router.post("/validate-move")
async def validate_player_move(
    body: TurnAction,
    db: AsyncSession = Depends(get_db),
):
    """Validate whether a player's move is legal."""
    result = await db.execute(select(GameSessionDB).where(GameSessionDB.id == body.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(select(GameDB).where(GameDB.id == session.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found")

    validation = await validate_move(
        game.structured_rules,
        session.game_state or {},
        body.player,
        body.action,
    )

    return {
        "session_id": body.session_id,
        "player": body.player,
        "action": body.action,
        **validation,
    }


@router.post("/advance-turn")
async def advance_turn(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Advance to the next player's turn."""
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    result = await db.execute(select(GameSessionDB).where(GameSessionDB.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Advance turn
    turn_order = session.turn_order or []
    if not turn_order:
        raise HTTPException(status_code=400, detail="No players in session")

    next_turn = (session.current_turn + 1) % len(turn_order)
    session.current_turn = next_turn
    session.status = "active"

    # Check if round increments
    game_state = dict(session.game_state or {})
    if next_turn == 0:
        game_state["round"] = game_state.get("round", 1) + 1
    session.game_state = game_state

    await db.commit()
    await db.refresh(session)

    current_player = turn_order[next_turn]

    # Get turn guidance
    result = await db.execute(select(GameDB).where(GameDB.id == session.game_id))
    game = result.scalar_one_or_none()
    guidance = ""
    if game and game.structured_rules:
        guidance = await get_turn_guidance(game.structured_rules, session.game_state, current_player)

    return {
        "session_id": session.id,
        "current_turn": session.current_turn,
        "current_player": current_player,
        "round": game_state.get("round", 1),
        "guidance": guidance,
    }


@router.post("/dispute")
async def dispute_resolution(
    body: DisputeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a rule dispute during gameplay."""
    result = await db.execute(select(GameDB).where(GameDB.id == body.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found")

    resolution = await resolve_dispute(
        game.structured_rules,
        game.house_rules or [],
        body.description,
    )

    return {
        "game_id": body.game_id,
        "session_id": body.session_id,
        "dispute": body.description,
        **resolution,
    }


@router.post("/check-win")
async def check_win(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Check if any player has met victory conditions."""
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    result = await db.execute(select(GameSessionDB).where(GameSessionDB.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(select(GameDB).where(GameDB.id == session.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found")

    win_check = await check_win_condition(game.structured_rules, session.game_state or {})

    if win_check.get("game_over"):
        session.status = "ended"
        await db.commit()

    return {
        "session_id": session_id,
        **win_check,
    }
