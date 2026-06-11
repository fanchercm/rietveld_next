"""Deterministic repository boundary checks.

The checks in this module are intentionally lightweight and dependency-free so
they can run in normal CI and local agent validation without requiring build
tooling.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


FORBIDDEN_TOP_LEVEL_IMPLEMENTATION_DIRS: frozenset[str] = frozenset(
    {
        "ai",
        "benchmarks",
        "core",
        "desktop",
        "diffraction",
        "edxrd",
        "hpc",
        "neutron",
        "optimization",
        "tests",
        "tof",
        "web",
        "workflows",
        "xray",
    }
)

ALLOWED_TOP_LEVEL_DIRS: frozenset[str] = frozenset(
    {
        ".agents",
        ".codex",
        ".codegraph",
        ".git",
        ".github",
        "architecture",
        "backend_corpus",
        "backlog",
        "docs",
        "github",
        "prompts",
        "scaffold",
        "schemas",
        "src",
        "validation",
    }
)

DISALLOWED_IMPORT_PREFIXES: dict[str, tuple[str, ...]] = {
    "rietveld_next.core": (
        "rietveld_next.ai",
        "rietveld_next.desktop",
        "rietveld_next.hpc",
        "rietveld_next.web",
        "rietveld_next.workflows",
    ),
    "rietveld_next.diffraction": (
        "rietveld_next.ai",
        "rietveld_next.desktop",
        "rietveld_next.web",
    ),
    "rietveld_next.optimization": (
        "rietveld_next.ai",
        "rietveld_next.desktop",
        "rietveld_next.web",
    ),
}


@dataclass(frozen=True)
class BoundaryIssue:
    """Single repository boundary violation.

    Args:
        code: Stable machine-readable issue code.
        path: Repository-relative path where the issue was found.
        message: Human-readable explanation.
    """

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class BoundaryReport:
    """Result of repository boundary validation."""

    issues: tuple[BoundaryIssue, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        """Return whether no boundary violations were found."""

        return not self.issues

    def require_ok(self) -> None:
        """Raise ``ValueError`` when the report contains violations.

        Raises:
            ValueError: If any boundary issue was collected.
        """

        if self.issues:
            first = self.issues[0]
            raise ValueError(f"{first.code} at {first.path}: {first.message}")


def check_repository_boundaries(root: Path) -> BoundaryReport:
    """Check source layout and import direction guardrails.

    Args:
        root: Repository root to inspect.

    Returns:
        Boundary report with deterministic issue ordering.

    Raises:
        ValueError: If ``root`` does not exist or is not a directory.
    """

    repository_root = root.resolve()
    if not repository_root.is_dir():
        raise ValueError(f"Repository root must be a directory: {root}")

    issues: list[BoundaryIssue] = []
    issues.extend(_check_top_level_directories(repository_root))
    issues.extend(_check_package_tree_location(repository_root))
    issues.extend(_check_import_boundaries(repository_root))
    return BoundaryReport(tuple(sorted(issues, key=lambda issue: (issue.path, issue.code, issue.message))))


def _check_top_level_directories(root: Path) -> Iterable[BoundaryIssue]:
    for child in sorted(root.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        if child.name in FORBIDDEN_TOP_LEVEL_IMPLEMENTATION_DIRS:
            yield BoundaryIssue(
                "forbidden_top_level_directory",
                child.name,
                f"Implementation and tests for {child.name!r} must live under src/.",
            )
        elif child.name not in ALLOWED_TOP_LEVEL_DIRS and not child.name.startswith("."):
            yield BoundaryIssue(
                "unknown_top_level_directory",
                child.name,
                "Top-level directories must be documented before use.",
            )


def _check_package_tree_location(root: Path) -> Iterable[BoundaryIssue]:
    if (root / "PACKAGE_TREE.md").exists():
        yield BoundaryIssue(
            "stale_package_tree_location",
            "PACKAGE_TREE.md",
            "The canonical package tree document is docs/PACKAGE_TREE.md.",
        )
    if not (root / "docs" / "PACKAGE_TREE.md").is_file():
        yield BoundaryIssue(
            "missing_package_tree",
            "docs/PACKAGE_TREE.md",
            "The canonical package tree document is required.",
        )


def _check_import_boundaries(root: Path) -> Iterable[BoundaryIssue]:
    source_root = root / "src" / "rietveld_next"
    if not source_root.is_dir():
        yield BoundaryIssue("missing_source_root", "src/rietveld_next", "Implementation source root is required.")
        return

    for file_path in sorted(source_root.rglob("*.py")):
        module = _module_name(source_root, file_path)
        disallowed_prefixes = _disallowed_prefixes_for_module(module)
        if not disallowed_prefixes:
            continue
        for imported_name in _imported_modules(file_path, module, file_path.name == "__init__.py"):
            if _matches_any_prefix(imported_name, disallowed_prefixes):
                yield BoundaryIssue(
                    "disallowed_import",
                    str(file_path.relative_to(root)),
                    f"{module} must not import {imported_name}.",
                )


def _module_name(source_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(("rietveld_next", *parts))


def _disallowed_prefixes_for_module(module: str) -> tuple[str, ...]:
    for package_prefix, disallowed_prefixes in DISALLOWED_IMPORT_PREFIXES.items():
        if module == package_prefix or module.startswith(f"{package_prefix}."):
            return disallowed_prefixes
    return ()


def _imported_modules(file_path: Path, module: str, is_package_init: bool) -> Iterable[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except SyntaxError as exc:
        yield f"<syntax-error:{exc.lineno}>"
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            for imported_name in _resolve_import_from(node, module, is_package_init):
                yield imported_name


def _resolve_import_from(node: ast.ImportFrom, module: str, is_package_init: bool) -> Iterable[str]:
    base_module = node.module or ""
    if node.level:
        package_module = module if is_package_init else module.rsplit(".", 1)[0]
        package_parts = package_module.split(".")
        keep_count = len(package_parts) - node.level + 1
        if keep_count <= 0:
            return
        prefix = ".".join(package_parts[:keep_count])
        base_module = f"{prefix}.{base_module}" if base_module else prefix

    if base_module:
        yield base_module
    for alias in node.names:
        if alias.name == "*":
            continue
        yield f"{base_module}.{alias.name}" if base_module else alias.name


def _matches_any_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes)
