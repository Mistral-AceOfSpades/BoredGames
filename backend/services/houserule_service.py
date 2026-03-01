"""House rule service — validates proposed house rules against base rules."""

from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.services.mistral_client import chat_completion

logger = logging.getLogger(__name__)
settings = get_settings()


async def validate_house_rule(structured_rules: dict, house_rule_description: str) -> dict:
    """Analyse a proposed house rule against the base game rules.

    Returns a structured analysis with contradiction detection, impact, and
    logical consistency checks.
    """
    context = json.dumps(structured_rules, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a board game design analyst. Evaluate the proposed house rule "
                "against the official base rules. Perform these analyses:\n\n"
                "1. **Contradiction check**: Does it contradict any existing rule?\n"
                "2. **Impact analysis**: How does it affect balance, game length, complexity?\n"
                "3. **Logical consistency**: Could it create infinite loops, unwinnable states, "
                "or broken economies?\n"
                "4. **Recommendation**: Accept, modify, or reject with reasoning.\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "contradiction": true/false,\n'
                '  "contradiction_reason": "..." or null,\n'
                '  "impacted_rules": ["rule section names"],\n'
                '  "balance_impact": "none|low|medium|high",\n'
                '  "length_impact": "shorter|unchanged|longer",\n'
                '  "complexity_impact": "simpler|unchanged|more_complex",\n'
                '  "logical_issues": ["any loops, unwinnable states, etc."],\n'
                '  "recommendation": "accept|modify|reject",\n'
                '  "recommendation_reason": "...",\n'
                '  "suggested_modification": "..." or null\n'
                "}\n\n"
                f"Base Game Rules:\n{context}"
            ),
        },
        {
            "role": "user",
            "content": f"Evaluate this proposed house rule:\n\n{house_rule_description}",
        },
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_houserules_ft,  # fine-tuned; falls back to large
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "contradiction": False,
            "raw_analysis": result,
            "recommendation": "review",
            "recommendation_reason": "Could not parse structured analysis",
        }


async def detect_live_rule_change(transcribed_text: str, current_rules: dict) -> dict | None:
    """Detect if transcribed speech contains a proposed rule change."""
    context = json.dumps(current_rules, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "You are listening to a board game session. Determine if the player's "
                "statement proposes a new house rule or rule change.\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "is_rule_change": true/false,\n'
                '  "proposed_rule": "description of the proposed rule" or null,\n'
                '  "affected_mechanic": "which part of the game it affects" or null\n'
                "}\n\n"
                f"Current Game Rules:\n{context}"
            ),
        },
        {"role": "user", "content": f"Player said: \"{transcribed_text}\""},
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_large,
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    try:
        parsed = json.loads(result)
        return parsed if parsed.get("is_rule_change") else None
    except json.JSONDecodeError:
        return None
