from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class GameObservation:
    """Structured snapshot of the current game state."""

    phase: str
    money: int
    hands_left: int
    discards_left: int
    score_to_beat: int
    current_score: int = 0
    jokers: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class GameAction:
    """A high-level in-game action before it is translated into UI input."""

    kind: str
    target: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class ValidationResult:
    """Whether the proposed action should be allowed to execute."""

    accepted: bool
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class StepRecord:
    """Single loop iteration for logging and later evaluation."""

    observation: GameObservation
    action: GameAction
    validation: ValidationResult
