"""Shared, fail-closed Google Colab helpers for the Distributed BFS MPI workflow.

The notebooks execute MPI jobs with an explicitly selected Open MPI compiler and
launcher. They never silently fall back to a serial MPI compatibility shim.
"""
from __future__ import annotations

import csv
from collections import deque
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import threading
import queue
import time
import zipfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

RUNNER_VERSION = "mpi-validated-v2-openmpi"
MPI_PREFIXES = (
    "OMPI_", "PMI_", "PMIX_", "HYDRA_", "MPIR_", "MPIEXEC_",
    "MPICH_", "I_MPI_", "MV2_", "PRTE_", "OPAL_", "SLURM_",
)


def clean_mpi_environment(base: dict | None = None) -> tuple[dict, list[str]]:
    env = dict(os.environ if base is None else base)
    removed = []
    for key in list(env):
        if key.startswith(MPI_PREFIXES):
            removed.append(key)
            env.pop(key, None)
    # A previously installed MPI implementation may have left library/include
    # paths in the notebook environment. Keep ordinary paths, but remove any
    # MPICH/Hydra-specific entries so Open MPI's wrapper and runtime stay paired.
    for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "LIBRARY_PATH", "CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH"):
        value = env.get(key)
        if not value:
            continue
        parts = value.split(":" if key != "LD_PRELOAD" else " ")
        kept = [part for part in parts if not re.search(r"mpich|hydra", part, re.IGNORECASE)]
        if len(kept) != len(parts):
            removed.append(f"{key}:mpich_or_hydra_entries")
            if kept:
                env[key] = (":" if key != "LD_PRELOAD" else " ").join(kept)
            else:
                env.pop(key, None)
    # Colab runtimes commonly execute notebook kernels as root. Open MPI
    # requires an explicit opt-in for this container-like use case.
    env["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
    env["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"
    return env, sorted(removed)


def run_stream(
    cmd: Iterable,
    *,
    env: dict | None = None,
    cwd: str | Path | None = None,
    log_path: str | Path | None = None,
    timeout: int | None = None,
    check: bool = True,
) -> tuple[str, int]:
    """Run a process group, stream output, and enforce a real wall timeout."""
    cmd = [str(x) for x in cmd]
    print("\n$ " + " ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    lines = deque(maxlen=2000)
    output_queue: queue.Queue = queue.Queue()
    log = Path(log_path).open("w", encoding="utf-8") if log_path else None

    def reader() -> None:
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()
    start = time.monotonic()
    finished_reading = False
    try:
        while not finished_reading:
            if timeout is not None and time.monotonic() - start > timeout and proc.poll() is None:
                raise TimeoutError(f"Command exceeded {timeout} seconds: {cmd}")
            try:
                item = output_queue.get(timeout=0.25)
            except queue.Empty:
                if proc.poll() is not None and not reader_thread.is_alive():
                    break
                continue
            if item is None:
                finished_reading = True
                continue
            lines.append(item)
            if log:
                log.write(item)
                log.flush()
            print(item, end="")
        rc = proc.wait()
    except BaseException:
        # Kill the whole launcher/process group so child MPI ranks are not orphaned.
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
        raise
    finally:
        if log:
            log.close()
        if proc.stdout:
            proc.stdout.close()
    output = "".join(lines)
    if check and rc != 0:
        raise RuntimeError(f"Command failed with exit code {rc}: {cmd}\n{''.join(list(lines)[-100:])}")
    return output, rc


def source_fingerprint(source_dir: str | Path) -> str:
    root = Path(source_dir)
    candidates = []
    for rel_root in ("src", "scripts"):
        folder = root / rel_root
        if folder.exists():
            candidates.extend(p for p in folder.rglob("*") if p.is_file())
    candidates.extend(p for p in (root / "Makefile", root / "requirements.txt") if p.is_file())
    digest = hashlib.sha256()
    for path in sorted(candidates, key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(rel).to_bytes(8, "little"))
        digest.update(rel)
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "little"))
        digest.update(payload)
    return digest.hexdigest()


def openmpi_probe_source() -> str:
    return r'''#include <mpi.h>
#include <algorithm>
#include <cstdio>
#include <string>
int main(int argc, char** argv) {
    int init_rc = MPI_Init(&argc, &argv);
    if (init_rc != MPI_SUCCESS) return 10;
    int rank = -1, size = -1, version_len = 0;
    char version[MPI_MAX_LIBRARY_VERSION_STRING];
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Get_library_version(version, &version_len);
    std::string lib(version, version_len);
    std::replace(lib.begin(), lib.end(), '\n', ' ');
    std::replace(lib.begin(), lib.end(), '\r', ' ');
    std::printf("MPI_PROBE rank=%d size=%d library=%s\n", rank, size, lib.c_str());
    std::fflush(stdout);
    MPI_Finalize();
    return 0;
}
'''


def mpi_launch_prefix(mpiexec: str | Path) -> list[str]:
    return [str(mpiexec), "--allow-run-as-root", "--oversubscribe", "--bind-to", "none"]


def run_openmpi_probe(
    mpiexec: str | Path,
    probe_binary: str | Path,
    env: dict,
    process_counts: Iterable[int],
    *,
    output_dir: str | Path,
    timeout: int = 90,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for count in sorted(set(int(x) for x in process_counts)):
        if count < 1:
            raise ValueError(f"Invalid MPI process count: {count}")
        cmd = mpi_launch_prefix(mpiexec) + ["-np", str(count), str(probe_binary)]
        proc = subprocess.run(
            cmd, env=env, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
        output = proc.stdout or ""
        (out / f"mpi_probe_np{count}.log").write_text(output, encoding="utf-8")
        rows = re.findall(
            r"^MPI_PROBE rank=(\d+) size=(\d+) library=(.*)$",
            output, flags=re.MULTILINE,
        )
        ranks = sorted(int(row[0]) for row in rows)
        sizes = sorted({int(row[1]) for row in rows})
        libraries = [row[2].strip() for row in rows]
        passed = (
            proc.returncode == 0
            and len(rows) == count
            and ranks == list(range(count))
            and sizes == [count]
            and len(libraries) == count
            and all("open mpi" in lib.lower() for lib in libraries)
        )
        results[str(count)] = {
            "command": cmd,
            "return_code": proc.returncode,
            "output": output,
            "ranks": ranks,
            "communicator_sizes": sizes,
            "libraries": libraries,
            "passed": passed,
        }
        if not passed:
            raise RuntimeError(
                f"Open MPI launch verification failed for -np {count}. "
                f"Expected ranks {list(range(count))}, each reporting size={count}; "
                f"observed ranks={ranks}, sizes={sizes}, return_code={proc.returncode}. "
                f"Full output: {output[-4000:]}"
            )
        print(f"Verified Open MPI -np {count}: ranks {ranks}, communicator size {count}.")
    return results


def install_openmpi_and_build(
    work_dir: str | Path,
    workspace: str | Path,
    process_counts: Iterable[int],
    *,
    install: bool = True,
    install_python_requirements: bool = True,
) -> dict:
    """Install/select Open MPI, run real communicator probes, then compile BFS."""
    work = Path(work_dir)
    workspace = Path(workspace)
    report_dir = workspace / "runs" / "mpi_environment"
    report_dir.mkdir(parents=True, exist_ok=True)

    mpicxx = Path("/usr/bin/mpicxx.openmpi")
    mpirun = Path("/usr/bin/mpirun.openmpi")
    required_commands = ("g++", "curl", "gzip", "ldd")
    missing_commands = [name for name in required_commands if shutil.which(name) is None]
    if install and (not mpicxx.exists() or not mpirun.exists() or missing_commands):
        run_stream([
            "bash", "-lc",
            "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq build-essential openmpi-bin libopenmpi-dev curl gzip",
        ], timeout=1800)
    if not mpicxx.is_file() or not mpirun.is_file():
        raise FileNotFoundError(
            "Explicit Debian/Ubuntu Open MPI wrappers were not found. Expected "
            f"{mpicxx} and {mpirun}. Refusing generic mpicxx/mpirun alternatives."
        )
    missing_after_install = [name for name in required_commands if shutil.which(name) is None]
    if missing_after_install:
        raise FileNotFoundError(
            "Required build/download commands are still missing after package setup: "
            + ", ".join(missing_after_install)
        )

    mpi_env, removed_env = clean_mpi_environment()
    compiler_version = subprocess.check_output(
        [str(mpicxx), "--showme:version"], env=mpi_env, text=True, stderr=subprocess.STDOUT
    ).strip()
    compiler_command = subprocess.check_output(
        [str(mpicxx), "--showme:command"], env=mpi_env, text=True, stderr=subprocess.STDOUT
    ).strip()
    compiler_link = subprocess.check_output(
        [str(mpicxx), "--showme:link"], env=mpi_env, text=True, stderr=subprocess.STDOUT
    ).strip()
    launcher_version = subprocess.check_output(
        [str(mpirun), "--version"], env=mpi_env, text=True, stderr=subprocess.STDOUT
    ).strip()
    compiler_banner = compiler_version.lower()
    launcher_banner = launcher_version.lower()
    # Debian/Ubuntu Open MPI's compiler wrapper identifies itself as "Open MPI",
    # while mpirun commonly identifies its runtime layer as "OpenRTE". The
    # launcher banner is therefore not expected to contain the literal words
    # "Open MPI". The executable/library identity is verified independently by
    # run_openmpi_probe(), which requires every process to report an Open MPI
    # library build and the requested MPI_COMM_WORLD size.
    compiler_is_openmpi = "open mpi" in compiler_banner
    launcher_is_openmpi = ("openrte" in launcher_banner) or ("open mpi" in launcher_banner)
    if not compiler_is_openmpi or not launcher_is_openmpi:
        raise RuntimeError(
            "The selected compiler and launcher are not both from the Open MPI toolchain. "
            f"Compiler={compiler_version!r}; launcher={launcher_version.splitlines()[0]!r}"
        )

    probe_cpp = Path("/content/mpi_two_rank_probe.cpp")
    probe_bin = Path("/content/mpi_two_rank_probe")
    probe_cpp.write_text(openmpi_probe_source(), encoding="utf-8")
    compile_probe_output, compile_probe_rc = run_stream(
        [str(mpicxx), "-O2", str(probe_cpp), "-o", str(probe_bin)],
        env=mpi_env, check=False, timeout=900,
    )
    if compile_probe_rc != 0 or not probe_bin.is_file():
        raise RuntimeError("Failed to compile the standalone Open MPI probe. " + compile_probe_output[-3000:])

    probe_results = run_openmpi_probe(
        mpirun, probe_bin, mpi_env, process_counts, output_dir=report_dir / "probes"
    )

    pip_output = ""
    if install_python_requirements and (work / "requirements.txt").exists():
        pip_output, _ = run_stream([
            os.environ.get("PYTHON", "python3"), "-m", "pip", "install", "-q",
            "-r", str(work / "requirements.txt"),
        ], env=mpi_env, timeout=900)

    build_env = mpi_env.copy()
    build_env["MPICXX"] = str(mpicxx)
    build_output, build_rc = run_stream(
        ["bash", str(work / "scripts" / "build.sh")], cwd=work, env=build_env, check=False, timeout=900
    )
    exe = work / "build" / "distributed_bfs"
    if build_rc != 0 or not exe.is_file():
        raise RuntimeError("Distributed BFS build failed. " + build_output[-6000:])

    ldd_output = subprocess.check_output(
        ["ldd", str(exe)], env=mpi_env, text=True, stderr=subprocess.STDOUT
    )
    lower_ldd = ldd_output.lower()
    if "libmpi.so" not in lower_ldd or "libmpich" in lower_ldd:
        raise RuntimeError(
            "The BFS executable is not demonstrably linked against Open MPI. "
            "Refusing to execute it. ldd output:\n" + ldd_output
        )

    report = {
        "mpi_implementation": "Open MPI",
        "compiler": str(mpicxx),
        "compiler_version": compiler_version,
        "compiler_command": compiler_command,
        "compiler_link_flags": compiler_link,
        "launcher": str(mpirun),
        "launcher_version": launcher_version,
        "inherited_mpi_environment_variables_removed": removed_env,
        "probe_compile_return_code": compile_probe_rc,
        "probe_compile_output": compile_probe_output,
        "probes": probe_results,
        "bfs_build_return_code": build_rc,
        "bfs_build_output": build_output,
        "bfs_executable_ldd": ldd_output,
        "python_requirements_install_output": pip_output,
        "source_fingerprint": source_fingerprint(work),
        "cpu_count": os.cpu_count(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (report_dir / "openmpi_toolchain.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\nOpen MPI toolchain, process-count probes, and BFS build all passed.")
    print("Compiler:", mpicxx)
    print("Launcher:", mpirun)
    print("Available logical CPUs:", os.cpu_count())
    return {
        "mpicxx": str(mpicxx),
        "mpirun": str(mpirun),
        "env": mpi_env,
        "report": report,
        "source_fingerprint": report["source_fingerprint"],
    }


def _require_valid_success_archive(workspace: str | Path, archive_name: str, result_dir_name: str) -> Path:
    """Require the persisted result ZIP and verify its success manifest is inside it."""
    archive_path = Path(workspace) / "downloads" / archive_name
    if not archive_path.is_file() or archive_path.stat().st_size == 0:
        raise RuntimeError(
            f"The successful results archive is missing: {archive_path}. "
            "Rerun the preceding notebook; an interrupted run is not accepted."
        )
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            bad = archive.testzip()
            manifest_name = f"{result_dir_name}/SUCCESS.json"
            if bad or manifest_name not in archive.namelist():
                raise RuntimeError(f"Archive integrity/manifest check failed: bad={bad}, manifest={manifest_name}")
            manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
            if manifest.get("success") is not True:
                raise RuntimeError("The archived SUCCESS.json does not mark success=true.")
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"The persisted result ZIP is corrupt: {archive_path}") from exc
    return archive_path


def require_correctness_passed(workspace: str | Path, source_dir: str | Path) -> dict:
    result_dir = Path(workspace) / "runs" / "mpi_correctness"
    result_path = result_dir / "validation_results.json"
    success_path = result_dir / "SUCCESS.json"
    if not result_path.is_file() or not success_path.is_file():
        raise RuntimeError("Notebook 01 has not completed successfully. Run the new Notebook 01 first.")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    success = json.loads(success_path.read_text(encoding="utf-8"))
    if not result.get("all_passed") or not result.get("two_rank_mpi_probe_passed"):
        raise RuntimeError("Notebook 01 validation record does not confirm two-rank MPI correctness.")
    if success.get("success") is not True or success.get("notebook") != "01":
        raise RuntimeError("Notebook 01 success manifest is invalid.")
    expected = {"original_blocking", "original_nonblocking", "random_blocking", "random_nonblocking"}
    checks = result.get("checks", [])
    got = {item.get("configuration") for item in checks if item.get("validation_pass") is True}
    if got != expected or len(checks) != 4:
        raise RuntimeError(f"Notebook 01 did not verify all four expected configurations: {got}")
    for item in checks:
        if sorted(item.get("rank_metric_ids", [])) != [0, 1]:
            raise RuntimeError(f"Notebook 01 rank metrics are not two-rank for {item.get('configuration')}")
        if item.get("summary_rank_counts") != [2]:
            raise RuntimeError(f"Notebook 01 summary rank count is not 2 for {item.get('configuration')}")
    expected_hash = source_fingerprint(source_dir)
    if result.get("source_fingerprint") != expected_hash or success.get("source_fingerprint") != expected_hash:
        raise RuntimeError("Source code changed after Notebook 01. Rerun Notebook 01 before benchmarking.")
    _require_valid_success_archive(workspace, "01_mpi_correctness_results.zip", "mpi_correctness")
    return result


def clear_previous_archive(workspace: str | Path, archive_name: str) -> None:
    workspace = Path(workspace)
    drive_zip = workspace / "downloads" / archive_name
    if drive_zip.parent.exists():
        drive_zip.unlink(missing_ok=True)
    local_zip = Path("/content") / archive_name
    if local_zip.parent.exists():
        local_zip.unlink(missing_ok=True)


def write_success_manifest(result_dir: str | Path, notebook: str, metadata: dict | None = None) -> Path:
    result_dir = Path(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    # A previous attempt may have failed and left FAILURE.json behind. Once all
    # current-run validation succeeds, remove that stale marker so the success
    # archive cannot contain contradictory status files.
    (result_dir / "FAILURE.json").unlink(missing_ok=True)
    payload = {
        "success": True,
        "notebook": str(notebook),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        payload.update(metadata)
    path = result_dir / "SUCCESS.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def create_success_zip(result_dir: str | Path, workspace: str | Path, archive_name: str) -> Path:
    """Create/download an archive only after SUCCESS.json explicitly marks success."""
    result_dir = Path(result_dir)
    workspace = Path(workspace)
    sentinel = result_dir / "SUCCESS.json"
    if not sentinel.is_file():
        raise RuntimeError("Refusing to create results ZIP: SUCCESS.json is missing.")
    status = json.loads(sentinel.read_text(encoding="utf-8"))
    if status.get("success") is not True:
        raise RuntimeError("Refusing to create results ZIP: run is not marked successful.")

    downloads = workspace / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    local_zip = Path("/content") / archive_name
    drive_zip = downloads / archive_name
    local_zip.unlink(missing_ok=True)
    drive_zip.unlink(missing_ok=True)

    file_count = 0
    temp_zip = local_zip.with_suffix(local_zip.suffix + ".partial")
    temp_zip.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(result_dir.rglob("*")):
                if path.is_file() and path.name != archive_name:
                    archive.write(path, (result_dir.name / path.relative_to(result_dir)).as_posix())
                    file_count += 1
        if file_count == 0:
            raise RuntimeError("Refusing to download an empty results ZIP.")
        with zipfile.ZipFile(temp_zip, "r") as check:
            bad = check.testzip()
            names = set(check.namelist())
            expected_sentinel = f"{result_dir.name}/SUCCESS.json"
            if bad or expected_sentinel not in names:
                raise RuntimeError(
                    f"Results ZIP integrity check failed: bad={bad}, "
                    f"success_manifest_present={expected_sentinel in names}"
                )
        temp_zip.replace(local_zip)
        shutil.copy2(local_zip, drive_zip)
        print("\nSUCCESS: all notebook checks passed; results ZIP created.")
        print("Files packaged:", file_count)
        print("Drive copy:", drive_zip)
        print("Starting browser download...")
        from google.colab import files
        files.download(str(local_zip))
    except BaseException:
        local_zip.unlink(missing_ok=True)
        drive_zip.unlink(missing_ok=True)
        temp_zip.unlink(missing_ok=True)
        raise
    return drive_zip


def read_csv(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(f"Required CSV is missing or empty: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_single_config(config_dir: str | Path, expected_ranks: int, expected_repetitions: int,
                           expected_dataset: str | None = None,
                           expected_ordering: str | None = None,
                           expected_mode: str | None = None) -> dict:
    cfg = Path(config_dir)
    summary = read_csv(cfg / "summary.csv")
    levels = read_csv(cfg / "per_level.csv")
    rank_rows = read_csv(cfg / "rank_metrics.csv")
    expected_sources = list(range(expected_repetitions))
    if len(summary) != expected_repetitions:
        raise RuntimeError(f"{cfg.name}: expected {expected_repetitions} summary rows, found {len(summary)}")
    if any(str(row.get("validation", "")).upper() != "PASS" for row in summary):
        raise RuntimeError(f"{cfg.name}: one or more BFS summary rows are not validation=PASS")
    summary_ranks = sorted({int(row["ranks"]) for row in summary})
    if summary_ranks != [expected_ranks]:
        raise RuntimeError(f"{cfg.name}: requested {expected_ranks} ranks, summary reports {summary_ranks}")
    source_ids = sorted(int(row["source_index"]) for row in summary)
    if source_ids != expected_sources:
        raise RuntimeError(f"{cfg.name}: expected source indices {expected_sources}, found {source_ids}")
    rank_ids = sorted(int(row["rank"]) for row in rank_rows)
    rank_counts = sorted({int(row["ranks"]) for row in rank_rows})
    if rank_ids != list(range(expected_ranks)) or rank_counts != [expected_ranks] or len(rank_rows) != expected_ranks:
        raise RuntimeError(f"{cfg.name}: rank metrics mismatch; ids={rank_ids}, ranks={rank_counts}, rows={len(rank_rows)}")
    if not levels or sorted({int(row["ranks"]) for row in levels}) != [expected_ranks]:
        raise RuntimeError(f"{cfg.name}: per-level metrics are missing or report an incorrect rank count")
    level_sources = sorted({int(row["source_index"]) for row in levels})
    if level_sources != expected_sources:
        raise RuntimeError(f"{cfg.name}: per-level metrics do not cover all sources; expected {expected_sources}, got {level_sources}")
    for row in summary:
        if expected_dataset is not None and row["dataset"] != expected_dataset:
            raise RuntimeError(f"{cfg.name}: unexpected dataset {row['dataset']}")
        if expected_ordering is not None and row["ordering"] != expected_ordering:
            raise RuntimeError(f"{cfg.name}: unexpected ordering {row['ordering']}")
        if expected_mode is not None and row["mode"] != expected_mode:
            raise RuntimeError(f"{cfg.name}: unexpected mode {row['mode']}")
    for row in levels:
        if expected_dataset is not None and row["dataset"] != expected_dataset:
            raise RuntimeError(f"{cfg.name}: per-level dataset mismatch: {row['dataset']}")
        if expected_ordering is not None and row["ordering"] != expected_ordering:
            raise RuntimeError(f"{cfg.name}: per-level ordering mismatch: {row['ordering']}")
        if expected_mode is not None and row["mode"] != expected_mode:
            raise RuntimeError(f"{cfg.name}: per-level mode mismatch: {row['mode']}")
    for row in rank_rows:
        if expected_dataset is not None and row["dataset"] != expected_dataset:
            raise RuntimeError(f"{cfg.name}: rank-metric dataset mismatch: {row['dataset']}")
        if expected_ordering is not None and row["ordering"] != expected_ordering:
            raise RuntimeError(f"{cfg.name}: rank-metric ordering mismatch: {row['ordering']}")
    log_path = cfg / "run.log"
    if not log_path.is_file() or log_path.stat().st_size == 0:
        raise RuntimeError(f"{cfg.name}: missing or empty run.log")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"Completed dataset=.*?ranks=(\d+).*?validation=PASS", log)
    if len(matches) != 1 or any(int(x) != expected_ranks for x in matches):
        raise RuntimeError(f"{cfg.name}: log does not prove exactly one completed run at rank count {expected_ranks}: {matches}")
    if expected_dataset is not None and f"Completed dataset={expected_dataset} " not in log:
        raise RuntimeError(f"{cfg.name}: completion line does not identify dataset={expected_dataset}")
    if expected_mode is not None and f"mode={expected_mode}" not in log:
        raise RuntimeError(f"{cfg.name}: completion line does not identify mode={expected_mode}")
    if expected_ordering is not None and f"ordering={expected_ordering}" not in log:
        raise RuntimeError(f"{cfg.name}: completion line does not identify ordering={expected_ordering}")
    if f"repetitions={expected_repetitions}" not in log:
        raise RuntimeError(f"{cfg.name}: completion line does not identify repetitions={expected_repetitions}")
    return {"ranks": expected_ranks, "rank_ids": rank_ids, "summary_rows": len(summary), "level_rows": len(levels), "source_indices": source_ids}


def validate_complete_run(
    run_dir: str | Path,
    *,
    datasets: Iterable[str],
    ranks: Iterable[int],
    orderings: Iterable[str] = ("original", "random"),
    modes: Iterable[str] = ("blocking", "nonblocking"),
    repetitions: int,
) -> dict:
    run_dir = Path(run_dir)
    csv_dir = run_dir / "csv"
    summary = read_csv(csv_dir / "summary.csv")
    levels = read_csv(csv_dir / "per_level.csv")
    rank_rows = read_csv(csv_dir / "rank_metrics.csv")
    expected_datasets = {str(x) for x in datasets}
    expected_ranks = {int(x) for x in ranks}
    expected_orderings = {str(x) for x in orderings}
    expected_modes = {str(x) for x in modes}
    expected_configs = {
        (ds, p, ordering, mode)
        for ds in expected_datasets for p in expected_ranks
        for ordering in expected_orderings for mode in expected_modes
    }
    actual_configs = {
        (row["dataset"], int(row["ranks"]), row["ordering"], row["mode"])
        for row in summary
    }
    if actual_configs != expected_configs:
        missing = sorted(expected_configs - actual_configs)
        extra = sorted(actual_configs - expected_configs)
        raise RuntimeError(f"Run configuration coverage mismatch. Missing={missing[:10]}, extra={extra[:10]}")
    expected_rows = len(expected_configs) * int(repetitions)
    if len(summary) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} BFS summary rows, found {len(summary)}")
    if any(str(row.get("validation", "")).upper() != "PASS" for row in summary):
        raise RuntimeError("At least one benchmark row is not validation=PASS")

    config_root = run_dir / "configs"
    checkpoint_root = run_dir / "checkpoints"
    expected_tags = set()
    for ds, p, ordering, mode in expected_configs:
        tag = f"{ds}_p{p}_{ordering}_{mode}"
        expected_tags.add(tag)
        cfg_dir = config_root / tag
        validate_single_config(
            cfg_dir, p, int(repetitions), expected_dataset=ds,
            expected_ordering=ordering, expected_mode=mode,
        )
        if not (checkpoint_root / f"{tag}.done").is_file():
            raise RuntimeError(f"Validated checkpoint missing for {tag}")

    config_dirs = {p.name for p in config_root.iterdir() if p.is_dir()} if config_root.exists() else set()
    done_tags = {p.stem for p in checkpoint_root.glob("*.done")} if checkpoint_root.exists() else set()
    if config_dirs != expected_tags or done_tags != expected_tags:
        raise RuntimeError(
            f"Checkpoint/config directories do not match expected matrix. "
            f"Missing configs={sorted(expected_tags-config_dirs)[:8]}, extra configs={sorted(config_dirs-expected_tags)[:8]}, "
            f"missing checkpoints={sorted(expected_tags-done_tags)[:8]}, extra checkpoints={sorted(done_tags-expected_tags)[:8]}"
        )

    if not levels or any(int(row["ranks"]) not in expected_ranks for row in levels):
        raise RuntimeError("Per-level CSV is empty or contains an unexpected rank count.")
    if not rank_rows:
        raise RuntimeError("Rank metrics CSV is empty.")
    rank_config_keys = {(r["dataset"], int(r["ranks"]), r["ordering"]) for r in rank_rows}
    expected_rank_keys = {(ds, p, ordering) for ds in expected_datasets for p in expected_ranks for ordering in expected_orderings}
    if rank_config_keys != expected_rank_keys:
        raise RuntimeError("Rank metrics do not cover every dataset/rank/ordering combination.")
    for ds, p, ordering in expected_rank_keys:
        rr = [r for r in rank_rows if r["dataset"] == ds and int(r["ranks"]) == p and r["ordering"] == ordering]
        expected_rank_ids = sorted(list(range(p)) * len(expected_modes))
        if sorted(int(r["rank"]) for r in rr) != expected_rank_ids or len(rr) != p * len(expected_modes):
            raise RuntimeError(
                f"Rank metric rows do not exactly cover each rank for every mode for {(ds,p,ordering)}; "
                f"expected {expected_rank_ids}, got {sorted(int(r['rank']) for r in rr)}"
            )

    plots_dir = run_dir / "plots"
    required_plot_patterns = ("teps_*.png", "per_level_*.png", "collective_request_*.png", "cut_imbalance_*.png", "remote_pairs_by_rank_*.png")
    for ds in expected_datasets:
        for pattern in required_plot_patterns:
            candidates = [p for p in plots_dir.glob(pattern) if ds in p.stem]
            if not candidates or any(p.stat().st_size == 0 for p in candidates):
                raise RuntimeError(f"Required non-empty plot missing for {ds}: {pattern}")

    aggregated = plots_dir / "summary_aggregated.csv"
    report_md = run_dir / "report" / "Measured_Analysis_Report.md"
    report_docx = run_dir / "report" / "Two_Page_Report.docx"
    deck = run_dir / "presentation" / "Distributed_BFS_Results_Presentation.pptx"
    for required in (aggregated, report_md, report_docx, deck):
        if not required.is_file() or required.stat().st_size == 0:
            raise RuntimeError(f"Expected generated deliverable missing or empty: {required}")

    completion = {
        "complete": True,
        "datasets": sorted(expected_datasets),
        "ranks": sorted(expected_ranks),
        "orderings": sorted(expected_orderings),
        "modes": sorted(expected_modes),
        "configurations": len(expected_configs),
        "bfs_summary_rows": len(summary),
        "repetitions_per_configuration": int(repetitions),
        "all_validations_pass": True,
        "runner_version": RUNNER_VERSION,
        "source_fingerprint": source_fingerprint(run_dir.parent.parent / "Distributed_BFS_MPI") if (run_dir.parent.parent / "Distributed_BFS_MPI").exists() else None,
    }
    (run_dir / "RUN_COMPLETE.json").write_text(json.dumps(completion, indent=2), encoding="utf-8")
    return completion


def ensure_run_config(run_dir: str | Path, config: dict, source_dir: str | Path) -> dict:
    """Freeze experiment settings and source hash before a resumable run starts."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(config)
    payload["runner_version"] = RUNNER_VERSION
    payload["source_fingerprint"] = source_fingerprint(source_dir)
    path = run_dir / "run_config.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError(
                f"Experiment settings or source changed for {run_dir}. "
                "Use a new RUN_NAME rather than mixing runs."
            )
    else:
        existing_artifacts = any((run_dir / name).exists() for name in ("configs", "checkpoints", "csv", "logs"))
        if existing_artifacts:
            raise RuntimeError(
                f"{run_dir} contains prior outputs but no run_config.json. "
                "Move the old results aside and start with a new RUN_NAME; refusing to mix legacy data."
            )
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def require_matrix_complete(run_dir: str | Path, source_dir: str | Path) -> dict:
    """Validate a completed benchmark matrix without requiring report artifacts."""
    run_dir = Path(run_dir)
    complete_path = run_dir / "RUN_COMPLETE.json"
    manifest_path = run_dir / "run_config.json"
    if not complete_path.is_file() or not manifest_path.is_file():
        raise RuntimeError(f"No completed matrix manifest was found in {run_dir}.")
    info = json.loads(complete_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if info.get("complete") is not True or info.get("all_validations_pass") is not True:
        raise RuntimeError("The benchmark matrix is not marked complete with all validations passing.")
    if info.get("runner_version") != RUNNER_VERSION or manifest.get("runner_version") != RUNNER_VERSION:
        raise RuntimeError("Benchmark was generated by an incompatible notebook runner version.")
    expected_hash = source_fingerprint(source_dir)
    if manifest.get("source_fingerprint") != expected_hash or info.get("source_fingerprint") != expected_hash:
        raise RuntimeError("Source fingerprint differs from the source used to collect the benchmark results.")

    datasets = set(info.get("datasets", []))
    ranks = {int(x) for x in info.get("ranks", [])}
    repetitions = int(info.get("repetitions_per_configuration", 0))
    orderings = {"original", "random"}
    modes = {"blocking", "nonblocking"}
    if not datasets or not ranks or repetitions < 1:
        raise RuntimeError("RUN_COMPLETE.json contains incomplete matrix metadata.")
    summary = read_csv(run_dir / "csv" / "summary.csv")
    expected_configs = {(ds, p, o, m) for ds in datasets for p in ranks for o in orderings for m in modes}
    actual_configs = {(r["dataset"], int(r["ranks"]), r["ordering"], r["mode"]) for r in summary}
    expected_rows = len(expected_configs) * repetitions
    if actual_configs != expected_configs or len(summary) != expected_rows:
        raise RuntimeError("Merged summary CSV does not contain the complete expected benchmark matrix.")
    if int(info.get("configurations", -1)) != len(expected_configs) or int(info.get("bfs_summary_rows", -1)) != expected_rows:
        raise RuntimeError("RUN_COMPLETE.json configuration/source totals do not match the expected matrix.")
    if any(str(r.get("validation", "")).upper() != "PASS" for r in summary):
        raise RuntimeError("Benchmark summary contains a failed BFS validation.")
    for ds, p, ordering, mode in expected_configs:
        tag = f"{ds}_p{p}_{ordering}_{mode}"
        validate_single_config(
            run_dir / "configs" / tag, p, repetitions,
            expected_dataset=ds, expected_ordering=ordering, expected_mode=mode,
        )
        if not (run_dir / "checkpoints" / f"{tag}.done").is_file():
            raise RuntimeError(f"Validated checkpoint missing: {tag}")
    return info


def require_complete_run(run_dir: str | Path, source_dir: str | Path | None = None) -> dict:
    run_dir = Path(run_dir)
    if source_dir is None:
        source_dir = run_dir.parent.parent / "Distributed_BFS_MPI"
    info = require_matrix_complete(run_dir, source_dir)
    if run_dir.name == "pilot":
        success_path = run_dir / "SUCCESS.json"
        if not success_path.is_file():
            raise RuntimeError("The pilot notebook has not reached its successful completion point.")
        success = json.loads(success_path.read_text(encoding="utf-8"))
        if success.get("success") is not True or success.get("notebook") != "02":
            raise RuntimeError("The pilot SUCCESS.json is invalid.")
        _require_valid_success_archive(run_dir.parent.parent, "02_pilot_benchmark_results.zip", "pilot")
    return validate_complete_run(
        run_dir,
        datasets=info["datasets"],
        ranks=info["ranks"],
        orderings=info.get("orderings", ["original", "random"]),
        modes=info.get("modes", ["blocking", "nonblocking"]),
        repetitions=int(info["repetitions_per_configuration"]),
    )


def available_memory_gb() -> float:
    """Estimate available memory using host free memory and cgroup limit/current usage."""
    try:
        import psutil
        available = psutil.virtual_memory().available
    except ImportError:
        available = 0
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                available = int(line.split()[1]) * 1024
                break
        if not available:
            raise RuntimeError("Cannot determine available memory; install psutil or inspect /proc/meminfo.")
    candidates = [available]
    # cgroup v2
    memory_max = Path("/sys/fs/cgroup/memory.max")
    memory_current = Path("/sys/fs/cgroup/memory.current")
    try:
        if memory_max.exists() and memory_current.exists():
            max_text = memory_max.read_text().strip()
            if max_text != "max":
                limit = int(max_text)
                current = int(memory_current.read_text().strip())
                candidates.append(max(0, limit - current))
    except (OSError, ValueError):
        pass
    # cgroup v1
    v1_limit = Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    v1_usage = Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
    try:
        if v1_limit.exists() and v1_usage.exists():
            limit = int(v1_limit.read_text().strip())
            usage = int(v1_usage.read_text().strip())
            if limit < (1 << 60):
                candidates.append(max(0, limit - usage))
    except (OSError, ValueError):
        pass
    return min(candidates) / (1024 ** 3)
