"""Agent action log and scientific copilot report payloads."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.ai.tools import ActionLogEntry


@dataclass(frozen=True)
class Citation:
    """Knowledge-base citation metadata for AI-generated reports."""

    citation_id: str
    source: str
    title: str
    locator: str | None = None

    def __post_init__(self) -> None:
        if not self.citation_id:
            raise ValueError("Citation.citation_id must be non-empty")
        if not self.source:
            raise ValueError("Citation.source must be non-empty")
        if not self.title:
            raise ValueError("Citation.title must be non-empty")
        if self.locator is not None and not self.locator:
            raise ValueError("Citation.locator must be non-empty when provided")

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic citation payload."""

        payload: dict[str, Any] = {
            "citation_id": self.citation_id,
            "source": self.source,
            "title": self.title,
        }
        if self.locator is not None:
            payload["locator"] = self.locator
        return MappingProxyType(payload)


@dataclass(frozen=True)
class CopilotReport:
    """Deterministic scientific copilot report."""

    project_id: str
    summary: str
    diagnostics: tuple[Mapping[str, Any], ...]
    recommendations: tuple[Mapping[str, Any], ...]
    action_log: tuple[Mapping[str, Any], ...]
    citations: tuple[Mapping[str, Any], ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.project_id:
            raise ValueError("CopilotReport.project_id must be non-empty")
        if not self.summary:
            raise ValueError("CopilotReport.summary must be non-empty")
        for limitation in self.limitations:
            if not limitation:
                raise ValueError("CopilotReport.limitations entries must be non-empty")

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like report payload."""

        return MappingProxyType(
            {
                "project_id": self.project_id,
                "summary": self.summary,
                "diagnostics": self.diagnostics,
                "recommendations": self.recommendations,
                "action_log": self.action_log,
                "citations": self.citations,
                "limitations": self.limitations,
            }
        )


def action_log_viewer_payload(action_log: Sequence[ActionLogEntry]) -> Mapping[str, Any]:
    """Build a deterministic action log viewer payload.

    Args:
        action_log: Tool registry action log entries.

    Returns:
        JSON-like viewer payload sorted by sequence.
    """

    entries = tuple(entry.to_payload() for entry in sorted(action_log, key=lambda item: item.sequence))
    return MappingProxyType(
        {
            "entry_count": len(entries),
            "entries": entries,
            "failed_count": sum(1 for entry in entries if entry["status"] == "error"),
        }
    )


def generate_copilot_report(
    *,
    project_id: str,
    diagnostics: Sequence[Mapping[str, Any]],
    recommendations: Sequence[Mapping[str, Any]],
    action_log: Sequence[ActionLogEntry],
    citations: Sequence[Citation | Mapping[str, Any]] = (),
    limitations: Sequence[str] = (),
) -> CopilotReport:
    """Generate a deterministic scientific copilot report.

    Args:
        project_id: Stable project identifier.
        diagnostics: Deterministic diagnostic payloads.
        recommendations: Strategy recommendation payloads.
        action_log: Logged deterministic tool actions.
        citations: Knowledge-base citations supporting the report.
        limitations: Explicit report limitations.

    Returns:
        A report object with no LLM-generated claims.
    """

    if not project_id:
        raise ValueError("project_id must be non-empty")
    diagnostic_payloads = tuple(MappingProxyType(dict(item)) for item in diagnostics)
    recommendation_payloads = tuple(MappingProxyType(dict(item)) for item in recommendations)
    diagnostic_count = len(diagnostic_payloads)
    recommendation_count = len(recommendation_payloads)
    failed_count = sum(1 for entry in action_log if entry.status == "error")
    summary = (
        f"Project {project_id}: {diagnostic_count} deterministic diagnostics, "
        f"{recommendation_count} recommendations, {failed_count} failed tool calls."
    )
    citation_payloads = tuple(_citation_payload(citation) for citation in citations)
    report_limitations = tuple(limitations) or (
        "Report is generated from deterministic tool payloads only; no validation data were inferred.",
    )
    return CopilotReport(
        project_id=project_id,
        summary=summary,
        diagnostics=diagnostic_payloads,
        recommendations=recommendation_payloads,
        action_log=tuple(action_log_viewer_payload(action_log)["entries"]),
        citations=citation_payloads,
        limitations=report_limitations,
    )


def _citation_payload(citation: Citation | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(citation, Citation):
        return citation.to_payload()
    required = ("citation_id", "source", "title")
    missing = [field for field in required if field not in citation]
    if missing:
        raise ValueError(f"citation missing required fields: {', '.join(missing)}")
    return MappingProxyType(dict(citation))
