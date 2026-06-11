"""Object storage URI and distributed result writer payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from rietveld_next.hpc.serialization import immutable_mapping


RESULT_DB_WRITE_SCHEMA_VERSION = "hpc-result-db-write-v1"
SUPPORTED_OBJECT_URI_SCHEMES = frozenset({"file", "s3", "gs", "az"})


@dataclass(frozen=True)
class ObjectStorageURI:
    """Portable object storage URI.

    Args:
        scheme: Storage scheme, such as ``"file"``, ``"s3"``, ``"gs"``, or
            ``"az"``.
        bucket: Bucket, container, or empty string for file URIs.
        key: Object key or absolute file path for file URIs.

    Raises:
        ValueError: If the URI components are incomplete or unsupported.
    """

    scheme: str
    bucket: str
    key: str

    def __post_init__(self) -> None:
        if self.scheme not in SUPPORTED_OBJECT_URI_SCHEMES:
            raise ValueError(f"Unsupported object storage scheme {self.scheme!r}")
        if not self.key:
            raise ValueError("ObjectStorageURI.key must be non-empty")
        if self.scheme == "file":
            if self.bucket:
                raise ValueError("file URIs must not include a bucket")
            if not self.key.startswith("/"):
                raise ValueError("file URI key must be an absolute path")
        elif not self.bucket:
            raise ValueError(f"{self.scheme} URIs require a bucket")

    @classmethod
    def parse(cls, uri: str) -> "ObjectStorageURI":
        """Parse a URI string into an :class:`ObjectStorageURI`.

        Example:
            >>> ObjectStorageURI.parse("s3://bucket/results.json").bucket
            'bucket'
        """

        if not uri:
            raise ValueError("uri must be non-empty")
        parsed = urlparse(uri)
        if not parsed.scheme:
            raise ValueError("uri must include a scheme")
        if parsed.scheme == "file":
            if parsed.netloc:
                raise ValueError("file URIs must use a local absolute path")
            return cls(scheme="file", bucket="", key=parsed.path)
        key = parsed.path.lstrip("/")
        return cls(scheme=parsed.scheme, bucket=parsed.netloc, key=key)

    def to_uri(self) -> str:
        """Return the canonical URI string."""

        if self.scheme == "file":
            return f"file://{self.key}"
        return f"{self.scheme}://{self.bucket}/{self.key}"

    def to_dict(self) -> dict[str, str]:
        """Return a deterministic JSON-compatible mapping."""

        return {"scheme": self.scheme, "bucket": self.bucket, "key": self.key, "uri": self.to_uri()}


@dataclass(frozen=True)
class ResultDatabaseWritePayload:
    """Framework-free payload for a distributed result database writer.

    The payload describes what an external writer should persist without
    opening a network connection or importing a database driver.
    """

    destination: ObjectStorageURI
    table: str
    records: Sequence[Mapping[str, Any]]
    primary_key_fields: tuple[str, ...] = ("job_id",)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=RESULT_DB_WRITE_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not self.table:
            raise ValueError("ResultDatabaseWritePayload.table must be non-empty")
        if not self.records:
            raise ValueError("ResultDatabaseWritePayload.records must be non-empty")
        if not self.primary_key_fields:
            raise ValueError("primary_key_fields must be non-empty")
        for field_name in self.primary_key_fields:
            if not field_name:
                raise ValueError("primary_key_fields must not contain empty names")

        copied_records: list[Mapping[str, Any]] = []
        for index, record in enumerate(self.records):
            copied_records.append(immutable_mapping(record, f"records[{index}]"))
            for primary_key in self.primary_key_fields:
                if primary_key not in record:
                    raise ValueError(f"records[{index}] is missing primary key field {primary_key!r}")
        object.__setattr__(self, "records", tuple(copied_records))
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata, "metadata"))
        object.__setattr__(self, "primary_key_fields", tuple(self.primary_key_fields))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible writer payload."""

        return {
            "schema_version": self.schema_version,
            "destination": self.destination.to_dict(),
            "table": self.table,
            "primary_key_fields": list(self.primary_key_fields),
            "records": [dict(sorted(record.items())) for record in self.records],
            "metadata": dict(sorted(self.metadata.items())),
        }
