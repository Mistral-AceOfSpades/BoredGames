"""Explanation service — provides rule explanations in multiple modes."""

from __future__ import annotations

import json
import logging

from backend.config import get_settings
from backend.services.mistral_client import chat_completion

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_game_context(structured_rules: dict) -> str:
    """Build a context string from structured game rules."""
    return json.dumps(structured_rules, indent=2)


async def quick_start_explanation(structured_rules: dict) -> str:
    """3–5 minute quick start summary."""
    context = _build_game_context(structured_rules)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly board game teacher. Provide a quick-start explanation "
                "that a new player can understand in 3-5 minutes. Focus on:\n"
                "1. The goal of the game\n"
                "2. Basic turn flow\n"
                "3. How to win\n\n"
                "Keep it concise, conversational, and easy to follow. "
                "Use numbered steps and bullet points."
            ),
        },
        {
            "role": "user",
            "content": f"Please give me a quick-start explanation for this game:\n\n{context}",
        },
    ]
    return await chat_completion(messages=messages, model=settings.model_reasoning)


async def step_by_step_explanation(structured_rules: dict) -> str:
    """Detailed walkthrough with setup guidance."""
    context = _build_game_context(structured_rules)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a detailed board game instructor. Provide a comprehensive "
                "step-by-step walkthrough including:\n"
                "1. Complete component list and what each does\n"
                "2. Full setup instructions\n"
                "3. Detailed turn structure with all phases\n"
                "4. All victory conditions\n"
                "5. Special rules and edge cases\n\n"
                "Be thorough but organized. Use headers, numbered lists, and clear formatting."
            ),
        },
        {
            "role": "user",
            "content": f"Give me a detailed step-by-step explanation for this game:\n\n{context}",
        },
    ]
    return await chat_completion(messages=messages, model=settings.model_reasoning, max_tokens=8192)


async def playthrough_simulation(structured_rules: dict, num_players: int = 2) -> str:
    """Simulate a sample round to demonstrate gameplay."""
    context = _build_game_context(structured_rules)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an engaging board game narrator. Simulate one complete sample "
                f"round of the game with {num_players} fictional players. Show:\n"
                "1. Setup completion\n"
                "2. Each player's first turn in detail\n"
                "3. Key decision points and their consequences\n"
                "4. How scoring/progression works\n\n"
                "Make it feel like watching a real game. Use player names and describe "
                "actions vividly. Add brief rule explanations as they come up naturally."
            ),
        },
        {
            "role": "user",
            "content": f"Simulate a sample round for this game:\n\n{context}",
        },
    ]
    return await chat_completion(
        messages=messages,
        model=settings.model_reasoning,
        max_tokens=8192,
        temperature=0.6,
    )


async def answer_question(structured_rules: dict, question: str, history: list[dict] | None = None) -> dict:
    """Answer a specific question about the game rules (Q&A mode)."""
    context = _build_game_context(structured_rules)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a board game rules expert. Answer the player's question about "
                "the game based on the official rules provided. Be precise and cite "
                "specific rules when possible.\n\n"
                "If the question involves a house rule that conflicts with official rules, "
                "explicitly note the conflict.\n\n"
                "Format your response as JSON with these fields:\n"
                '- "answer": your detailed answer\n'
                '- "citations": list of relevant rule references\n'
                '- "confidence": "high", "medium", or "low"\n'
                '- "conflicts": list of any rule conflicts detected (empty if none)\n\n'
                f"Game Rules:\n{context}"
            ),
        },
    ]

    # Add conversation history if present
    if history:
        for msg in history[-10:]:  # Keep last 10 messages
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    result = await chat_completion(
        messages=messages,
        model=settings.model_qa_ft,  # fine-tuned Q&A model; falls back to large
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"answer": result, "citations": [], "confidence": "medium", "conflicts": []}
