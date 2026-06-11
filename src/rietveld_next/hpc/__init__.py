"""HPC and cloud execution boundary primitives."""

from rietveld_next.hpc.kubernetes import KUBERNETES_WORKER_SCHEMA_VERSION, KubernetesWorkerManifest
from rietveld_next.hpc.object_store import (
    RESULT_DB_WRITE_SCHEMA_VERSION,
    ObjectStorageURI,
    ResultDatabaseWritePayload,
)
from rietveld_next.hpc.optional_adapters import AdapterAvailability, DaskAdapter, RayAdapter
from rietveld_next.hpc.provenance import (
    HPC_PROVENANCE_SCHEMA_VERSION,
    HPCProvenanceRecord,
    JobProvenanceRecord,
    capture_hpc_provenance,
    capture_runtime_environment,
)
from rietveld_next.hpc.retry import RetryBackoffPolicy
from rietveld_next.hpc.scheduler import (
    SUPPORTED_JOB_STATUSES,
    BatchRun,
    CancellationResult,
    JobResult,
    JobSpec,
    LocalParallelBatchRunner,
    LocalScheduler,
    Scheduler,
    summarize_results,
)
from rietveld_next.hpc.slurm import (
    SLURM_ARRAY_SCHEMA_VERSION,
    SlurmArrayArtifacts,
    SlurmJobArrayAdapter,
    collect_slurm_results,
)
from rietveld_next.hpc.smoke import SMOKE_FIXTURE_SCHEMA_VERSION, BenchmarkClusterSmokeFixture
from rietveld_next.hpc.streams import (
    BEAMLINE_FRAME_SCHEMA_VERSION,
    STATUS_STREAM_SCHEMA_VERSION,
    BeamlineFrame,
    BeamlineLiveIngestMock,
    StatusStreamRecord,
    build_status_stream,
)

__all__ = [
    "BEAMLINE_FRAME_SCHEMA_VERSION",
    "HPC_PROVENANCE_SCHEMA_VERSION",
    "KUBERNETES_WORKER_SCHEMA_VERSION",
    "RESULT_DB_WRITE_SCHEMA_VERSION",
    "SLURM_ARRAY_SCHEMA_VERSION",
    "SMOKE_FIXTURE_SCHEMA_VERSION",
    "STATUS_STREAM_SCHEMA_VERSION",
    "SUPPORTED_JOB_STATUSES",
    "AdapterAvailability",
    "BatchRun",
    "BeamlineFrame",
    "BeamlineLiveIngestMock",
    "BenchmarkClusterSmokeFixture",
    "CancellationResult",
    "DaskAdapter",
    "HPCProvenanceRecord",
    "JobResult",
    "JobProvenanceRecord",
    "JobSpec",
    "KubernetesWorkerManifest",
    "LocalParallelBatchRunner",
    "LocalScheduler",
    "ObjectStorageURI",
    "RayAdapter",
    "ResultDatabaseWritePayload",
    "RetryBackoffPolicy",
    "Scheduler",
    "SlurmArrayArtifacts",
    "SlurmJobArrayAdapter",
    "StatusStreamRecord",
    "build_status_stream",
    "capture_hpc_provenance",
    "capture_runtime_environment",
    "collect_slurm_results",
    "summarize_results",
]
