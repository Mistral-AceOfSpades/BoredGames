"""House rules router — validates and manages house rules."""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import GameDB, HouseRule, HouseRuleRequest
from backend.services.houserule_service import validate_house_rule

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/houserules", tags=["houserules"])


@router.post("/validate")
async def validate_rule(
    body: HouseRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a proposed house rule against the game's base rules."""
    result = await db.execute(select(GameDB).where(GameDB.id == body.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found or rules not loaded")

    validation = await validate_house_rule(game.structured_rules, body.description)

    return {
        "game_id": body.game_id,
        "house_rule": body.description,
        **validation,
    }


@router.post("/add")
async def add_house_rule(
    body: HouseRuleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate and add a house rule to a game."""
    result = await db.execute(select(GameDB).where(GameDB.id == body.game_id))
    game = result.scalar_one_or_none()
    if not game or not game.structured_rules:
        raise HTTPException(status_code=404, detail="Game not found or rules not loaded")

    # Validate first
    validation = await validate_house_rule(game.structured_rules, body.description)

    house_rule = HouseRule(
        id=str(uuid4()),
        description=body.description,
        impact=validation.get("balance_impact", "unknown"),
        validated=True,
        contradiction=validation.get("contradiction", False),
        contradiction_reason=validation.get("contradiction_reason"),
    )

    # Add to game's house rules
    current_rules = list(game.house_rules or [])
    current_rules.append(house_rule.model_dump())
    game.house_rules = current_rules
    await db.commit()

    return {
        "game_id": body.game_id,
        "house_rule": house_rule.model_dump(),
        "validation": validation,
    }


@router.get("/{game_id}")
async def list_house_rules(game_id: str, db: AsyncSession = Depends(get_db)):
    """List all house rules for a game."""
    result = await db.execute(select(GameDB).where(GameDB.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game_id": game_id, "house_rules": game.house_rules or []}


@router.delete("/{game_id}/{rule_id}")
async def delete_house_rule(
    game_id: str,
    rule_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a house rule from a game."""
    result = await db.execute(select(GameDB).where(GameDB.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    current_rules = list(game.house_rules or [])
    game.house_rules = [r for r in current_rules if r.get("id") != rule_id]
    await db.commit()

    return {"status": "deleted", "game_id": game_id, "rule_id": rule_id}
