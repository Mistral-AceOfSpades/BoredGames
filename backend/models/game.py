"""Game-related Pydantic schemas and SQLAlchemy models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.sql import func

from backend.database import Base


# ---------- SQLAlchemy ORM ----------


class GameDB(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(256), nullable=False, index=True)
    slug = Column(String(256), unique=True, index=True)
    source = Column(String(32))  # "search" | "ocr"
    raw_rules = Column(Text)
    structured_rules = Column(JSON)
    house_rules = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GameSessionDB(Base):
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    game_id = Column(String, nullable=False, index=True)
    players = Column(JSON, default=list)
    current_turn = Column(Integer, default=0)
    turn_order = Column(JSON, default=list)
    game_state = Column(JSON, default=dict)
    status = Column(String(32), default="setup")  # setup | active | paused | ended
    conversation_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ---------- Pydantic Schemas ----------


class GameComponent(BaseModel):
    name: str
    quantity: int | None = None
    description: str = ""


class TurnPhase(BaseModel):
    name: str
    description: str
    actions: list[str] = []


class VictoryCondition(BaseModel):
    description: str
    type: str = "standard"  # standard | alternative | cooperative


class GameSchema(BaseModel):
    """Structured game schema — the normalised output from rule extraction."""

    name: str
    min_players: int = 2
    max_players: int = 4
    estimated_duration_minutes: int | None = None
    components: list[GameComponent] = []
    setup_instructions: list[str] = []
    turn_structure: list[TurnPhase] = []
    victory_conditions: list[VictoryCondition] = []
    special_rules: list[str] = []
    edge_cases: list[str] = []
    summary: str = ""


class HouseRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    modifies_rule: str | None = None
    impact: str | None = None
    validated: bool = False
    contradiction: bool = False
    contradiction_reason: str | None = None


class GameCreate(BaseModel):
    name: str


class GameResponse(BaseModel):
    id: str
    name: str
    slug: str
    source: str
    structured_rules: GameSchema | None = None
    house_rules: list[HouseRule] = []
    created_at: datetime


class ExplanationMode(str, Enum):
    quick_start = "quick_start"
    step_by_step = "step_by_step"
    playthrough = "playthrough"
    qa = "qa"


class ExplanationRequest(BaseModel):
    game_id: str
    mode: ExplanationMode = ExplanationMode.quick_start


class QARequest(BaseModel):
    game_id: str
    question: str


class HouseRuleRequest(BaseModel):
    game_id: str
    description: str


class DisputeRequest(BaseModel):
    game_id: str
    session_id: str
    description: str


class SessionCreate(BaseModel):
    game_id: str
    players: list[str]


class TurnAction(BaseModel):
    session_id: str
    player: str
    action: str
    details: str = ""


class ChatMessage(BaseModel):
    role: str  # user | assistant | system
    content: str
    citations: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
