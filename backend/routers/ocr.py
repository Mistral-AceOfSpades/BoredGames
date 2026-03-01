"""OCR router — handles rulebook image uploads and text extraction."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.game import GameDB, GameResponse, GameSchema
from backend.services.ocr_service import process_rulebook_image, process_rulebook_pdf, process_rulebook_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ocr", tags=["ocr"])
MAX_RULEBOOK_BYTES = 20 * 1024 * 1024


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")


def _coerce_structured_rules(raw: Any) -> dict | None:
    if raw is None:
        return None
    try:
        return GameSchema.model_validate(raw).model_dump()
    except Exception:
        logger.warning("Ignoring invalid OCR structured_rules payload")
        return None


def _is_blocked_host(hostname: str) -> bool:
    host = hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"}:
        return True

    def _ip_is_blocked(ip_str: str) -> bool:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        )

    try:
        return _ip_is_blocked(host)
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return True
        for info in infos:
            ip_str = info[4][0]
            try:
                if _ip_is_blocked(ip_str):
                    return True
            except ValueError:
                continue
    return False


async def _validate_rulebook_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="URL must use http or https")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must include a valid host")
    if _is_blocked_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="URL host is not allowed")
    if parsed.port and parsed.port not in {80, 443}:
        raise HTTPException(status_code=400, detail="Only standard HTTP/HTTPS ports are allowed")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.head(url)
            if response.status_code in {405, 501}:
                response = await client.get(url, headers={"Range": "bytes=0-0"})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail="Unable to fetch URL") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Rulebook URL is not reachable")

    final_url = str(response.url)
    final_parsed = urlparse(final_url)
    if (
        final_parsed.scheme not in {"http", "https"}
        or not final_parsed.hostname
        or _is_blocked_host(final_parsed.hostname)
    ):
        raise HTTPException(status_code=400, detail="URL redirect target is not allowed")

    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type and not (content_type.startswith("image/") or content_type == "application/pdf"):
        raise HTTPException(status_code=400, detail="URL must point to an image or PDF")

    content_length = response.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            size = 0
        if size > MAX_RULEBOOK_BYTES:
            raise HTTPException(status_code=400, detail="Remote file too large (max 20MB)")

    return final_url


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

    file_data = await file.read()
    if len(file_data) > MAX_RULEBOOK_BYTES:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    if file.content_type == "application/pdf":
        result = await process_rulebook_pdf(file_data)
    else:
        result = await process_rulebook_image(file_data, file.content_type)

    structured = _coerce_structured_rules(result.get("structured_rules"))
    game_name = (structured or {}).get("name", file.filename or "Unknown Game")
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

    validated_url = await _validate_rulebook_url(url)
    result = await process_rulebook_url(validated_url)

    structured = _coerce_structured_rules(result.get("structured_rules"))
    game_name = (structured or {}).get("name", "Unknown Game")
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
