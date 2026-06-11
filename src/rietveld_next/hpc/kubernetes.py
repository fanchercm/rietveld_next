"""Kubernetes worker manifest payload model."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Sequence

from rietveld_next.hpc.serialization import immutable_mapping


KUBERNETES_WORKER_SCHEMA_VERSION = "hpc-kubernetes-worker-v1"
_DNS_LABEL_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")


@dataclass(frozen=True)
class KubernetesWorkerManifest:
    """Kubernetes Job manifest for an HPC worker payload.

    Args:
        name: Kubernetes DNS label used for the Job and container.
        image: Container image reference.
        command: Worker command and arguments.
        env: Environment variables passed to the container.
        labels: Pod and Job labels.
        resources: Kubernetes resource requests and limits.

    Raises:
        ValueError: If required fields are empty or invalid.
        TypeError: If mapping fields are not mappings.
    """

    name: str
    image: str
    command: Sequence[str]
    env: Mapping[str, str] = field(default_factory=dict)
    labels: Mapping[str, str] = field(default_factory=dict)
    resources: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = field(default=KUBERNETES_WORKER_SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not _DNS_LABEL_PATTERN.fullmatch(self.name):
            raise ValueError("name must be a Kubernetes DNS label")
        if not self.image:
            raise ValueError("image must be non-empty")
        if not self.command or any(not item for item in self.command):
            raise ValueError("command must contain non-empty strings")
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "env", immutable_mapping(self.env, "env"))
        object.__setattr__(self, "labels", immutable_mapping(self.labels, "labels"))
        object.__setattr__(self, "resources", immutable_mapping(self.resources, "resources"))

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic Kubernetes Job manifest payload."""

        labels = {"app.kubernetes.io/name": self.name, **dict(sorted(self.labels.items()))}
        container: dict[str, Any] = {
            "name": self.name,
            "image": self.image,
            "command": list(self.command),
            "env": [{"name": key, "value": value} for key, value in sorted(self.env.items())],
        }
        if self.resources:
            container["resources"] = dict(sorted(self.resources.items()))
        return {
            "schema_version": self.schema_version,
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {"name": self.name, "labels": labels},
            "spec": {
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {"restartPolicy": "Never", "containers": [container]},
                },
                "backoffLimit": 0,
            },
        }
