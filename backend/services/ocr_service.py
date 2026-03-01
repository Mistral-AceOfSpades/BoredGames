"""OCR service — extracts and structures rulebook content from uploaded images."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from backend.config import get_settings
from backend.models.game import GameSchema
from backend.services.mistral_client import chat_completion, ocr_extract

logger = logging.getLogger(__name__)
settings = get_settings()

GAME_SCHEMA_JSON = GameSchema.model_json_schema()

STRUCTURING_SYSTEM_PROMPT = """You are a board game rulebook expert. Given raw OCR text extracted
from a board game rulebook, produce a structured JSON game schema.

The JSON must conform to this schema:
{schema}

Rules:
- Extract ALL relevant information from the OCR text.
- If a field is not found, use reasonable defaults or empty arrays.
- Be precise with turn structures and victory conditions.
- Include edge cases and special rules you can find.
- Provide a concise summary of gameplay.

Return ONLY valid JSON, no markdown fences.""".format(schema=json.dumps(GAME_SCHEMA_JSON, indent=2))


async def process_rulebook_image(image_data: bytes, content_type: str = "image/png") -> dict[str, Any]:
    """Full pipeline: image → OCR → structured game schema."""

    # Step 1: Convert image to base64 data URL
    b64 = base64.b64encode(image_data).decode("utf-8")
    image_url = f"data:{content_type};base64,{b64}"

    # Step 2: OCR extraction
    raw_text = await ocr_extract(image_url=image_url)
    logger.info("OCR extracted %d characters", len(raw_text))

    # Step 3: Structure the rules
    structured = await structure_rules(raw_text)

    return {
        "raw_text": raw_text,
        "structured_rules": structured,
    }


async def process_rulebook_url(document_url: str) -> dict[str, Any]:
    """Process a rulebook from a URL (PDF or image)."""
    raw_text = await ocr_extract(document_url=document_url)
    logger.info("OCR extracted %d characters from URL", len(raw_text))
    structured = await structure_rules(raw_text)
    return {
        "raw_text": raw_text,
        "structured_rules": structured,
    }


async def structure_rules(raw_text: str) -> dict:
    """Use Mistral to normalise raw OCR text into the GameSchema JSON."""
    messages = [
        {"role": "system", "content": STRUCTURING_SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is the raw OCR text from a board game rulebook:\n\n{raw_text}"},
    ]

    result = await chat_completion(
        messages=messages,
        model=settings.model_schema_ft,  # fine-tuned; falls back to model_large
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    try:
        parsed = json.loads(result)
        # Validate against schema
        schema = GameSchema(**parsed)
        return schema.model_dump()
    except Exception:
        logger.warning("Failed to parse structured rules, returning raw JSON")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_output": result}
