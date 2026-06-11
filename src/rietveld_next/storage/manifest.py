"""Checksum and file manifest helpers for project packages."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class FileManifestEntry:
    """Checksum metadata for one package file."""

    path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible manifest entry."""

        return {"path": self.path, "sha256": self.sha256, "size_bytes": self.size_bytes}


@dataclass(frozen=True)
class FileManifestVerificationIssue:
    """Single manifest verification issue."""

    code: str
    path: str
    message: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest for a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_file_manifest(package_root: Path) -> tuple[FileManifestEntry, ...]:
    """Build a deterministic SHA-256 manifest for files under a package root.

    Args:
        package_root: Directory to scan recursively.

    Returns:
        Manifest entries sorted by package-relative path.

    Raises:
        ValueError: If ``package_root`` is not a directory.
    """

    root = Path(package_root)
    if not root.is_dir():
        raise ValueError(f"package_root must be a directory: {root}")
    entries: list[FileManifestEntry] = []
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = file_path.relative_to(root).as_posix()
        entries.append(
            FileManifestEntry(path=relative, size_bytes=file_path.stat().st_size, sha256=sha256_file(file_path))
        )
    return tuple(entries)


def verify_file_manifest(package_root: Path, entries: tuple[FileManifestEntry, ...]) -> tuple[FileManifestVerificationIssue, ...]:
    """Verify package files against a manifest.

    Args:
        package_root: Package directory.
        entries: Expected manifest entries.

    Returns:
        Deterministic tuple of verification issues.
    """

    root = Path(package_root)
    issues: list[FileManifestVerificationIssue] = []
    for entry in sorted(entries, key=lambda item: item.path):
        target = root / entry.path
        if not target.is_file():
            issues.append(FileManifestVerificationIssue("missing_file", entry.path, "Manifest file is missing."))
            continue
        actual_size = target.stat().st_size
        if actual_size != entry.size_bytes:
            issues.append(
                FileManifestVerificationIssue(
                    "size_mismatch",
                    entry.path,
                    f"Expected {entry.size_bytes} bytes, found {actual_size}.",
                )
            )
        actual_digest = sha256_file(target)
        if actual_digest != entry.sha256:
            issues.append(FileManifestVerificationIssue("checksum_mismatch", entry.path, "SHA-256 digest mismatch."))
    return tuple(issues)
