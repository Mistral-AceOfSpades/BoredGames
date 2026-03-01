"""Moderation service — game session moderation, turn management, dispute resolution."""

from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.services.mistral_client import chat_completion, moderate_text

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------- Turn Management ----------


async def validate_move(
    structured_rules: dict,
    game_state: dict,
    player: str,
    action: str,
) -> dict:
    """Check if a player's move is valid according to the rules and current state."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a board game moderator. Validate whether the proposed move "
                "is legal according to the game rules and current state.\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "valid": true/false,\n'
                '  "reason": "explanation",\n'
                '  "rule_reference": "which rule applies",\n'
                '  "suggestion": "what the player should do instead" or null\n'
                "}\n\n"
                f"Game Rules:\n{json.dumps(structured_rules, indent=2)}\n\n"
                f"Current Game State:\n{json.dumps(game_state, indent=2)}"
            ),
        },
        {
            "role": "user",
            "content": f'Player "{player}" wants to: {action}',
        },
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_large,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.warning("validate_move: received malformed JSON from chat_completion: %r", result)
        return {
            "valid": False,
            "reason": "Could not validate move (malformed validator response)",
            "rule_reference": "",
            "suggestion": None,
        }


async def resolve_dispute(
    structured_rules: dict,
    house_rules: list[dict],
    dispute_description: str,
) -> dict:
    """Resolve a rule dispute with citations and interpretation hierarchy."""
    # First, check content safety
    safety = await moderate_text(dispute_description)
    if safety.get("flagged"):
        return {
            "resolution": "Your dispute description was flagged for inappropriate content. Please rephrase.",
            "flagged": True,
        }

    hr_text = json.dumps(house_rules, indent=2) if house_rules else "None"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a neutral board game arbiter. Resolve the dispute using this "
                "interpretation hierarchy (highest to lowest priority):\n"
                "1. Official rule (from the rulebook)\n"
                "2. FAQ clarifications\n"
                "3. Community consensus\n"
                "4. House rule override\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "resolution": "your ruling",\n'
                '  "citations": ["specific rule references"],\n'
                '  "interpretation_level": "official|faq|community|house_rule",\n'
                '  "confidence": "high|medium|low",\n'
                '  "alternative_interpretations": ["other valid readings"]\n'
                "}\n\n"
                f"Official Rules:\n{json.dumps(structured_rules, indent=2)}\n\n"
                f"Active House Rules:\n{hr_text}"
            ),
        },
        {"role": "user", "content": f"Dispute: {dispute_description}"},
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_large,
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    try:
        parsed = json.loads(result)
        parsed["flagged"] = False
        return parsed
    except json.JSONDecodeError:
        return {
            "resolution": result,
            "citations": [],
            "interpretation_level": "unknown",
            "confidence": "medium",
            "flagged": False,
        }


async def get_turn_guidance(
    structured_rules: dict,
    game_state: dict,
    current_player: str,
) -> str:
    """Provide guidance for the current player's turn."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful board game moderator. Briefly tell the current player "
                "what they can do on their turn based on the rules and game state. "
                "Be concise and helpful.\n\n"
                f"Game Rules:\n{json.dumps(structured_rules, indent=2)}\n\n"
                f"Game State:\n{json.dumps(game_state, indent=2)}"
            ),
        },
        {
            "role": "user",
            "content": f'It\'s {current_player}\'s turn. What are their options?',
        },
    ]

    return await chat_completion(
        messages=messages,
        model=settings.model_large,
        temperature=0.3,
    )


async def check_win_condition(
    structured_rules: dict,
    game_state: dict,
) -> dict:
    """Check if any player has met the victory conditions."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a board game victory condition checker. Analyse the current "
                "game state against the victory conditions.\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "game_over": true/false,\n'
                '  "winner": "player name" or null,\n'
                '  "condition_met": "which victory condition" or null,\n'
                '  "near_victory": [{"player": "name", "condition": "description", "progress": "X%"}]\n'
                "}\n\n"
                f"Victory Conditions:\n{json.dumps(structured_rules.get('victory_conditions', []), indent=2)}\n\n"
                f"Game State:\n{json.dumps(game_state, indent=2)}"
            ),
        },
        {"role": "user", "content": "Check if anyone has won or is close to winning."},
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_large,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"game_over": False, "winner": None, "condition_met": None, "near_victory": []}
