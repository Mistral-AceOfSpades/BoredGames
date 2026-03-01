"""Explain router — game rule explanation endpoint in multiple modes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import ExplanationMode, ExplanationRequest, GameDB, QARequest
from backend.services.explain_service import (
    answer_question,
    playthrough_simulation,
    quick_start_explanation,
    step_by_step_explanation,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/explain", tags=["explain"])


@router.post("")
async def explain_game(
    body: ExplanationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Get an explanation of the game rules in the requested mode."""
    result = await db.execute(select(GameDB).where(GameDB.id == body.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found or rules not loaded")

    rules = game.structured_rules

    match body.mode:
        case ExplanationMode.quick_start:
            explanation = await quick_start_explanation(rules)
        case ExplanationMode.step_by_step:
            explanation = await step_by_step_explanation(rules)
        case ExplanationMode.playthrough:
            num_players = rules.get("min_players", 2)
            explanation = await playthrough_simulation(rules, num_players)
        case ExplanationMode.qa:
            raise HTTPException(
                status_code=400,
                detail="Use /explain/qa endpoint for Q&A mode",
            )

    return {
        "game_id": body.game_id,
        "mode": body.mode.value,
        "explanation": explanation,
    }


@router.post("/qa")
async def qa_mode(
    body: QARequest,
    db: AsyncSession = Depends(get_db),
):
    """Ask a question about the game rules."""
    result = await db.execute(select(GameDB).where(GameDB.id == body.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found or rules not loaded")

    answer = await answer_question(game.structured_rules, body.question)

    return {
        "game_id": body.game_id,
        "question": body.question,
        **answer,
    }
