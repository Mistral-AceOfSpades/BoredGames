"""OCR router — handles rulebook image uploads and text extraction."""

from __future__ import annotations

import logging
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import GameDB, GameResponse
from backend.services.ocr_service import process_rulebook_image, process_rulebook_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["ocr"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")


@router.post("/upload")
async def upload_rulebook(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a rulebook image/PDF and extract + structure the rules."""
    if not file.content_type or not (
        file.content_type.startswith("image/") or file.content_type == "application/pdf"
    ):
        raise HTTPException(status_code=400, detail="File must be an image or PDF")

    image_data = await file.read()
    if len(image_data) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    result = await process_rulebook_image(image_data, file.content_type)

    structured = result.get("structured_rules", {})
    game_name = structured.get("name", file.filename or "Unknown Game")
    slug = _slugify(game_name)

    # Save to database
    game = GameDB(
        id=str(uuid4()),
        name=game_name,
        slug=slug,
        source="ocr",
        raw_rules=result.get("raw_text", ""),
        structured_rules=structured,
        house_rules=[],
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    return GameResponse(
        id=game.id,
        name=game.name,
        slug=game.slug,
        source="ocr",
        structured_rules=structured,
        house_rules=[],
        created_at=game.created_at,
    )


@router.post("/url")
async def process_url(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Process a rulebook from a URL."""
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    result = await process_rulebook_url(url)

    structured = result.get("structured_rules", {})
    game_name = structured.get("name", "Unknown Game")
    slug = _slugify(game_name)

    game = GameDB(
        id=str(uuid4()),
        name=game_name,
        slug=slug,
        source="ocr",
        raw_rules=result.get("raw_text", ""),
        structured_rules=structured,
        house_rules=[],
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    return GameResponse(
        id=game.id,
        name=game.name,
        slug=game.slug,
        source="ocr",
        structured_rules=structured,
        house_rules=[],
        created_at=game.created_at,
    )
