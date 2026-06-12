"""Small opt-in benchmark helpers for workflow, AI, and HPC overheads."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
from typing import Any

from rietveld_next.ai.tools import ToolContract, ToolRegistry
from rietveld_next.benchmarks.results import BenchmarkResult, BenchmarkTiming
from rietveld_next.hpc.object_store import ObjectStorageURI
from rietveld_next.hpc.scheduler import JobSpec
from rietveld_next.hpc.slurm import SlurmArrayArtifacts, SlurmJobArrayAdapter
from rietveld_next.workflows.sequential import (
    PreviousPointInitialization,
    RetryPolicy,
    SequentialPointSpec,
    SequentialResultTable,
    SequentialRunRequest,
    SequentialRunner,
    export_parameter_evolution,
)


def run_sequential_refinement_workflow_overhead_benchmark(
    *,
    sequence_points: int = 4,
    iterations: int = 1,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark deterministic sequential-refinement orchestration overhead.

    Args:
        sequence_points: Number of synthetic time/temperature points.
        iterations: Number of measured workflow runs.
        warmup: Number of unmeasured workflow runs before timing.
        seed: Deterministic fixture seed recorded in metadata.

    Returns:
        Benchmark result with total/per-point runtime and trajectory checksum.

    Raises:
        ValueError: If sizing arguments are invalid.
    """

    _positive_int(sequence_points, "sequence_points")
    _positive_int(iterations, "iterations")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    for _ in range(warmup):
        _run_sequential_fixture(sequence_points=sequence_points, seed=seed)

    measurements: list[float] = []
    per_point_measurements: list[float] = []
    final_checksum = 0.0
    final_failures = 0
    final_trajectory: list[dict[str, Any]] = []
    for _ in range(iterations):
        start = time.perf_counter()
        table = _run_sequential_fixture(sequence_points=sequence_points, seed=seed)
        elapsed = time.perf_counter() - start
        measurements.append(elapsed)
        per_point_measurements.append(elapsed / float(sequence_points))
        trajectory = list(export_parameter_evolution(table, ["lattice_a_angstrom"]))
        final_checksum = _trajectory_checksum(trajectory)
        final_failures = sum(1 for row in table.rows if row.status != "ok")
        final_trajectory = trajectory

    total_runtime = sum(measurements)
    return BenchmarkResult(
        name="workflow.sequential_refinement.python.small.synthetic",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=sequence_points,
        iterations=iterations,
        warmup=warmup,
        checksum=final_checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(measurements),
            min_seconds=min(measurements),
            max_seconds=max(measurements),
            compile_seconds=None,
        ),
        environment={
            **_base_environment(seed=seed, issue_numbers=[305]),
            "sequence_points": sequence_points,
            "total_runtime_seconds": total_runtime,
            "per_point_runtime_seconds": {
                "median": statistics.median(per_point_measurements),
                "min": min(per_point_measurements),
                "max": max(per_point_measurements),
            },
            "failures": final_failures,
            "parameter_trajectory_checksum": final_checksum,
            "parameter_trajectory": final_trajectory,
            "initialization": "previous_successful",
            "synthetic_model": {
                "parameter": "lattice_a_angstrom",
                "unit": "angstrom",
                "temperature_start_k": 300.0 + float(seed),
                "temperature_step_k": 5.0,
            },
        },
    )


def build_deterministic_tool_registry() -> ToolRegistry:
    """Create a mock deterministic AI tool registry fixture.

    Returns:
        Registry with three deterministic handlers and no LLM calls.
    """

    registry = ToolRegistry()
    registry.register(
        ToolContract(
            name="estimate_background",
            input_fields=("scan_id", "point_count"),
            output_fields=("background_level", "numerical_work_units"),
            description="Estimate a synthetic background level without an LLM.",
        ),
        _estimate_background,
    )
    registry.register(
        ToolContract(
            name="score_residual",
            input_fields=("scan_id", "background_level"),
            output_fields=("score", "numerical_work_units"),
            description="Score a synthetic residual payload without an LLM.",
        ),
        _score_residual,
    )
    registry.register(
        ToolContract(
            name="select_strategy",
            input_fields=("scan_id", "score"),
            output_fields=("strategy", "numerical_work_units"),
            description="Select a deterministic refinement strategy without an LLM.",
        ),
        _select_strategy,
    )
    return registry


def run_ai_tool_call_overhead_benchmark(
    *,
    tool_calls: int = 12,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark deterministic AI tool-call overhead with LLM latency excluded.

    Args:
        tool_calls: Number of measured deterministic tool calls.
        warmup: Number of unmeasured tool calls before timing.
        seed: Deterministic fixture seed recorded in metadata.

    Returns:
        Benchmark result reporting calls per second and per-tool latency stats.

    Raises:
        ValueError: If sizing arguments are invalid.
    """

    _positive_int(tool_calls, "tool_calls")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")

    registry = build_deterministic_tool_registry()
    for index in range(warmup):
        name, payload = _tool_call_fixture(index=index, seed=seed)
        registry.call_tool(name, payload)

    total_work_units = 0.0
    latencies: list[float] = []
    latencies_by_tool: dict[str, list[float]] = {
        "estimate_background": [],
        "score_residual": [],
        "select_strategy": [],
    }
    checksum = 0.0

    total_start = time.perf_counter()
    for index in range(tool_calls):
        name, payload = _tool_call_fixture(index=index, seed=seed)
        call_start = time.perf_counter()
        result = registry.call_tool(name, payload)
        call_elapsed = time.perf_counter() - call_start
        if result.status != "ok" or result.output is None:
            raise RuntimeError(f"deterministic tool fixture failed for {name}: {result.error}")
        latencies.append(call_elapsed)
        latencies_by_tool[name].append(call_elapsed)
        output = dict(result.output)
        total_work_units += float(output["numerical_work_units"])
        checksum += _mapping_checksum({"tool": name, "payload": payload, "output": output})
    total_elapsed = time.perf_counter() - total_start
    handler_seconds = 0.0
    orchestration_seconds = total_elapsed

    return BenchmarkResult(
        name="ai.tool_call_overhead.python.small.mock",
        backend="python",
        status="ok",
        dtype="float64",
        input_size=tool_calls,
        iterations=tool_calls,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(
            median_seconds=statistics.median(latencies),
            min_seconds=min(latencies),
            max_seconds=max(latencies),
            compile_seconds=None,
        ),
        environment={
            **_base_environment(seed=seed, issue_numbers=[320]),
            "tool_calls": tool_calls,
            "llm_latency_included": False,
            "mock_llm_latency_seconds": 0.0,
            "calls_per_second": tool_calls / max(total_elapsed, 1.0e-12),
            "total_runtime_seconds": total_elapsed,
            "handler_runtime_seconds": handler_seconds,
            "numerical_runtime_seconds": 0.0,
            "orchestration_runtime_seconds": orchestration_seconds,
            "numerical_work_units": total_work_units,
            "per_tool_latency_seconds": _latency_summary_by_tool(latencies_by_tool),
            "action_log_entries": len(registry.action_log),
            "registered_tools": sorted(registry.contracts),
        },
    )


def run_slurm_job_array_packaging_benchmark(
    *,
    output_directory: str | Path,
    job_count: int = 4,
    warmup: int = 0,
    seed: int = 0,
) -> BenchmarkResult:
    """Benchmark dry-run Slurm job-array artifact packaging.

    Args:
        output_directory: Directory where dry-run artifacts are written.
        job_count: Number of synthetic batch jobs to package.
        warmup: Number of unmeasured packaging runs before timing.
        seed: Deterministic fixture seed recorded in metadata.

    Returns:
        Benchmark result with payload size, generated files, and runtime.

    Raises:
        ValueError: If sizing arguments are invalid.
    """

    _positive_int(job_count, "job_count")
    _nonnegative_int(warmup, "warmup")
    _nonnegative_int(seed, "seed")
    output_path = _prepared_output_directory(output_directory)

    for _ in range(warmup):
        _render_slurm_artifacts(job_count=job_count, output_path=output_path, seed=seed, write_files=False)

    start = time.perf_counter()
    artifacts, generated_files = _render_slurm_artifacts(
        job_count=job_count,
        output_path=output_path,
        seed=seed,
        write_files=True,
    )
    elapsed = time.perf_counter() - start
    payload_size_bytes = len(artifacts.script_text.encode("utf-8")) + len(artifacts.task_manifest_jsonl.encode("utf-8"))
    checksum = _text_checksum(artifacts.script_text + artifacts.task_manifest_jsonl)

    return BenchmarkResult(
        name="hpc.slurm_job_array_packaging.python.small.dry_run",
        backend="python",
        status="ok",
        dtype="json",
        input_size=job_count,
        iterations=1,
        warmup=warmup,
        checksum=checksum,
        timing=BenchmarkTiming(elapsed, elapsed, elapsed, compile_seconds=None),
        environment={
            **_base_environment(seed=seed, issue_numbers=[322]),
            "job_count": job_count,
            "payload_size_bytes": payload_size_bytes,
            "generated_files": generated_files,
            "output_directory": str(output_path),
            "submitted_jobs": False,
            "slurm_artifact_schema_version": artifacts.schema_version,
            "result_uri": artifacts.result_uri.to_uri(),
        },
    )


def _run_sequential_fixture(*, sequence_points: int, seed: int) -> SequentialResultTable:
    points = [
        SequentialPointSpec(
            point_id=f"point_{index:03d}",
            dataset_id=f"synthetic_scan_{index:03d}",
            variables={"temperature_k": 300.0 + float(seed) + 5.0 * float(index)},
        )
        for index in range(sequence_points)
    ]
    runner = SequentialRunner(
        "benchmark-sequential-refinement",
        points,
        {"lattice_a_angstrom": 4.0 + 0.001 * float(seed)},
        _synthetic_refinement_handler,
        initialization=PreviousPointInitialization("previous_successful"),
        retry_policy=RetryPolicy(max_attempts=1),
    )
    return runner.run()


def _synthetic_refinement_handler(request: SequentialRunRequest) -> Mapping[str, Any]:
    temperature = float(request.point.variables["temperature_k"])
    initial_a = float(request.initial_parameters["lattice_a_angstrom"])
    target_a = 4.0 + (temperature - 300.0) * 2.0e-4
    refined_a = target_a + 0.1 * (initial_a - target_a)
    residual_0 = refined_a - target_a
    residual_1 = residual_0 * 0.5
    return {
        "status": "ok",
        "parameters": {
            "lattice_a_angstrom": {
                "value": refined_a,
                "unit": "angstrom",
                "uncertainty": 1.0e-4,
                "provenance": {
                    "fixture": "deterministic_sequential_refinement",
                    "assumption": "single lattice parameter linear in temperature",
                },
            }
        },
        "metrics": {
            "objective": residual_0 * residual_0 + residual_1 * residual_1,
            "temperature_k": temperature,
        },
        "residuals": [residual_0, residual_1],
    }


def _estimate_background(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    point_count = int(payload["point_count"])
    level = 0.001 * float(point_count) + 0.01 * float(len(str(payload["scan_id"])))
    return {
        "background_level": level,
        "numerical_work_units": float(point_count),
    }


def _score_residual(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    background = float(payload["background_level"])
    score = background * background + 0.125
    return {
        "score": score,
        "numerical_work_units": 1.0,
    }


def _select_strategy(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    score = float(payload["score"])
    strategy = "continue" if score < 0.5 else "review"
    return {
        "strategy": strategy,
        "numerical_work_units": 1.0,
    }


def _tool_call_fixture(*, index: int, seed: int) -> tuple[str, dict[str, Any]]:
    scan_id = f"scan_{seed:02d}_{index:04d}"
    phase = index % 3
    if phase == 0:
        return "estimate_background", {"scan_id": scan_id, "point_count": 64 + seed + index}
    if phase == 1:
        return "score_residual", {"scan_id": scan_id, "background_level": 0.1 + 0.001 * float(seed + index)}
    return "select_strategy", {"scan_id": scan_id, "score": 0.1 + 0.01 * float((seed + index) % 5)}


def _render_slurm_artifacts(
    *,
    job_count: int,
    output_path: Path,
    seed: int,
    write_files: bool,
) -> tuple[SlurmArrayArtifacts, list[dict[str, Any]]]:
    jobs = [
        JobSpec(
            job_id=f"refine_{index:04d}",
            command="refine",
            payload={
                "scan_id": f"synthetic_scan_{seed:02d}_{index:04d}",
                "sequence_index": index,
                "temperature_k": 300.0 + float(seed) + 2.5 * float(index),
            },
            resources={"cpus": 1, "memory_mb": 512},
            metadata={"fixture": "slurm_packaging_benchmark", "seed": seed},
        )
        for index in range(job_count)
    ]
    adapter = SlurmJobArrayAdapter(
        job_name="rn-benchmark-refine",
        result_uri=ObjectStorageURI.parse((output_path / "results").as_uri()),
        cpus_per_task=1,
    )
    artifacts = adapter.render_artifacts(jobs)
    generated_files: list[dict[str, Any]] = []
    if write_files:
        files = {
            "submit_array.sbatch": artifacts.script_text,
            "task_manifest.jsonl": artifacts.task_manifest_jsonl,
        }
        for filename, text in files.items():
            path = output_path / filename
            path.write_text(text, encoding="utf-8")
            generated_files.append(
                {
                    "path": str(path),
                    "name": filename,
                    "size_bytes": path.stat().st_size,
                }
            )
    return artifacts, generated_files


def _prepared_output_directory(output_directory: str | Path) -> Path:
    if isinstance(output_directory, str) and not output_directory:
        raise ValueError("output_directory must be a non-empty path.")
    output_path = Path(output_directory).resolve()
    if output_path.exists() and not output_path.is_dir():
        raise ValueError(f"output_directory must be a directory, got {output_path}.")
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _latency_summary_by_tool(latencies_by_tool: dict[str, list[float]]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for tool_name, latencies in sorted(latencies_by_tool.items()):
        if latencies:
            summary[tool_name] = {
                "calls": len(latencies),
                "median": statistics.median(latencies),
                "min": min(latencies),
                "max": max(latencies),
            }
        else:
            summary[tool_name] = {"calls": 0, "median": 0.0, "min": 0.0, "max": 0.0}
    return summary


def _base_environment(*, seed: int, issue_numbers: list[int]) -> dict[str, Any]:
    return {
        "benchmark_issue_numbers": issue_numbers,
        "git_commit": _git_commit_or_none(),
        "platform_machine": platform.machine(),
        "platform_system": platform.system(),
        "python_version": platform.python_version(),
        "seed": seed,
        "timing_model": {
            "compile_seconds": "none for dependency-free Python fixtures",
            "steady_state": "median/min/max measured wall time from perf_counter",
            "warmup": "unmeasured fixture runs before steady-state timing",
        },
    }


def _git_commit_or_none() -> str | None:
    repo_root = Path(__file__).resolve().parents[3]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=1.0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = completed.stdout.strip()
    if completed.returncode != 0 or not commit:
        return None
    return commit


def _trajectory_checksum(trajectory: list[dict[str, Any]]) -> float:
    return _mapping_checksum({"trajectory": trajectory})


def _mapping_checksum(value: Mapping[str, Any]) -> float:
    return _text_checksum(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _text_checksum(text: str) -> float:
    return float(sum((index + 1) * ord(character) for index, character in enumerate(text)))


def _positive_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value!r}.")


def _nonnegative_int(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}.")
