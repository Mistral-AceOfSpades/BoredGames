"""OCR service — extracts and structures rulebook content from uploaded images and PDFs."""

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


def _fallback_schema(name: str = "Unknown Game", raw_text: str | None = None) -> dict:
    summary = "Rulebook text was extracted but could not be fully structured automatically."
    if raw_text:
        snippet = " ".join(raw_text.split())[:220]
        if snippet:
            summary = f"{summary} OCR excerpt: {snippet}"
    return GameSchema(name=name, summary=summary).model_dump()


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


async def process_rulebook_pdf(pdf_data: bytes) -> dict[str, Any]:
    """Full pipeline: PDF bytes → OCR → structured game schema."""

    # Use a document data URL to route through document OCR ingestion.
    b64 = base64.b64encode(pdf_data).decode("utf-8")
    document_url = f"data:application/pdf;base64,{b64}"

    raw_text = await ocr_extract(document_url=document_url)
    logger.info("OCR extracted %d characters from PDF upload", len(raw_text))

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
    except json.JSONDecodeError:
        logger.warning("Failed to parse structured rules JSON")
        return _fallback_schema(raw_text=raw_text)

    if isinstance(parsed, dict) and not parsed.get("name"):
        parsed["name"] = "Unknown Game"

    try:
        schema = GameSchema.model_validate(parsed)
        return schema.model_dump()
    except Exception:
        logger.warning("Structured rules did not match schema, returning fallback schema")
        fallback_name = parsed.get("name", "Unknown Game") if isinstance(parsed, dict) else "Unknown Game"
        return _fallback_schema(name=fallback_name, raw_text=raw_text)
