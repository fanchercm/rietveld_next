"""Append-only JSONL provenance log helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProvenanceLogEvent:
    """Single deterministic provenance event.

    Args:
        event_id: Stable event identifier.
        action: Action name recorded by the caller.
        timestamp: Caller-supplied timestamp string.
        payload: JSON-compatible event details.
    """

    event_id: str
    action: str
    timestamp: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate required event fields."""

        for name, value in (("event_id", self.event_id), ("action", self.action), ("timestamp", self.timestamp)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a JSON object.")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible event mapping."""

        return {
            "action": self.action,
            "event_id": self.event_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


def append_provenance_event(log_path: Path, event: ProvenanceLogEvent) -> None:
    """Append one event to a JSONL provenance log.

    Args:
        log_path: JSONL file path to append.
        event: Event to serialize.

    Raises:
        ValueError: If the log path points to a directory.
    """

    path = Path(log_path)
    if path.exists() and path.is_dir():
        raise ValueError(f"Provenance log path must be a file, got directory: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_provenance_events(log_path: Path) -> tuple[ProvenanceLogEvent, ...]:
    """Read provenance events from a JSONL log in file order.

    Args:
        log_path: JSONL file path.

    Returns:
        Tuple of parsed events.

    Raises:
        ValueError: If a line is malformed or missing required fields.
    """

    path = Path(log_path)
    if not path.exists():
        return ()
    events: list[ProvenanceLogEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            decoded = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid provenance JSONL at line {line_number}: {exc.msg}") from exc
        if not isinstance(decoded, dict):
            raise ValueError(f"Invalid provenance JSONL at line {line_number}: event must be an object.")
        try:
            events.append(
                ProvenanceLogEvent(
                    event_id=decoded["event_id"],
                    action=decoded["action"],
                    timestamp=decoded["timestamp"],
                    payload=decoded.get("payload", {}),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Invalid provenance JSONL at line {line_number}: missing {exc.args[0]}.") from exc
    return tuple(events)
