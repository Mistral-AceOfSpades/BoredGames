"""Voice router — handles audio transcription."""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile

from backend.services.mistral_client import transcribe_audio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio file to text using Voxtral."""
    audio_data = await file.read()
    if len(audio_data) > 25 * 1024 * 1024:  # 25 MB limit
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Audio file too large (max 25MB)")

    mime_type = file.content_type or "audio/webm"
    text = await transcribe_audio(audio_data, mime_type)

    return {"text": text, "mime_type": mime_type}
