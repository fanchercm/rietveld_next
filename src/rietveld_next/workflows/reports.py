"""Comparison reports and high-throughput workflow summaries."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from rietveld_next.workflows.sequential import SequentialResultTable


@dataclass(frozen=True)
class ParameterTolerance:
    """Absolute comparison tolerance for one parameter."""

    parameter: str
    absolute: float

    def __post_init__(self) -> None:
        """Validate tolerance fields."""

        if not isinstance(self.parameter, str) or not self.parameter:
            raise ValueError("ParameterTolerance.parameter must be non-empty")
        if isinstance(self.absolute, bool):
            raise ValueError("ParameterTolerance.absolute must be a non-negative finite number")
        absolute = float(self.absolute)
        if not math.isfinite(absolute) or absolute < 0.0:
            raise ValueError("ParameterTolerance.absolute must be a non-negative finite number")
        object.__setattr__(self, "absolute", absolute)


def compare_workflow_results(
    baseline: SequentialResultTable,
    candidate: SequentialResultTable,
    *,
    tolerances: Sequence[ParameterTolerance] = (),
) -> dict[str, Any]:
    """Compare two sequential result tables by point and parameter.

    Args:
        baseline: Reference result table.
        candidate: Candidate result table.
        tolerances: Optional absolute parameter tolerances.

    Returns:
        Machine-readable comparison report with per-parameter deltas.
    """

    tolerance_by_parameter = {item.parameter: float(item.absolute) for item in tolerances}
    candidate_by_point = {row.point_id: row for row in candidate.rows}
    rows: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for left in baseline.rows:
        right = candidate_by_point.get(left.point_id)
        if right is None:
            status = "missing_candidate"
            rows.append({"point_id": left.point_id, "status": status, "parameters": []})
            status_counts[status] = status_counts.get(status, 0) + 1
            continue
        parameters: list[dict[str, Any]] = []
        row_status = "ok"
        for name, estimate in left.parameters.items():
            candidate_estimate = right.parameters.get(name)
            if candidate_estimate is None:
                parameter_status = "missing_candidate_parameter"
                delta = None
            else:
                delta = candidate_estimate.value - estimate.value
                parameter_status = "ok" if abs(delta) <= tolerance_by_parameter.get(name, 0.0) else "different"
            if parameter_status != "ok":
                row_status = "different"
            parameters.append(
                {
                    "parameter": name,
                    "baseline": estimate.value,
                    "candidate": candidate_estimate.value if candidate_estimate is not None else None,
                    "delta": delta,
                    "tolerance": tolerance_by_parameter.get(name, 0.0),
                    "status": parameter_status,
                }
            )
        rows.append({"point_id": left.point_id, "status": row_status, "parameters": parameters})
        status_counts[row_status] = status_counts.get(row_status, 0) + 1
    return {
        "baseline_study_id": baseline.study_id,
        "candidate_study_id": candidate.study_id,
        "status_counts": dict(sorted(status_counts.items())),
        "rows": rows,
    }


def summarize_high_throughput_results(
    tables: Sequence[SequentialResultTable],
    *,
    objective_metric: str = "objective",
) -> Mapping[str, Any]:
    """Summarize many workflow result tables for high-throughput screening."""

    status_counts: dict[str, int] = {}
    study_rows: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for table in tables:
        study_status = "ok" if table.succeeded else "error"
        status_counts[study_status] = status_counts.get(study_status, 0) + 1
        metric_values = [
            row.metrics[objective_metric]
            for row in table.rows
            if row.status == "ok" and objective_metric in row.metrics
        ]
        best_metric = min(metric_values) if metric_values else None
        study_row = {
            "study_id": table.study_id,
            "status": study_status,
            "point_count": len(table.rows),
            "successful_points": sum(1 for row in table.rows if row.status == "ok"),
            "failed_points": sum(1 for row in table.rows if row.status == "error"),
            "best_metric": best_metric,
            "objective_metric": objective_metric,
        }
        study_rows.append(study_row)
        if best_metric is not None and (best is None or best_metric < best["best_metric"]):
            best = study_row
    return {
        "study_count": len(tables),
        "status_counts": dict(sorted(status_counts.items())),
        "objective_metric": objective_metric,
        "best_study": best,
        "studies": study_rows,
    }
