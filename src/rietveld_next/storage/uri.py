"""Package-local data URI resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote


@dataclass(frozen=True)
class ResolvedDataUri:
    """Resolved data URI target.

    Args:
        uri: Original URI string.
        path: Absolute filesystem path.
        scheme: URI scheme used for resolution.
    """

    uri: str
    path: Path
    scheme: str


def resolve_data_uri(package_root: Path, uri: str) -> ResolvedDataUri:
    """Resolve a supported data URI relative to a package root.

    Supported forms are package-relative paths such as ``arrays/x.bin``,
    ``package://arrays/x.bin``, and local ``file://`` URIs. Package-relative
    targets are prevented from escaping the package root.

    Args:
        package_root: Root directory for package-relative paths.
        uri: URI or relative path to resolve.

    Returns:
        Resolved URI target.

    Raises:
        ValueError: If the URI is empty, unsupported, or escapes the package.
    """

    if not isinstance(uri, str) or not uri:
        raise ValueError("uri must be a non-empty string.")
    root = Path(package_root).resolve()
    parsed = urlparse(uri)

    if parsed.scheme in ("", "package"):
        raw_path = parsed.path or parsed.netloc
        if parsed.scheme == "package" and parsed.netloc and parsed.path:
            raw_path = f"{parsed.netloc}{parsed.path}"
        target = (root / unquote(raw_path).lstrip("/")).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Data URI escapes package root: {uri}") from exc
        return ResolvedDataUri(uri=uri, path=target, scheme=parsed.scheme or "package")

    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ValueError(f"Only local file URIs are supported: {uri}")
        return ResolvedDataUri(uri=uri, path=Path(unquote(parsed.path)).resolve(), scheme="file")

    raise ValueError(f"Unsupported data URI scheme: {parsed.scheme}")
