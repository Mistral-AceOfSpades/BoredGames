"""Central Mistral AI client — wraps the mistralai SDK for all model calls."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from mistralai import Mistral

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache()
def get_mistral_client() -> Mistral:
    """Singleton Mistral SDK client."""
    return Mistral(api_key=settings.mistral_api_key)


# ---------- Helpers ----------


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    response_format: dict | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Generic chat completion call.  Falls back to model_large when a
    fine-tuned model is unavailable (404)."""
    client = get_mistral_client()
    model = model or settings.model_large
    kwargs: dict[str, Any] = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if response_format:
        kwargs["response_format"] = response_format

    try:
        resp = await client.chat.complete_async(**kwargs)
        return resp.choices[0].message.content
    except Exception as exc:
        # If a fine-tuned model 404s, fall back to the large model.
        if "404" in str(exc) and model != settings.model_large:
            logger.warning("Model %s unavailable, falling back to %s", model, settings.model_large)
            kwargs["model"] = settings.model_large
            resp = await client.chat.complete_async(**kwargs)
            return resp.choices[0].message.content
        raise


async def embed_text(texts: list[str]) -> list[list[float]]:
    """Generate embeddings via mistral-embed."""
    client = get_mistral_client()
    resp = await client.embeddings.create_async(
        model=settings.model_embed,
        inputs=texts,
    )
    return [d.embedding for d in resp.data]


async def moderate_text(text: str) -> dict:
    """Run content through Mistral Moderation."""
    client = get_mistral_client()
    resp = await client.classifiers.moderate_chat_async(
        model=settings.model_moderation,
        inputs=[{"role": "user", "content": text}],
    )
    result = resp.results[0] if resp.results else None
    if result:
        flagged = any(
            getattr(result.categories, cat, False)
            for cat in [
                "sexual",
                "hate_and_discrimination",
                "violence_and_threats",
                "dangerous_and_criminal_content",
                "selfharm",
            ]
        )
        return {"flagged": flagged, "categories": result.categories.__dict__ if result.categories else {}}
    return {"flagged": False, "categories": {}}


async def ocr_extract(image_url: str | None = None, document_url: str | None = None) -> str:
    """Extract text from an image or PDF using mistral-ocr-2512."""
    client = get_mistral_client()
    if document_url:
        resp = await client.ocr.process_async(
            model=settings.model_ocr,
            document={"type": "document_url", "document_url": document_url},
        )
    elif image_url:
        resp = await client.ocr.process_async(
            model=settings.model_ocr,
            document={"type": "image_url", "image_url": image_url},
        )
    else:
        raise ValueError("Either image_url or document_url must be provided")

    # Combine all page texts
    pages_text = []
    for page in resp.pages:
        pages_text.append(page.markdown)
    return "\n\n---\n\n".join(pages_text)


async def transcribe_audio(audio_data: bytes, mime_type: str = "audio/webm") -> str:
    """Transcribe audio using voxtral-mini-transcribe."""
    client = get_mistral_client()
    import tempfile
    import os

    # Write to temp file for SDK upload
    suffix = ".webm" if "webm" in mime_type else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            resp = await client.audio.transcriptions.create_async(
                model=settings.model_voice,
                file={"file_name": f"audio{suffix}", "content": f.read()},
            )
        return resp.text
    finally:
        os.unlink(tmp_path)
