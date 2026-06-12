"""Storage command-line helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from rietveld_next.core.schema import SchemaValidationError, validate_project_json


def validate_project_schema_file(path: Path) -> tuple[bool, str]:
    """Validate a project JSON file against the canonical schema.

    Args:
        path: Project JSON file path.

    Returns:
        ``(ok, message)`` tuple suitable for CLI output.
    """
    target = Path(path)
    try:
        validate_project_json(target.read_text(encoding="utf-8"))
    except OSError as exc:
        return False, f"read_error: {exc}"
    except SchemaValidationError as exc:
        first = exc.issues[0]
        return False, f"schema_error: {first.path}: {first.message}"
    return True, "ok"


def main(argv: list[str] | None = None) -> int:
    """Run the storage CLI."""
    parser = argparse.ArgumentParser(prog="rietveld-next-storage")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate-project", help="validate project JSON")
    validate_parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    if args.command == "validate-project":
        ok, message = validate_project_schema_file(args.path)
        print(message)
        return 0 if ok else 1
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    sys.exit(main())
