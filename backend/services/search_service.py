"""Search service — finds game rules by name using Mistral + web search."""

from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.models.game import GameSchema
from backend.services.mistral_client import chat_completion

logger = logging.getLogger(__name__)
settings = get_settings()

GAME_SCHEMA_JSON = GameSchema.model_json_schema()

SEARCH_SYSTEM_PROMPT = """You are a board game rules expert with access to extensive knowledge of
board games. When given a board game name, provide comprehensive rules including:

1. Components list
2. Number of players (min/max)
3. Setup instructions
4. Turn structure with all phases
5. Victory conditions
6. Special rules and edge cases
7. A brief gameplay summary

Respond with a structured JSON object that conforms to this schema:
{schema}

Be thorough and accurate. If you're unsure about specific rules, note them in edge_cases.
Return ONLY valid JSON, no markdown fences.""".format(schema=json.dumps(GAME_SCHEMA_JSON, indent=2))


async def search_game_by_name(game_name: str) -> dict:
    """Search for game rules by name using Mistral Large + web search agent."""

    # Try with the large model (which supports web search as a built-in tool)
    messages = [
        {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Find and structure the complete official rules for the board game: "
                f'"{game_name}". Include all standard rules, setup, turn structure, '
                f"and victory conditions."
            ),
        },
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_large,
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=8192,
    )

    try:
        parsed = json.loads(result)
        schema = GameSchema(**parsed)
        return {
            "source": "search",
            "structured_rules": schema.model_dump(),
        }
    except Exception:
        logger.warning("Failed to parse game search result as schema")
        try:
            return {"source": "search", "structured_rules": json.loads(result)}
        except json.JSONDecodeError:
            return {"source": "search", "structured_rules": {"raw_output": result}}
