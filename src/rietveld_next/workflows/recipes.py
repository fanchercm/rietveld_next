"""Versioned batch recipe and checkpoint helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from rietveld_next.workflows.parametric import ParametricExpression, ParametricParameterModel
from rietveld_next.workflows.sequential import (
    PreviousPointInitialization,
    RetryPolicy,
    SequentialPointSpec,
    SequentialResultTable,
)


RECIPE_SCHEMA_VERSION = "workflow.batch_recipe.v1"
CHECKPOINT_SCHEMA_VERSION = "workflow.checkpoint.v1"


@dataclass(frozen=True)
class BatchRecipe:
    """Framework-free sequential/parametric batch recipe.

    Args:
        recipe_id: Stable recipe identifier.
        points: Ordered sequential points.
        initial_parameters: Starting parameters before workflow policies apply.
        retry_policy: Failed-point retry policy.
        initialization: Previous-point initialization policy.
        parametric_models: Optional expression models evaluated by callers.
        metadata: JSON-compatible audit metadata.
        schema_version: Versioned recipe format identifier.
    """

    recipe_id: str
    points: tuple[SequentialPointSpec, ...]
    initial_parameters: Mapping[str, float]
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    initialization: PreviousPointInitialization = field(default_factory=PreviousPointInitialization)
    parametric_models: tuple[ParametricParameterModel, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = RECIPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate recipe fields and freeze mappings."""

        _non_empty_string(self.recipe_id, "recipe_id")
        if self.schema_version != RECIPE_SCHEMA_VERSION:
            raise ValueError(f"Unsupported batch recipe schema_version '{self.schema_version}'")
        seen: set[str] = set()
        for point in self.points:
            if not isinstance(point, SequentialPointSpec):
                raise TypeError("points must contain SequentialPointSpec values")
            if point.point_id in seen:
                raise ValueError(f"Duplicate recipe point_id '{point.point_id}'")
            seen.add(point.point_id)
        for model in self.parametric_models:
            if not isinstance(model, ParametricParameterModel):
                raise TypeError("parametric_models must contain ParametricParameterModel values")
        initial_parameters = {
            str(name): _finite_float(value, f"initial_parameters.{name}")
            for name, value in self.initial_parameters.items()
        }
        object.__setattr__(self, "initial_parameters", MappingProxyType(dict(sorted(initial_parameters.items()))))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible recipe mapping."""

        return {
            "schema_version": self.schema_version,
            "recipe_id": self.recipe_id,
            "points": [point.to_dict() for point in self.points],
            "initial_parameters": dict(self.initial_parameters),
            "retry_policy": self.retry_policy.to_dict(),
            "initialization": self.initialization.to_dict(),
            "parametric_models": [model.to_dict() for model in self.parametric_models],
            "metadata": dict(sorted(self.metadata.items())),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BatchRecipe":
        """Create a recipe from a versioned mapping.

        Raises:
            ValueError: If the schema version is unsupported or required fields
                are missing.
        """

        if not isinstance(data, Mapping):
            raise TypeError("BatchRecipe.from_dict data must be a mapping")
        if data.get("schema_version") != RECIPE_SCHEMA_VERSION:
            raise ValueError(f"Unsupported batch recipe schema_version '{data.get('schema_version')}'")
        try:
            points = tuple(
                SequentialPointSpec(
                    point_id=str(point["point_id"]),
                    dataset_id=str(point["dataset_id"]),
                    variables=point.get("variables", {}),
                )
                for point in data["points"]
            )
            retry_data = data.get("retry_policy", {})
            initialization_data = data.get("initialization", {})
            models = tuple(_parametric_model_from_dict(model) for model in data.get("parametric_models", ()))
            return cls(
                recipe_id=str(data["recipe_id"]),
                points=points,
                initial_parameters=data["initial_parameters"],
                retry_policy=RetryPolicy(
                    max_attempts=int(retry_data.get("max_attempts", 1)),
                    retry_statuses=tuple(retry_data.get("retry_statuses", ("error",))),
                ),
                initialization=PreviousPointInitialization(str(initialization_data.get("mode", "previous_successful"))),
                parametric_models=models,
                metadata=data.get("metadata", {}),
            )
        except KeyError as exc:
            raise ValueError(f"Batch recipe missing required field '{exc.args[0]}'") from exc

    def digest(self) -> str:
        """Return a stable SHA-256 digest of the recipe content."""

        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class WorkflowCheckpoint:
    """Portable checkpoint for replaying or resuming a workflow."""

    checkpoint_id: str
    recipe_digest: str
    completed_point_ids: tuple[str, ...]
    result_table: Mapping[str, Any]
    schema_version: str = CHECKPOINT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate checkpoint fields."""

        _non_empty_string(self.checkpoint_id, "checkpoint_id")
        _non_empty_string(self.recipe_digest, "recipe_digest")
        if self.schema_version != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError(f"Unsupported checkpoint schema_version '{self.schema_version}'")
        object.__setattr__(self, "result_table", MappingProxyType(dict(self.result_table)))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible checkpoint mapping."""

        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "recipe_digest": self.recipe_digest,
            "completed_point_ids": list(self.completed_point_ids),
            "result_table": dict(self.result_table),
        }


def create_checkpoint(recipe: BatchRecipe, table: SequentialResultTable, checkpoint_id: str) -> WorkflowCheckpoint:
    """Create a deterministic checkpoint from successful and failed rows."""

    completed = tuple(row.point_id for row in table.rows)
    return WorkflowCheckpoint(
        checkpoint_id=checkpoint_id,
        recipe_digest=recipe.digest(),
        completed_point_ids=completed,
        result_table=table.to_dict(),
    )


def remaining_points(recipe: BatchRecipe, checkpoint: WorkflowCheckpoint) -> tuple[SequentialPointSpec, ...]:
    """Return recipe points not present in a compatible checkpoint."""

    if recipe.digest() != checkpoint.recipe_digest:
        raise ValueError("Checkpoint recipe_digest does not match recipe")
    completed = set(checkpoint.completed_point_ids)
    return tuple(point for point in recipe.points if point.point_id not in completed)


def _parametric_model_from_dict(data: Mapping[str, Any]) -> ParametricParameterModel:
    expression_data = data["expression"]
    return ParametricParameterModel(
        parameter=str(data["parameter"]),
        expression=ParametricExpression(
            expression=str(expression_data["expression"]),
            units=str(expression_data["units"]),
            assumptions=expression_data.get("assumptions", {}),
        ),
    )


def _non_empty_string(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite number")
    return converted
