"""Deterministic AI tool boundary primitives."""

from rietveld_next.ai.approval import ApprovalCheckpoint, ApprovalLedger
from rietveld_next.ai.diagnostics import (
    DiagnosticFinding,
    ResidualPatternClassification,
    classify_residual_pattern,
    detect_nonphysical_solution,
    detect_overfitting,
    diagnose_residuals,
)
from rietveld_next.ai.evals import (
    EvaluationSuite,
    EvaluationTask,
    default_ai_evaluation_suite,
    run_prompt_injection_regression_suite,
)
from rietveld_next.ai.planning import AutonomousRecipePlan, RecipeStep, plan_autonomous_recipe
from rietveld_next.ai.reports import Citation, CopilotReport, action_log_viewer_payload, generate_copilot_report
from rietveld_next.ai.safety import (
    SafetyFinding,
    detect_prompt_injection,
    evaluate_tool_call_safety,
    prompt_injection_regression_cases,
    safety_allows,
)
from rietveld_next.ai.strategy import (
    StrategyRecommendation,
    StrategyRule,
    StrategyRuleEngine,
    default_strategy_engine,
)
from rietveld_next.ai.tools import (
    ActionLogEntry,
    ToolCallResult,
    ToolContract,
    ToolField,
    ToolRegistry,
)
from rietveld_next.ai.wrappers import (
    TOOL_CONTRACTS,
    add_constraint_tool,
    compare_models_tool,
    create_refinement_tool_registry,
    diagnose_residuals_tool,
    freeze_parameter_tool,
    rollback_tool,
    run_refinement_tool,
    set_refinement_flags_tool,
)

__all__ = [
    "ActionLogEntry",
    "ApprovalCheckpoint",
    "ApprovalLedger",
    "AutonomousRecipePlan",
    "Citation",
    "CopilotReport",
    "DiagnosticFinding",
    "EvaluationSuite",
    "EvaluationTask",
    "RecipeStep",
    "ResidualPatternClassification",
    "SafetyFinding",
    "StrategyRecommendation",
    "StrategyRule",
    "StrategyRuleEngine",
    "TOOL_CONTRACTS",
    "ToolCallResult",
    "ToolContract",
    "ToolField",
    "ToolRegistry",
    "action_log_viewer_payload",
    "add_constraint_tool",
    "classify_residual_pattern",
    "compare_models_tool",
    "create_refinement_tool_registry",
    "default_ai_evaluation_suite",
    "default_strategy_engine",
    "detect_nonphysical_solution",
    "detect_overfitting",
    "detect_prompt_injection",
    "diagnose_residuals",
    "diagnose_residuals_tool",
    "evaluate_tool_call_safety",
    "freeze_parameter_tool",
    "generate_copilot_report",
    "plan_autonomous_recipe",
    "prompt_injection_regression_cases",
    "rollback_tool",
    "run_prompt_injection_regression_suite",
    "run_refinement_tool",
    "safety_allows",
    "set_refinement_flags_tool",
]
