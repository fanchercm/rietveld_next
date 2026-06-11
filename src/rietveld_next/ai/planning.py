"""Autonomous recipe planner v0 for deterministic AI workflows."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.ai.strategy import default_strategy_engine


@dataclass(frozen=True)
class RecipeStep:
    """A deterministic recipe step proposed by the planner."""

    step_id: str
    tool: str
    payload: Mapping[str, Any]
    rationale: str
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.step_id:
            raise ValueError("RecipeStep.step_id must be non-empty")
        if not self.tool:
            raise ValueError("RecipeStep.tool must be non-empty")
        if not self.rationale:
            raise ValueError("RecipeStep.rationale must be non-empty")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        return MappingProxyType(
            {
                "step_id": self.step_id,
                "tool": self.tool,
                "payload": dict(self.payload),
                "rationale": self.rationale,
                "requires_approval": self.requires_approval,
            }
        )


@dataclass(frozen=True)
class AutonomousRecipePlan:
    """A deterministic autonomous recipe plan."""

    goal: str
    steps: tuple[RecipeStep, ...]
    blocked_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.goal:
            raise ValueError("AutonomousRecipePlan.goal must be non-empty")
        for reason in self.blocked_reasons:
            if not reason:
                raise ValueError("AutonomousRecipePlan.blocked_reasons entries must be non-empty")

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        return MappingProxyType(
            {
                "goal": self.goal,
                "steps": tuple(step.to_payload() for step in self.steps),
                "blocked_reasons": self.blocked_reasons,
            }
        )


def plan_autonomous_recipe(
    *,
    goal: str,
    context: Mapping[str, Any],
    allowed_tools: Sequence[str],
) -> AutonomousRecipePlan:
    """Plan a deterministic autonomous recipe from rule-engine output.

    Args:
        goal: User-visible planning goal.
        context: Deterministic context payload.
        allowed_tools: Tool allow-list for this planning run.

    Returns:
        An autonomous plan with blocked reasons for disallowed actions.

    Raises:
        ValueError: If goal or allowed tool names are empty.
        TypeError: If context is not a mapping.
    """

    if not goal:
        raise ValueError("goal must be non-empty")
    if not isinstance(context, Mapping):
        raise TypeError("context must be a mapping")
    allowed = frozenset(_validate_tool_names(allowed_tools))
    recommendations = default_strategy_engine().recommend(context)
    steps: list[RecipeStep] = []
    blocked: list[str] = []
    for recommendation in recommendations:
        tool = str(recommendation["tool"])
        if tool not in allowed:
            blocked.append(f"Tool `{tool}` is not allowed for this recipe.")
            continue
        steps.append(
            RecipeStep(
                step_id=f"step-{len(steps):03d}",
                tool=tool,
                payload=recommendation["payload"],
                rationale=str(recommendation["rationale"]),
                requires_approval=bool(recommendation["requires_approval"]),
            )
        )
    return AutonomousRecipePlan(goal=goal, steps=tuple(steps), blocked_reasons=tuple(blocked))


def _validate_tool_names(tool_names: Sequence[str]) -> tuple[str, ...]:
    names: list[str] = []
    for name in tool_names:
        if not isinstance(name, str) or not name:
            raise ValueError("allowed_tools entries must be non-empty strings")
        names.append(name)
    return tuple(names)
