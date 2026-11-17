# Start Here — Distributed BFS with MPI

This project contains a C++17 distributed Breadth-First Search implementation using MPI-3, together with Google Colab notebooks for correctness testing, benchmarking, and report generation.

## One-Time Setup

1. Extract the project folder.
2. Upload the complete project folder to the top level of Google Drive.
3. Open `01_Setup_and_Correctness.ipynb` from Google Drive using Google Colab.
4. Select Python 3, CPU runtime, and no accelerator.
5. Execute the notebook cells and review the correctness results.

Run the notebooks one at a time and preserve the generated result ZIP files and Drive checkpoints.

## Notebook Execution Order

| Notebook | Purpose |
|---|---|
| `01_Setup_and_Correctness.ipynb` | Install and verify Open MPI, compile BFS, check MPI communicator sizes, and run correctness configurations. |
| `02_Pilot_Benchmark.ipynb` | Execute the RMAT scale 16 pilot benchmark with ranks 1, 2, and 4. |
| `03_Full_Experiment_Matrix.ipynb` | Execute the SNAP and RMAT benchmark matrix with ranks 1, 2, 4, 8, and 16. |
| `04_Rebuild_Reports.ipynb` | Rebuild plots, reports, and presentation from the saved validated partial-matrix results. |
| `04_Rebuild_Reports_Full_Matrix_Legacy.ipynb` | Older report-generation workflow retained for reference. |

The recommended report-generation notebook is `04_Rebuild_Reports.ipynb`.

## Existing Experiment Results

The full benchmark matrix was designed with:

- 12 graph datasets: 3 SNAP datasets and 9 RMAT scales.
- 5 MPI process counts: 1, 2, 4, 8, and 16.
- 2 vertex orderings: original and randomized.
- 2 communication modes: blocking and nonblocking.

Total planned configurations: 240.

Total planned BFS traversals: 3,840.

The saved experiment contains 234 completed and validated configurations, corresponding to 3,744 BFS traversals.

Six configurations were not completed:

- RMAT scale 24, 8 ranks, random ordering, blocking communication.
- RMAT scale 24, 8 ranks, random ordering, nonblocking communication.
- RMAT scale 24, 16 ranks, original ordering, blocking communication.
- RMAT scale 24, 16 ranks, original ordering, nonblocking communication.
- RMAT scale 24, 16 ranks, random ordering, blocking communication.
- RMAT scale 24, 16 ranks, random ordering, nonblocking communication.

The full experiment run was interrupted when an MPI process was terminated during execution in the Colab environment.

The existing validated checkpoints and results have been preserved. The report-generation notebook rebuilds outputs from these 234 configurations. Do not describe the saved experiment as a completed 240-configuration matrix.

## Success-Only ZIP Behavior

The notebooks use success-only packaging.

A notebook creates its corresponding ZIP only after its required commands, data checks, validation steps, and output checks succeed.

The generated ZIP is written to `/content/`, copied to the corresponding Google Drive `downloads/` folder, integrity-checked, and then passed to Colab's browser download function.

If a notebook encounters an error or fails validation, it does not generate a successful result ZIP. Validated configuration checkpoints and logs remain in Drive to support resumption when the runtime is interrupted.

A hard runtime termination may prevent notebook cleanup from running. Preserve the existing Drive checkpoints and use unchanged experiment settings when resuming.

## Where Data Lives

The Google Drive project folder contains:

- The five notebook files.
- `colab_helpers.py`.
- `Distributed_BFS_MPI/` — canonical source project.
- `data/snap/` — downloaded SNAP graph cache.
- `downloads/` — generated result ZIP files.
- `exports/` — generated reports and plots.
- `runs/` — environment checks, correctness results, pilot results, and full-matrix results.

The source is copied to `/content/` for compilation and execution. The Colab `/content/` directory is temporary, so persistent source, datasets, logs, checkpoints, and results should remain in Google Drive.

## MPI Environment

The notebooks explicitly install and select the Debian/Ubuntu Open MPI packages:

- `openmpi-bin`
- `libopenmpi-dev`

They use the versioned wrapper paths:

- `/usr/bin/mpicxx.openmpi`
- `/usr/bin/mpirun.openmpi`

The workflow verifies actual MPI communicator sizes before executing the BFS benchmark matrix. It also checks the compiled executable's MPI linkage.

The notebooks do not allow a serial MPI fallback for submitted distributed results.

Open MPI's local process launch supports multiple ranks on one Colab VM. Oversubscription is enabled for the single-VM environment. This should not be interpreted as multi-node execution.

See `MPI_COLAB_IMPLEMENTATION_NOTES.md` for additional implementation details.

## Scope and Limitations

- CPU runtime only; no GPU acceleration is used.
- All MPI ranks execute on one Colab VM.
- The experiments demonstrate multi-process MPI execution, not multi-node cluster scaling.
- The Colab runtime used two logical CPUs; configurations above two ranks involve CPU oversubscription.
- Colab runtime lifetime and available resources are dynamic.
- The saved full experiment matrix contains 234 of 240 validated configurations.
- RMAT scale 24 configurations at 8 and 16 ranks were not fully completed.
- The serial compatibility shim is intended only for local smoke tests and must not be used to report distributed MPI timings.

Performance results should be interpreted with these limitations in mind.

