"""Search service — finds game rules by name using Mistral + web search."""

from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.models.game import GameSchema
from backend.services.mistral_client import chat_completion

logger = logging.getLogger(__name__)
settings = get_settings()


class GameSearchError(Exception):
    """Raised when game search fails in a known, user-facing way."""

    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _fallback_schema(game_name: str, raw_output: str | None = None) -> dict:
    summary = "Rules were retrieved but could not be fully structured automatically."
    if raw_output:
        snippet = " ".join(raw_output.split())[:220]
        if snippet:
            summary = f"{summary} Raw excerpt: {snippet}"
    return GameSchema(name=game_name, summary=summary).model_dump()

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

    if not settings.mistral_api_key:
        raise GameSearchError(
            "Game search is not configured. Set MISTRAL_API_KEY in backend .env.",
            status_code=503,
        )

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

    try:
        result = await chat_completion(
            messages=messages,
            model=settings.model_large,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=8192,
        )
    except Exception as exc:
        error_text = str(exc).lower()
        if "401" in error_text or "unauthorized" in error_text:
            raise GameSearchError(
                "Mistral authentication failed. Please verify MISTRAL_API_KEY.",
                status_code=503,
            ) from exc
        if "429" in error_text or "rate" in error_text:
            raise GameSearchError(
                "Game search is rate-limited right now. Please try again shortly.",
                status_code=503,
            ) from exc
        raise GameSearchError(
            "Game search provider is temporarily unavailable. Please try again.",
            status_code=502,
        ) from exc

    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and not parsed.get("name"):
            parsed["name"] = game_name
        schema = GameSchema.model_validate(parsed)
        return {
            "source": "search",
            "structured_rules": schema.model_dump(),
        }
    except Exception:
        logger.warning("Failed to parse game search result as schema")
        return {
            "source": "search",
            "structured_rules": _fallback_schema(game_name, result),
        }
