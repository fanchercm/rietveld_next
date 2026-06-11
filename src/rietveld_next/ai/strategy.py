"""Deterministic strategy rule engine for AI refinement agents."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence


RulePredicate = Callable[[Mapping[str, Any]], bool]
RuleAction = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class StrategyRecommendation:
    """A deterministic recommendation emitted by the strategy engine."""

    rule_id: str
    tool: str
    payload: Mapping[str, Any]
    rationale: str
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("StrategyRecommendation.rule_id must be non-empty")
        if not self.tool:
            raise ValueError("StrategyRecommendation.tool must be non-empty")
        if not self.rationale:
            raise ValueError("StrategyRecommendation.rationale must be non-empty")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        return MappingProxyType(
            {
                "rule_id": self.rule_id,
                "tool": self.tool,
                "payload": dict(self.payload),
                "rationale": self.rationale,
                "requires_approval": self.requires_approval,
            }
        )


@dataclass(frozen=True)
class StrategyRule:
    """A deterministic strategy rule."""

    rule_id: str
    description: str
    predicate: RulePredicate
    action: RuleAction

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("StrategyRule.rule_id must be non-empty")
        if not self.description:
            raise ValueError("StrategyRule.description must be non-empty")
        if not callable(self.predicate):
            raise TypeError("StrategyRule.predicate must be callable")
        if not callable(self.action):
            raise TypeError("StrategyRule.action must be callable")


class StrategyRuleEngine:
    """Evaluate strategy rules in stable order."""

    def __init__(self, rules: Sequence[StrategyRule]) -> None:
        self._rules = tuple(rules)
        rule_ids = [rule.rule_id for rule in self._rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("StrategyRuleEngine rules must have unique rule_id values")

    @property
    def rules(self) -> tuple[StrategyRule, ...]:
        """Return immutable strategy rules."""

        return self._rules

    def recommend(self, context: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
        """Return deterministic recommendations for the context."""

        if not isinstance(context, Mapping):
            raise TypeError("context must be a mapping")
        recommendations: list[Mapping[str, Any]] = []
        for rule in sorted(self._rules, key=lambda item: item.rule_id):
            if rule.predicate(context):
                output = rule.action(context)
                recommendations.append(
                    StrategyRecommendation(
                        rule_id=rule.rule_id,
                        tool=str(output["tool"]),
                        payload=dict(output.get("payload", {})),
                        rationale=str(output["rationale"]),
                        requires_approval=bool(output.get("requires_approval", False)),
                    ).to_payload()
                )
        return tuple(recommendations)


def default_strategy_engine() -> StrategyRuleEngine:
    """Create the v0 deterministic strategy rule engine."""

    return StrategyRuleEngine(
        (
            StrategyRule(
                rule_id="S001",
                description="Run residual diagnostics when residuals are available.",
                predicate=lambda context: "residuals" in context,
                action=lambda context: {
                    "tool": "diagnose_residuals",
                    "payload": {"residuals": context["residuals"]},
                    "rationale": "Residuals are available and should be diagnosed before proposing refinement changes.",
                },
            ),
            StrategyRule(
                rule_id="S002",
                description="Freeze parameters flagged as nonphysical.",
                predicate=lambda context: bool(context.get("nonphysical_parameters")),
                action=lambda context: {
                    "tool": "freeze_parameter",
                    "payload": {
                        "parameter": sorted(context["nonphysical_parameters"])[0],
                        "model_state": context.get("model_state", {}),
                        "provenance": {"source": "strategy_rule", "rule_id": "S002"},
                    },
                    "rationale": "A nonphysical parameter should be frozen pending human review.",
                    "requires_approval": True,
                },
            ),
            StrategyRule(
                rule_id="S003",
                description="Compare candidate models when multiple candidates are present.",
                predicate=lambda context: len(context.get("candidate_models", ())) > 1,
                action=lambda context: {
                    "tool": "compare_models",
                    "payload": {"models": context["candidate_models"]},
                    "rationale": "Multiple candidate models require deterministic metric comparison.",
                },
            ),
            StrategyRule(
                rule_id="S004",
                description="Request rollback when validation metrics indicate overfitting.",
                predicate=lambda context: bool(context.get("overfitting_findings")) and bool(context.get("snapshots")),
                action=lambda context: {
                    "tool": "rollback",
                    "payload": {
                        "snapshots": context["snapshots"],
                        "snapshot_id": context["snapshots"][0]["snapshot_id"],
                        "provenance": {"source": "strategy_rule", "rule_id": "S004"},
                    },
                    "rationale": "Overfitting findings suggest returning to the previous stable snapshot.",
                    "requires_approval": True,
                },
            ),
        )
    )
