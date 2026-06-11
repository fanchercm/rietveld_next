"""Human approval checkpoints for deterministic AI actions."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


_DECISIONS = {"pending", "approved", "rejected"}


@dataclass(frozen=True)
class ApprovalCheckpoint:
    """A human approval checkpoint for a proposed tool call."""

    checkpoint_id: str
    tool: str
    payload: Mapping[str, Any]
    rationale: str
    status: str = "pending"
    reviewer: str | None = None

    def __post_init__(self) -> None:
        if not self.checkpoint_id:
            raise ValueError("ApprovalCheckpoint.checkpoint_id must be non-empty")
        if not self.tool:
            raise ValueError("ApprovalCheckpoint.tool must be non-empty")
        if not self.rationale:
            raise ValueError("ApprovalCheckpoint.rationale must be non-empty")
        if self.status not in _DECISIONS:
            raise ValueError("ApprovalCheckpoint.status must be pending, approved, or rejected")
        if self.reviewer is not None and not self.reviewer:
            raise ValueError("ApprovalCheckpoint.reviewer must be non-empty when provided")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic checkpoint payload."""

        payload: dict[str, Any] = {
            "checkpoint_id": self.checkpoint_id,
            "tool": self.tool,
            "payload": dict(self.payload),
            "rationale": self.rationale,
            "status": self.status,
        }
        if self.reviewer is not None:
            payload["reviewer"] = self.reviewer
        return MappingProxyType(payload)


class ApprovalLedger:
    """In-memory deterministic approval ledger for agent checkpoints."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, ApprovalCheckpoint] = {}

    @property
    def checkpoints(self) -> tuple[ApprovalCheckpoint, ...]:
        """Return checkpoints sorted by ID."""

        return tuple(self._checkpoints[key] for key in sorted(self._checkpoints))

    def request(self, *, tool: str, payload: Mapping[str, Any], rationale: str) -> ApprovalCheckpoint:
        """Create a pending approval checkpoint."""

        checkpoint_id = f"approval-{len(self._checkpoints):04d}"
        checkpoint = ApprovalCheckpoint(
            checkpoint_id=checkpoint_id,
            tool=tool,
            payload=payload,
            rationale=rationale,
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def decide(self, checkpoint_id: str, *, approved: bool, reviewer: str) -> ApprovalCheckpoint:
        """Approve or reject an existing checkpoint."""

        if checkpoint_id not in self._checkpoints:
            raise ValueError(f"Unknown checkpoint_id `{checkpoint_id}`")
        status = "approved" if approved else "rejected"
        previous = self._checkpoints[checkpoint_id]
        if previous.status != "pending":
            raise ValueError(f"checkpoint `{checkpoint_id}` is already {previous.status}")
        checkpoint = ApprovalCheckpoint(
            checkpoint_id=checkpoint_id,
            tool=previous.tool,
            payload=previous.payload,
            rationale=previous.rationale,
            status=status,
            reviewer=reviewer,
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def is_approved(self, checkpoint_id: str) -> bool:
        """Return whether a checkpoint is approved."""

        if checkpoint_id not in self._checkpoints:
            raise ValueError(f"Unknown checkpoint_id `{checkpoint_id}`")
        return self._checkpoints[checkpoint_id].status == "approved"
