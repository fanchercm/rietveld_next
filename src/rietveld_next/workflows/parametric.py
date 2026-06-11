"""Parametric expression API for workflow-level parameter models."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import math
from types import MappingProxyType
from typing import Any, Mapping


_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
}


@dataclass(frozen=True)
class ParametricExpression:
    """Safe arithmetic expression evaluated against external variables.

    Args:
        expression: Arithmetic expression using variable names, numeric
            literals, and ``abs``, ``exp``, ``log``, or ``sqrt``.
        units: Unit of the evaluated parameter value.
        assumptions: Audit metadata describing model assumptions.

    Example:
        >>> ParametricExpression("a0 + alpha * (temperature_k - 300)", "A").evaluate(
        ...     {"a0": 5.0, "alpha": 0.01, "temperature_k": 310.0}
        ... )
        5.1
    """

    expression: str
    units: str
    assumptions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate expression syntax and units."""

        if not isinstance(self.expression, str) or not self.expression:
            raise ValueError("ParametricExpression.expression must be non-empty")
        if not isinstance(self.units, str) or not self.units:
            raise ValueError("ParametricExpression.units must be non-empty")
        _validate_ast(ast.parse(self.expression, mode="eval"))
        object.__setattr__(self, "assumptions", MappingProxyType(dict(self.assumptions)))

    def evaluate(self, variables: Mapping[str, float]) -> float:
        """Evaluate the expression with finite numeric variables."""

        names = {str(name): _finite_float(value, f"variables.{name}") for name, value in variables.items()}
        result = _evaluate_node(ast.parse(self.expression, mode="eval").body, names)
        return _finite_float(result, "expression result")

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "expression": self.expression,
            "units": self.units,
            "assumptions": dict(sorted(self.assumptions.items())),
        }


@dataclass(frozen=True)
class ParametricParameterModel:
    """Bind a safe expression to one refinement parameter."""

    parameter: str
    expression: ParametricExpression

    def __post_init__(self) -> None:
        """Validate parameter identity."""

        if not isinstance(self.parameter, str) or not self.parameter:
            raise ValueError("ParametricParameterModel.parameter must be non-empty")

    def value_at(self, variables: Mapping[str, float]) -> float:
        """Evaluate the model at external variables."""

        return self.expression.evaluate(variables)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible mapping."""

        return {"parameter": self.parameter, "expression": self.expression.to_dict()}


@dataclass(frozen=True)
class TemperatureParameterModel:
    """Linear temperature-dependent workflow parameter model.

    Args:
        parameter: Stable parameter path.
        reference_value: Value at ``reference_temperature_k``.
        slope_per_kelvin: Linear slope in parameter units per kelvin.
        reference_temperature_k: Reference temperature in kelvin.
        units: Parameter units.
    """

    parameter: str
    reference_value: float
    slope_per_kelvin: float
    reference_temperature_k: float
    units: str

    def __post_init__(self) -> None:
        """Validate temperature model fields."""

        _non_empty_string(self.parameter, "parameter")
        _non_empty_string(self.units, "units")
        object.__setattr__(self, "reference_value", _finite_float(self.reference_value, "reference_value"))
        object.__setattr__(self, "slope_per_kelvin", _finite_float(self.slope_per_kelvin, "slope_per_kelvin"))
        reference = _finite_float(self.reference_temperature_k, "reference_temperature_k")
        if reference < 0.0:
            raise ValueError("reference_temperature_k must be non-negative")
        object.__setattr__(self, "reference_temperature_k", reference)

    def value_at(self, temperature_k: float) -> float:
        """Return the parameter value at a temperature in kelvin."""

        temperature = _finite_float(temperature_k, "temperature_k")
        if temperature < 0.0:
            raise ValueError("temperature_k must be non-negative")
        return self.reference_value + self.slope_per_kelvin * (temperature - self.reference_temperature_k)

    def as_parametric_model(self) -> ParametricParameterModel:
        """Return an equivalent expression-backed parameter model."""

        return ParametricParameterModel(
            self.parameter,
            ParametricExpression(
                "reference_value + slope_per_kelvin * (temperature_k - reference_temperature_k)",
                self.units,
                assumptions={"model": "linear_temperature", "temperature_units": "K"},
            ),
        )


@dataclass(frozen=True)
class PressureParameterModel:
    """Linear pressure-dependent workflow parameter model."""

    parameter: str
    reference_value: float
    slope_per_gpa: float
    reference_pressure_gpa: float
    units: str

    def __post_init__(self) -> None:
        """Validate pressure model fields."""

        _non_empty_string(self.parameter, "parameter")
        _non_empty_string(self.units, "units")
        object.__setattr__(self, "reference_value", _finite_float(self.reference_value, "reference_value"))
        object.__setattr__(self, "slope_per_gpa", _finite_float(self.slope_per_gpa, "slope_per_gpa"))
        reference = _finite_float(self.reference_pressure_gpa, "reference_pressure_gpa")
        if reference < 0.0:
            raise ValueError("reference_pressure_gpa must be non-negative")
        object.__setattr__(self, "reference_pressure_gpa", reference)

    def value_at(self, pressure_gpa: float) -> float:
        """Return the parameter value at a pressure in gigapascals."""

        pressure = _finite_float(pressure_gpa, "pressure_gpa")
        if pressure < 0.0:
            raise ValueError("pressure_gpa must be non-negative")
        return self.reference_value + self.slope_per_gpa * (pressure - self.reference_pressure_gpa)

    def as_parametric_model(self) -> ParametricParameterModel:
        """Return an equivalent expression-backed parameter model."""

        return ParametricParameterModel(
            self.parameter,
            ParametricExpression(
                "reference_value + slope_per_gpa * (pressure_gpa - reference_pressure_gpa)",
                self.units,
                assumptions={"model": "linear_pressure", "pressure_units": "GPa"},
            ),
        )


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Expression | ast.BinOp | ast.UnaryOp | ast.Call | ast.Load | ast.Constant | ast.Name):
            continue
        if isinstance(node, ast.Add | ast.Sub | ast.Mult | ast.Div | ast.Pow | ast.USub | ast.UAdd):
            continue
        raise ValueError(f"Unsupported expression syntax: {node.__class__.__name__}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS:
                raise ValueError("Unsupported expression function")


def _evaluate_node(node: ast.AST, variables: Mapping[str, float]) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise ValueError("Expression constants must be numeric")
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"Missing expression variable '{node.id}'")
        return variables[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _evaluate_node(node.operand, variables)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value
    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left, variables)
        right = _evaluate_node(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0.0:
                raise ValueError("Expression division by zero")
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = _ALLOWED_FUNCTIONS[node.func.id]
        args = [_evaluate_node(argument, variables) for argument in node.args]
        return float(function(*args))
    raise ValueError(f"Unsupported expression syntax: {node.__class__.__name__}")


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
