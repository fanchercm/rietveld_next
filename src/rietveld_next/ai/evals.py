"""Deterministic AI evaluation benchmark scaffolding without LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.ai.safety import detect_prompt_injection, prompt_injection_regression_cases
from rietveld_next.ai.tools import ToolRegistry


@dataclass(frozen=True)
class EvaluationTask:
    """A deterministic tool-evaluation task."""

    task_id: str
    tool: str
    payload: Mapping[str, Any]
    expected_status: str = "ok"
    expected_output_subset: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("EvaluationTask.task_id must be non-empty")
        if not self.tool:
            raise ValueError("EvaluationTask.tool must be non-empty")
        if self.expected_status not in {"ok", "error"}:
            raise ValueError("EvaluationTask.expected_status must be ok or error")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        if self.expected_output_subset is not None:
            object.__setattr__(self, "expected_output_subset", MappingProxyType(dict(self.expected_output_subset)))


@dataclass(frozen=True)
class EvaluationResult:
    """Result from a deterministic evaluation task."""

    task_id: str
    passed: bool
    observed_status: str
    error: str | None = None

    def to_payload(self) -> Mapping[str, Any]:
        """Return a deterministic JSON-like payload."""

        payload: dict[str, Any] = {
            "task_id": self.task_id,
            "passed": self.passed,
            "observed_status": self.observed_status,
        }
        if self.error is not None:
            payload["error"] = self.error
        return MappingProxyType(payload)


class EvaluationSuite:
    """Run deterministic AI tool evaluations without LLM or network calls."""

    def __init__(self, tasks: Sequence[EvaluationTask]) -> None:
        self._tasks = tuple(tasks)
        task_ids = [task.task_id for task in self._tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("EvaluationSuite task_id values must be unique")

    @property
    def tasks(self) -> tuple[EvaluationTask, ...]:
        """Return immutable evaluation tasks."""

        return self._tasks

    def run(self, registry: ToolRegistry) -> Mapping[str, Any]:
        """Run all tasks against a deterministic tool registry."""

        results = tuple(_run_task(registry, task).to_payload() for task in self._tasks)
        return MappingProxyType(
            {
                "task_count": len(results),
                "passed_count": sum(1 for result in results if result["passed"]),
                "results": results,
            }
        )


def default_ai_evaluation_suite() -> EvaluationSuite:
    """Create a lightweight deterministic AI evaluation suite."""

    return EvaluationSuite(
        (
            EvaluationTask(
                task_id="diagnose-residuals-basic",
                tool="diagnose_residuals",
                payload={"residuals": [0.0, 1.0, -1.0, 0.5]},
                expected_status="ok",
                expected_output_subset={"count": 4},
            ),
            EvaluationTask(
                task_id="compare-models-basic",
                tool="compare_models",
                payload={
                    "models": (
                        {"model_id": "b", "metrics": {"rwp": 12.0, "aic": 4.0}},
                        {"model_id": "a", "metrics": {"rwp": 10.0, "aic": 6.0}},
                    )
                },
                expected_status="ok",
                expected_output_subset={"best_model_id": "a"},
            ),
        )
    )


def run_prompt_injection_regression_suite() -> Mapping[str, Any]:
    """Run prompt-injection regression fixtures through deterministic checks."""

    results: list[Mapping[str, Any]] = []
    for case in prompt_injection_regression_cases():
        findings = detect_prompt_injection(case["payload"])
        blocked = bool(findings)
        results.append(
            MappingProxyType(
                {
                    "case_id": case["case_id"],
                    "passed": blocked == bool(case["expected_blocked"]),
                    "blocked": blocked,
                    "finding_count": len(findings),
                }
            )
        )
    return MappingProxyType(
        {
            "case_count": len(results),
            "passed_count": sum(1 for result in results if result["passed"]),
            "results": tuple(results),
        }
    )


def _run_task(registry: ToolRegistry, task: EvaluationTask) -> EvaluationResult:
    result = registry.call_tool(task.tool, task.payload)
    passed = result.status == task.expected_status
    error = result.error
    if passed and task.expected_output_subset is not None:
        observed = result.output or {}
        for key, expected in task.expected_output_subset.items():
            if observed.get(key) != expected:
                passed = False
                error = f"Expected output `{key}`={expected!r}, got {observed.get(key)!r}"
                break
    return EvaluationResult(task_id=task.task_id, passed=passed, observed_status=result.status, error=error)
